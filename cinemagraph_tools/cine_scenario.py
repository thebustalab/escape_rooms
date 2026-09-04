#!/usr/bin/env python3
"""cine_scenario.py — run the cinemagraph stage over EVERY (room, world-state) of a scenario.

`cine_stage.py` does one state: render, gate, measure, repair, re-measure. This walks the scenario and
drives it over all of them, then puts the surviving clip where the player can find it.

THREE THINGS IT REFUSES TO GUESS
  1. **Which images exist.** States come from `scene_states.scene_states()`, never from `room.panorama`.
     A room is not one picture: a full-scene night variant hangs off a carrier hotspot, and code that
     walks the room node animates the base and silently ships a half-dead second act. That is not
     hypothetical — it shipped a daytime panorama as the "night deck" on 2026-08-29.
  2. **What should move.** The motion spec is authored (`authoring.motionSpec`), not inferred. A state
     with no spec is SKIPPED and reported, because the alternative is a generic prompt that animates
     whatever the model feels like and measures nothing.
  3. **Box-scope states.** Only `scope == "full-scene"` states get their own render. A boxed variant is
     composited over its room's full-scene clip at runtime, so rendering one separately would be paying
     for a frame nobody displays.

WHERE THE WORK LANDS. Renders, tiles and intermediate composites go to a scratch tree outside the repo
(they are large and most are throwaway); only the FINAL clip is copied into the room directory, under a
stable name (`cine_<state>.mp4`). Nothing is written into scenario.json here — wiring the clip onto a
carrier hotspot is a separate, reviewable step.

  cine_scenario.py --chapter hierarchical_clustering --scenario canyon [--rooms j_c1,works]
                   [--dry-run] [--no-repair] [--reuse]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "authoring_v2"))

import cine_stage as CS      # noqa: E402
import scene_states as SS    # noqa: E402

ROOMS = os.path.join(HERE, "..", "rooms")
WORK_ROOT = "/home/bustalab/Documents/Tools/temp/cine"


def states_to_run(doc, base, rooms=None):
    """The full-scene states worth rendering, each paired with its authored motion spec."""
    by_key = {r.get("key"): r for r in doc.get("rooms") or []}
    out = []
    for st in SS.scene_states(doc, base):
        if rooms and st["room"] not in rooms:
            continue
        if st["scope"] != "full-scene":
            out.append((st, None, "boxed variant — composited over the room's clip at runtime"))
            continue
        if not st["exists"]:
            out.append((st, None, "no art on disk for this state"))
            continue
        spec = ((by_key.get(st["room"]) or {}).get("authoring") or {}).get("motionSpec")
        if st["state"] != "base":
            # A variant's motion spec, if authored, lives beside the base one keyed by state name.
            spec = (spec or {}).get("states", {}).get(st["state"]) if isinstance(spec, dict) else None
        if not spec:
            out.append((st, None, "no authored motionSpec — nothing to name and nothing to measure"))
            continue
        spec = dict(spec)
        spec["room"], spec["state"] = st["room"], st["state"]
        out.append((st, spec, None))
    return out


BAKE_FADE = 0.5      # Lucas's loop treatment, settled in the sweep work and unchanged since.


def mask_png(base, room, state, clip, pct="auto", region=0.0, still_boxes=None):
    """Build the room's cinemagraph mask and return (path, meta). Greyscale: white = show the VIDEO.

    `auto` is the confirmed default — a percentile ladder over the clip's own motion scored by object
    SOLIDITY, then closed, hole-filled and feathered (`auto_mask`). A number instead picks a rung on that
    same ladder by hand, which is what the gallery's threshold slider sets.

    `still_boxes` — image-fraction boxes forced BLACK after the mask is built, so those regions play the
    still no matter how hard they moved. This is the bake-time half of `motion_spec`'s `still: True`
    flag, which until now was measured (`still_violations`) and reported but never ENFORCED.

    WHY IT HAD TO EXIST (egypt/library, 2026-09-02). BOTH mask axes select FOR motion, so neither can
    remove an unwanted mover — they can only remove wanted ones:
      * threshold keeps the pixels that move HARDEST. In the Library the wrongly-animated lectern codex
        measured p95 32.9 and the dust the room exists to show measured 4.3, so every rung that drops
        the book drops the dust seven times over.
      * the region cut keeps LARGE COHERENT regions. The book and the scroll-racks are exactly that;
        drifting dust is fine speckle, so the cut deletes the dust and keeps the book.
    Turning either slider up made the clip worse in the same motion. A region you want held still has to
    be named, because nothing about its motion distinguishes it from the motion you want."""
    import numpy as np
    from PIL import Image
    sys.path.insert(0, HERE)
    from auto_mask import auto_mask, mask_at_percentile  # noqa: WPS433
    from motion_mask import sample_frames  # noqa: WPS433
    tstd = sample_frames(clip, n=16).std(axis=0).mean(axis=2)
    # `region` is the REGION CUT in parts-per-million of the frame (`auto_mask.drop_small`): the second,
    # independent axis the gallery exposes. The percentile says how hard a pixel must move; this says how
    # much company it must keep, so isolated speckle is dropped while a big gentle mover survives.
    # Converted to pixels HERE, against this clip's own frame, so one slider position means the same
    # thing on a full panorama and on a crop.
    min_px = int(float(region or 0) * tstd.size / 1e6)
    if pct in (None, "auto"):
        m, thr, rep = auto_mask(tstd, min_px=min_px)
        meta = {"pct": "auto", "threshold": round(float(thr), 3), "coverage": round(float(m.mean()), 4)}
    else:
        m, thr, cov, _reg = mask_at_percentile(tstd, float(pct), min_px=min_px)
        meta = {"pct": float(pct), "threshold": round(float(thr), 3), "coverage": round(float(cov), 4)}
    meta["region"] = float(region or 0)
    meta["minPx"] = min_px
    # STILL BOXES, applied LAST — after the threshold, the region cut and the feather, so nothing
    # downstream can bleed motion back into a region that was declared still. Recorded in the sidecar
    # meta so the gallery can say why a region is frozen rather than leaving it a mystery.
    H, W = m.shape[:2]
    pinned = []
    for b in (still_boxes or []):
        try:
            x0, y0, x1, y1 = [float(v) for v in b["box"]]
        except Exception:  # noqa: BLE001 — a malformed box must not lose the whole mask
            continue
        c0, r0 = int(round(x0 * W)), int(round(y0 * H))
        c1, r1 = int(round(x1 * W)), int(round(y1 * H))
        if c1 <= c0 or r1 <= r0:
            continue
        m[r0:r1, c0:c1] = 0.0
        pinned.append(b.get("name") or "unnamed")
    if pinned:
        meta["stillBoxes"] = pinned
        meta["coverage"] = round(float(np.clip(m, 0, 1).mean()), 4)   # post-pin truth, not pre-pin
    d = os.path.join(base, "_scratch", "motion")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, "bakemask_%s_%s.png" % (room, state))
    Image.fromarray((np.clip(m, 0, 1) * 255).astype("uint8"), "L").save(out)
    return out, meta


def bake_loop(raw, out, fade=BAKE_FADE, log=print, still=None, mask=None):
    """Dissolve the tail into the head so an ordinary `loop` plays seamlessly.

    THIS IS NOT OPTIONAL AND IT IS NOT A PLAYBACK SETTING. The recipe's end-guide gets the last frame
    CLOSE to the first — that is what drives loop jump down to ~2 — but close is not equal, and the
    residual pop is what the 0.5 s crossfade hides. Shipping the raw render skips it entirely: the
    clips visibly hitched at the wrap and Lucas caught all nine at once (2026-08-31). The raw file is
    kept beside the bake (`*_raw.mp4`, gitignored) so the loop treatment can be changed later without
    paying for the render again.

    `--seam` repairs the equirectangular wrap on every frame. These are 360 panoramas and the render
    does not preserve the join, so a still repaired to a seam of 0.00 still yields a clip that visibly
    splits — measured at 8.33 on `j_c4` and 3.66 on `works`, which Lucas spotted in the floodworks.
    """
    os.makedirs("/tmp/sweep", exist_ok=True)     # bake_flat stages frames here
    cmd = [sys.executable, os.path.join(HERE, "bake_flat.py"), raw,
           "--out", out, "--fade", str(fade), "--seam"]
    if still and mask:
        # THE MASK COMPOSITE. Show the generated video only where it moves and the ORIGINAL still
        # everywhere else — the classic cinemagraph construction. Static regions then keep the
        # panorama's full detail: they cannot soften, drift or invent content, because those pixels
        # are never generated at all. Baked in at Lucas's instruction (2026-08-31); the tooling for it
        # had existed unused since the sweep work.
        cmd += ["--still", still, "--mask", mask]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("bake failed: " + (r.stderr or r.stdout).strip()[-300:])
    log("  bake: " + (r.stdout or "").strip())
    return out


def state_still(base, room, state):
    """The panorama a given (room, state) is actually drawn from, as an absolute path, or None.

    One resolver for the still, shared by the bake and the gallery, so the image the composite is laid
    over and the image the reviewer sees underneath the clip cannot be different files."""
    if state == "base":
        p = os.path.join(base, room, "scene.png")
        return p if os.path.isfile(p) else None
    try:
        doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
        for st in SS.scene_states(doc, base):
            if st["room"] == room and st["state"] == state and st.get("panorama"):
                p = os.path.join(base, st["panorama"])
                return p if os.path.isfile(p) else None
    except Exception:  # noqa: BLE001
        return None
    return None


def _still_boxes(base, room, state):
    """The authored `still: True` subjects for this (room, state), as {name, box}.

    Resolved from `scenario.json` HERE rather than passed in, so that every path to a bake honours the
    pins — including the gallery's "commit mask + re-bake" and the per-patch rebuild, neither of which
    has a spec in hand. A pin that survived a render but was dropped by a re-bake would be worse than no
    pin at all, because it would come back only sometimes."""
    try:
        doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a clips-only fixture has no scenario; nothing is pinned
        return []
    node = next((r for r in doc.get("rooms") or [] if r.get("key") == room), None)
    spec = ((node or {}).get("authoring") or {}).get("motionSpec")
    if isinstance(spec, dict) and state != "base":
        spec = (spec.get("states") or {}).get(state)
    subs = (spec or {}).get("subjects") or []
    return [{"name": s.get("name"), "box": s["box"]}
            for s in subs if s.get("still") and isinstance(s.get("box"), (list, tuple))]


def _mask_inputs(base, room, state, clip, log=print):
    """(still, mask) for the bake, honouring a per-clip `cine_<state>.mask.json` if one was authored.

    The sidecar records the percentile chosen in the gallery, so a re-bake reproduces the same mask
    instead of silently reverting to auto — the threshold is an authored decision, not a default."""
    room_dir = os.path.join(base, room)
    # THE STILL MUST BE THIS STATE'S ART, NOT THE ROOM'S BASE ART. `scene.png` was hardcoded here, so a
    # variant clip (`cine_night.mp4`, `cine_lantern.mp4`) was composited over the DAY panorama: every
    # pixel the mask held still showed the wrong world state, and only the moving region carried the
    # variant. Resolve it the way the rest of the pipeline does — via `scene_states`, never by guessing
    # from the room node, which is the same rule that stopped a daytime panorama shipping as the "night
    # deck" (2026-08-29).
    still = state_still(base, room, state) or os.path.join(room_dir, "scene.png")
    if not os.path.isfile(still):
        return None, None
    sj = os.path.join(room_dir, "cine_%s.mask.json" % state)
    pct, region = "auto", 0.0
    if os.path.isfile(sj):
        try:
            cfg = json.load(open(sj, encoding="utf-8"))
            if cfg.get("enabled") is False:
                log("  mask disabled for this clip — baking unmasked")
                return None, None
            pct = cfg.get("pct", "auto")
            region = float(cfg.get("region") or 0)
        except Exception:  # noqa: BLE001
            pass
    pins = _still_boxes(base, room, state)
    mk, meta = mask_png(base, room, state, clip, pct, region, still_boxes=pins)
    json.dump(dict(meta, enabled=True), open(sj, "w", encoding="utf-8"), indent=1)
    log("  mask: pct=%s region=%gppm(%dpx) thr=%.2f -> %.1f%% video, rest still"
        % (meta["pct"], meta["region"], meta["minPx"], meta["threshold"], 100 * meta["coverage"]))
    if meta.get("stillBoxes"):
        log("  pinned still: %s" % ", ".join(meta["stillBoxes"]))
    return still, mk


def rebuild_clip(base, room, state, log=print):
    """Rebuild a baked clip from its UNPATCHED render, re-applying only the patches marked enabled.

    This is what makes the gallery's per-patch toggle mean something. A repair tile is composited INTO
    the clip, so "ship without this patch" cannot be a display flag — the file itself has to be rebuilt.
    Three inputs, all on disk beside the scenario so this works after any scratch cleanup:

      cine_<state>_src.mp4              the render with NO tiles pasted (gitignored, local only)
      _scratch/tiles/<room>_<state>_<name>.mp4   each repair tile
      cine_<state>.patches.json         the patch list, each with an `enabled` flag

    Then the standard bake: 0.5 s crossfade + per-frame wrap-seam repair. Disabling every patch is a
    normal outcome, not an error — most of canyon's first-pass patches were animating bare rock.
    """
    room_dir = os.path.join(base, room)
    src = os.path.join(room_dir, "cine_%s_src.mp4" % state)
    if not os.path.isfile(src):
        raise RuntimeError("no unpatched source (%s) — cannot rebuild" % os.path.basename(src))
    pj = os.path.join(room_dir, "cine_%s.patches.json" % state)
    patches = json.load(open(pj, encoding="utf-8")) if os.path.isfile(pj) else []
    on = [p for p in patches if p.get("enabled", True)]

    work = os.path.join(WORK_ROOT, os.path.basename(base.rstrip("/")), room)
    os.makedirs(work, exist_ok=True)
    cur = src
    for p in on:
        tile = os.path.join(base, "_scratch", "tiles", "%s_%s_%s.mp4" % (room, state, p["name"]))
        if not os.path.isfile(tile):
            log("  patch %s: tile missing, skipped" % p["name"])
            continue
        b = p["box"]
        tb = CS.CR.tile_bounds(b, CS.CR.FULL_W, CS.CR.FULL_H)
        region = (b[0] * CS.CR.FULL_W, b[1] * CS.CR.FULL_H, b[2] * CS.CR.FULL_W, b[3] * CS.CR.FULL_H)
        nxt = os.path.join(work, "rebuild_%s_%s.mp4" % (state, p["name"]))
        CS.CR.composite_tile(cur, tile, tb, nxt, region_px=region)
        cur = nxt
        log("  re-applied patch %s" % p["name"])
    dest = os.path.join(room_dir, "cine_%s.mp4" % state)
    shutil.copyfile(cur, os.path.join(room_dir, "cine_%s_raw.mp4" % state))
    still, mk = _mask_inputs(base, room, state, cur, log)
    bake_loop(cur, dest, log=log, still=still, mask=mk)
    log("  rebuilt %s/%s with %d of %d patch(es)" % (room, state, len(on), len(patches)))
    return dest


def _record_patches(base, room, state, spec, res, unpatched, work, log=print):
    """File the inputs a repair decision needs LATER: the un-patched render, the tiles, and the list.

    A fresh render that composites a repair tile used to leave no record of it. `rebuild_clip` and the
    gallery's per-patch "drop" button both read `cine_<state>_src.mp4` + `cine_<state>.patches.json` +
    `_scratch/tiles/<room>_<state>_<name>.mp4`, and only `rebuild_clip` ever wrote them — so a tile
    applied by a first render was permanent, invisible in the Baked tab ("no patches") and impossible to
    drop without re-rendering the room. Lucas hit the need on j_c5 on 2026-09-01 and it only worked
    because an earlier rebuild had happened to leave those files behind.

    `_src.mp4` is written even when nothing was repaired, so a later hand-added tile has a base to
    rebuild from and the file set is the same shape for every clip."""
    room_dir = os.path.join(base, room)
    src_keep = os.path.join(room_dir, "cine_%s_src.mp4" % state)
    shutil.copyfile(unpatched, src_keep)                   # the render with NO tiles pasted
    repaired = res.get("repaired") or []
    pj = os.path.join(room_dir, "cine_%s.patches.json" % state)
    if not repaired:
        if os.path.isfile(pj):
            os.remove(pj)          # stale list from a previous render would name tiles that are gone
        return
    boxes = {sub["name"]: sub.get("box") for sub in (spec.get("subjects") or [])}
    tiles_dir = os.path.join(base, "_scratch", "tiles")
    os.makedirs(tiles_dir, exist_ok=True)
    patches = []
    for name in repaired:
        tile = os.path.join(work, "tile_%s.mp4" % name)
        if not os.path.isfile(tile):
            log("  ! repaired %s but its tile is missing — not recorded, so it cannot be dropped" % name)
            continue
        shutil.copyfile(tile, os.path.join(tiles_dir, "%s_%s_%s.mp4" % (room, state, name)))
        patches.append({"name": name, "box": boxes.get(name), "enabled": True})
    with open(pj, "w", encoding="utf-8") as f:
        json.dump(patches, f, indent=1)
    log("  patches: %s (droppable in the gallery)" % ", ".join(p["name"] for p in patches))


def run_state(st, spec, base, repair=True, reuse=False, log=print):
    """One state end to end; returns cine_stage's result dict plus where the clip was filed."""
    src = os.path.join(base, st["panorama"])
    work = os.path.join(WORK_ROOT, os.path.basename(base.rstrip("/")), st["room"])
    os.makedirs(work, exist_ok=True)
    out = os.path.join(work, "%s.mp4" % st["state"])
    res = CS.run(spec, src, out, repair=repair, reuse=reuse, log=log)
    if res.get("status") != "ok":
        return res
    # The clip that ships is the last composite if anything was repaired, else the base render —
    # then BAKED, so what lands in the room is the crossfaded loop, never the raw render.
    final = res.get("final") or out
    raw_keep = os.path.join(base, st["room"], "cine_%s_raw.mp4" % st["state"])
    shutil.copyfile(final, raw_keep)
    _record_patches(base, st["room"], st["state"], spec, res, out, work, log)
    dest = os.path.join(base, st["room"], "cine_%s.mp4" % st["state"])
    still, mk = _mask_inputs(base, st["room"], st["state"], final, log)
    bake_loop(final, dest, log=log, still=still, mask=mk)
    res["raw"] = os.path.relpath(raw_keep, base)
    res["filed"] = os.path.relpath(dest, base)
    return res


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--rooms", default=None, help="comma-separated subset; default every state")
    ap.add_argument("--dry-run", action="store_true", help="list what would run, render nothing")
    ap.add_argument("--no-repair", action="store_true")
    ap.add_argument("--reuse", action="store_true", help="skip a full-frame render whose clip exists")
    a = ap.parse_args()

    base = os.path.join(ROOMS, a.chapter, a.scenario)
    doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    rooms = set(a.rooms.split(",")) if a.rooms else None
    plan = states_to_run(doc, base, rooms)

    runnable = [(st, sp) for st, sp, why in plan if sp]
    print("%d state(s) to render, %d skipped" % (len(runnable), len(plan) - len(runnable)))
    for st, sp, why in plan:
        print("  %-12s %-8s %s" % (st["room"], st["state"], "RUN" if sp else "skip — " + why))
    if a.dry_run:
        return 0

    t0, results = time.time(), []
    for i, (st, spec) in enumerate(runnable, 1):
        print("\n[%d/%d] %s/%s" % (i, len(runnable), st["room"], st["state"]), flush=True)
        try:
            res = run_state(st, spec, base, repair=not a.no_repair, reuse=a.reuse,
                            log=lambda m: print("   " + m, flush=True))
        except Exception as e:                       # one bad state must not lose the rest of the run
            print("   FAILED — %s" % str(e)[:200], flush=True)
            results.append({"room": st["room"], "state": st["state"], "status": "error"})
            continue
        res["room"], res["state"] = st["room"], st["state"]
        results.append(res)

    print("\n=== SUMMARY (%d min) ===" % round((time.time() - t0) / 60))
    for r in results:
        subs = r.get("subjects_after") or r.get("subjects") or []
        dead = [s["name"] for s in subs if s["verdict"] == "dead"]
        print("%-12s %-8s %-6s repaired=%-22s %s"
              % (r.get("room"), r.get("state"), r.get("status"),
                 ",".join(r.get("repaired") or []) or "-",
                 ("STILL DEAD: " + ",".join(dead)) if dead else "all subjects alive/weak"))
    print("\nCLIPS ARE NOT WIRED. Look at every one before attaching it — metrics screen out, they "
          "cannot certify (cinemagraph_handoff.md §2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
