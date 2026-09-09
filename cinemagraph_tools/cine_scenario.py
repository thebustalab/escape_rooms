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


def paint_out_boxes(base, room, state):
    """The HAND-DRAWN pins for this (room, state), from `cine_<state>.mask.json` -> `paintOut`.

    THE SECOND SOURCE OF PINS, and the one a human owns. An authored `still: True` subject is a claim
    about the room — this thing is not supposed to move — and it belongs in the motion spec, travels
    into the render prompt, and is worth a re-render to get right. A paint-out is a much smaller claim:
    *whatever* that rectangle is doing, do not let it reach the player. It is pure bake-time, costs a
    `rebuild_clip` and no GPU, and it is the affordance the two mask sliders cannot provide.

    WHY IT HAD TO EXIST BEFORE THE LOOP COULD STOP SUPPRESSING (2026-09-06). The plan is that the
    overnight loop gets one or two hero motions alive and leaves everything else to Lucas's mask pass.
    But the mask he had was `thresh` and `region`, and both of those SELECT FOR MOTION — the canon
    entry is explicit that no rung of either can drop a churning codex without dropping the drifting
    dust several rungs earlier. So "I'll handle the rest in the mask" was not yet true of the mask that
    existed: the only thing that could remove a specific unwanted mover was a spec pin, i.e. exactly the
    authoring the change was meant to avoid. This closes that gap.

    Boxes are [x0, y0, x1, y1] image fractions, the same convention as a motion-spec box.
    """
    sj = os.path.join(base, room, "cine_%s.mask.json" % state)
    if not os.path.isfile(sj):
        return []
    try:
        cfg = json.load(open(sj, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for i, b in enumerate(cfg.get("paintOut") or []):
        box = b.get("box") if isinstance(b, dict) else b
        if isinstance(box, (list, tuple)) and len(box) == 4:
            nm = (b.get("name") if isinstance(b, dict) else None) or "paint_%d" % (i + 1)
            out.append({"name": nm, "box": list(box)})
    return out


def mover_boxes(base, room, state):
    """The boxes the spec says SHOULD move, as {name, box} — the hero(es) if any are marked, else
    every non-`still` subject.

    Hero-first is deliberate. Under the one-or-two-hero policy the hero is the motion the room is
    promised to show; an incidental mover named alongside it is something nobody promised, and the
    whole point of the box mask is that only promised motion reaches the player. A spec authored
    before the `hero` flag existed has no heroes, so it falls back to all its movers and behaves as
    it always did.
    """
    try:
        doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    node = next((r for r in doc.get("rooms") or [] if r.get("key") == room), None)
    spec = ((node or {}).get("authoring") or {}).get("motionSpec")
    if isinstance(spec, dict) and state != "base":
        spec = (spec.get("states") or {}).get(state)
    subs = [s for s in ((spec or {}).get("subjects") or [])
            if not s.get("still") and isinstance(s.get("box"), (list, tuple))]
    heroes = [s for s in subs if s.get("hero")]
    use = heroes or subs
    return [{"name": s.get("name"), "box": list(s["box"])} for s in use]


def box_mask(base, room, state, size, mover=None, still_boxes=None, feather=24):
    """The playback mask built FROM THE AUTHORED BOXES, not from measured motion magnitude.

    WHY THIS EXISTS, AND WHY THE THRESHOLD COULD NOT DO IT (2026-09-07, Lucas). The auto threshold
    chooses which pixels play the video by how hard they move, and on this corpus the hardest-moving
    thing is not the hero — it is the render's own drift of the rigid scene. Measured on
    fenwatch/base frame 0 against frame 30: the mist box changed at p95 19 while the office and yard
    STONE changed at p95 40, twice as hard. So every rung of the threshold ladder kept the drift and
    dropped the mist, and no rung could do otherwise; the search was well-posed and the answer was
    that magnitude cannot separate them.
    A box can, because the spec already says where the motion is supposed to be. Baking fenwatch with
    the hero box as the mask took the stone from p95 40.00 to **0.00** and the slate roof from 27.00
    to 0.00 while the mist kept its 21.00, at 8.4% coverage against the threshold's 71.2%.

    THIS IS HOW THE BOXED ERA WORKED, and losing it is what broke the pipeline. `wrangling/trees`
    animates cloud and mist convincingly — Lucas: "I know for a fact that trees has clouds and mist
    moving in it, though it was done with the old style box cinemagraphs" — and its clips are small
    crops (416x448, 640x320) where the object fills the frame. The box WAS the mask, so drift outside
    it was never in the picture. Replacing that with a magnitude threshold quietly discarded the one
    thing that made it work.

    THE BOX MUST CONTAIN THE WHOLE MOVING OBJECT. A feathered edge across a region that goes on
    moving past it reads as motion stopping where it shouldn't — Lucas's own report of the old boxed
    clips, and the same failure `tile_bounds` warns about for tiles. That is why the box wants a human
    look, and it is the argument for drawing it during the hotspot phase (todo.md).
    """
    import numpy as np
    from PIL import Image, ImageFilter
    W, H = size
    m = np.zeros((H, W), np.float32)
    used = []
    for b in (mover or []):
        try:
            x0, y0, x1, y1 = [float(v) for v in b["box"]]
        except Exception:  # noqa: BLE001
            continue
        c0, r0 = int(round(x0 * W)), int(round(y0 * H))
        c1, r1 = int(round(x1 * W)), int(round(y1 * H))
        if c1 <= c0 or r1 <= r0:
            continue
        m[r0:r1, c0:c1] = 1.0
        used.append(b.get("name") or "unnamed")
    if not used:
        return None, None
    img = Image.fromarray((m * 255).astype("uint8"), "L")
    if feather:
        # Softened so the boundary is not a hard rectangle. Canon: a pin edge is invisible where
        # nothing moves and glaring where something does, so the edge wants to fall off gradually.
        img = img.filter(ImageFilter.GaussianBlur(feather))
    a = np.asarray(img, np.float32) / 255.0
    # PINS LAST, as in the threshold path: a `still` subject inside a mover box must still win.
    pinned = []
    for b in (still_boxes or []):
        try:
            x0, y0, x1, y1 = [float(v) for v in b["box"]]
        except Exception:  # noqa: BLE001
            continue
        c0, r0 = int(round(x0 * W)), int(round(y0 * H))
        c1, r1 = int(round(x1 * W)), int(round(y1 * H))
        if c1 <= c0 or r1 <= r0:
            continue
        a[r0:r1, c0:c1] = 0.0
        pinned.append(b.get("name") or "unnamed")
    d = os.path.join(base, "_scratch", "motion")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, "bakemask_%s_%s.png" % (room, state))
    Image.fromarray((np.clip(a, 0, 1) * 255).astype("uint8"), "L").save(out)
    meta = {"pct": "boxes", "maskMode": "boxes", "boxes": used, "feather": feather,
            "coverage": round(float(np.clip(a, 0, 1).mean()), 4), "region": 0.0, "minPx": 0,
            "threshold": None}
    if pinned:
        meta["stillBoxes"] = pinned
    return out, meta


def _still_boxes(base, room, state):
    """Every pin the bake must honour for this (room, state), as {name, box}.

    TWO SOURCES, UNIONED: the authored `still: True` subjects of the motion spec, and the hand-drawn
    `paintOut` rectangles from the mask sidecar (`paint_out_boxes`). Both end up forced black in the
    playback mask, because a pin is a pin once it reaches the bake — what differs is who owns it and
    whether it also shapes the render prompt.

    Resolved from disk HERE rather than passed in, so that every path to a bake honours the pins —
    including the gallery's "commit mask + re-bake" and the per-patch rebuild, neither of which has a
    spec in hand. A pin that survived a render but was dropped by a re-bake would be worse than no pin
    at all, because it would come back only sometimes."""
    authored = []
    try:
        doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a clips-only fixture has no scenario; nothing is authored
        doc = None
    if doc is not None:
        node = next((r for r in doc.get("rooms") or [] if r.get("key") == room), None)
        spec = ((node or {}).get("authoring") or {}).get("motionSpec")
        if isinstance(spec, dict) and state != "base":
            spec = (spec.get("states") or {}).get(state)
        subs = (spec or {}).get("subjects") or []
        authored = [{"name": s.get("name"), "box": s["box"]}
                    for s in subs if s.get("still") and isinstance(s.get("box"), (list, tuple))]
    return authored + paint_out_boxes(base, room, state)


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
    pct, region, cfg = "auto", 0.0, {}
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

    # ---- MASK MODE: boxes by default, threshold only as a fallback (2026-09-07) -------------------
    # `maskMode` in the sidecar is an authored override ("boxes" | "auto" | a percentile via `pct`).
    # With nothing authored, a state that HAS mover boxes uses them, because the threshold provably
    # cannot separate the hero from the render's drift of the rigid scene — see `box_mask`. A state
    # with no mover boxes (a boxed-era clip with no spec) has nothing to build a box mask from and
    # keeps the old behaviour.
    mode = cfg.get("maskMode")
    movers = mover_boxes(base, room, state)
    if mode is None:
        mode = "boxes" if movers else "auto"
    if mode == "boxes" and movers:
        from PIL import Image as _Im  # noqa: WPS433
        with _Im.open(still) as _s:
            size = _s.size
        mk, meta = box_mask(base, room, state, size, mover=movers, still_boxes=pins,
                            feather=int(cfg.get("feather", 24)))
        if mk is None:                        # every box malformed — do not ship an unmasked clip
            log("  box mask produced nothing; falling back to the threshold")
            mk, meta = mask_png(base, room, state, clip, pct, region, still_boxes=pins)
        else:
            log("  mask: BOXES (%s) feather=%d -> %.1f%% video, rest still"
                % (", ".join(meta["boxes"]), meta["feather"], 100 * meta["coverage"]))
    else:
        mk, meta = mask_png(base, room, state, clip, pct, region, still_boxes=pins)
        log("  mask: pct=%s region=%gppm(%dpx) thr=%.2f -> %.1f%% video, rest still"
            % (meta["pct"], meta["region"], meta["minPx"], meta["threshold"],
               100 * meta["coverage"]))
    # PRESERVE `paintOut` ACROSS THIS REWRITE. `meta` is what the mask builder measured — pct, region,
    # threshold, coverage — and this line replaces the whole sidecar with it. The hand-drawn pins live
    # in the SAME file, so writing `dict(meta, ...)` alone deletes them, and it deletes them on the very
    # next bake: paint a box, commit it, then drop a repair patch, and the boxes are gone with no error
    # anywhere. That is the same shape as the stale-copy warning in authoring_v2/AGENTS.md ("a stale copy
    # makes commit mask + re-bake silently drop the pins") and it wants the same treatment — carry the
    # authored keys forward explicitly rather than trusting a wholesale overwrite.
    keep = {k: cfg[k] for k in ("paintOut", "maskMode", "feather") if k in cfg}
    json.dump(dict(meta, enabled=True, **keep), open(sj, "w", encoding="utf-8"), indent=1)
    if meta.get("stillBoxes"):
        log("  pinned still: %s" % ", ".join(meta["stillBoxes"]))
    return still, mk


def paced(base, room, state, dest, log=print):
    """Slow a baked clip down IN PLACE, if this clip's sidecar asks for it.

    OPT-IN per clip via `cine_<state>.mask.json` -> `"pace": 1.5` (a multiplier: 1 = as rendered,
    1.5 = half again as long, 2 = twice as long). Absent or 1 leaves the file untouched.

    APPLIED AFTER `bake_loop`, not before. The retime rewrites presentation timestamps and the
    container rate only; `bake_loop` re-encodes at its own constant rate, so anything done earlier is
    discarded. This runs on the finished file and rewrites it.

    HOW (changed 2026-09-09): MOTION-COMPENSATED INTERPOLATION, not frame-holding. Intermediate frames
    are estimated from the optical flow, so the clip lasts longer at a full 24 fps instead of showing
    each original frame for longer. Lucas judged the two head to head at a matched 2x on the same clip
    and again at 3x and 4x on hard-edged water: interpolation won, and the held version reads as a
    slideshow as the factor rises.

    CAPPED AT 2.5x, on his call: "a 3x slowdown is hard to recover from ... 2x or 2.5x is probably the
    most that will look reasonable, if it needs more than that then a re-roll is probably better."

    The earlier frame-HOLD is kept as `--hold` for the record; it is what he called "okay at best".
    Both differ from the recorded dead end, which was retiming by DUPLICATION ("they look 'slowed', not
    natural"). Interpolation invents genuine in-between frames; duplication invents nothing:

      * Retiming by frame duplication was tried on the quay at half and third speed and Lucas's verdict
        was "they look 'slowed', not natural" — duplication is not new motion.
      * Slowing the GENERATION by raising `LTXVConditioning.frame_rate` was tried on 2026-09-08 at 36,
        48 and 72 against a 24 baseline and it does not work: measured adjacent-frame difference went
        1.00 -> 1.19 -> 1.60 -> 1.05, i.e. FASTER and non-monotone, because the model is trained around
        24-25 and an out-of-distribution rate buys per-frame incoherence rather than slower movement.

    Lucas accepted this hold at 1.5x on cropping_weld ("that slow down that you did that you're calling
    hold that worked"), which is why it is the mechanism wired here. The trade is real and is the reason
    this is opt-in rather than a default: fewer frames per second of playback means the motion can
    judder, and how much is tolerable depends on the clip.
    """
    sj = os.path.join(base, room, "cine_%s.mask.json" % state)
    if not os.path.isfile(sj):
        return dest
    try:
        cfg = json.load(open(sj, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return dest
    try:
        pace = float(cfg.get("pace") or 1.0)
    except Exception:  # noqa: BLE001
        return dest
    if pace <= 1.001:
        return dest
    # 2.5x is the ceiling Lucas set by eye; beyond it a re-roll beats a slowdown.
    if pace > 2.5:
        log("  pace %.2fx requested; capping at 2.5x — beyond that a re-render is the better move" % pace)
        pace = 2.5
    fps = CS.CR.FPS
    work = os.path.join(WORK_ROOT, os.path.basename(base.rstrip("/")), room)
    os.makedirs(work, exist_ok=True)
    tmp = os.path.join(work, "pace_%s.mp4" % state)
    hold = bool((cfg or {}).get("paceHold"))
    if hold:
        f2 = fps / pace
        vf = "settb=1/%.6f,setpts=N/%.6f/TB" % (f2, f2)
        rate = "%.6f" % f2
    else:
        vf = ("minterpolate=fps=%.6f:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
              "settb=1/%.6f,setpts=N/%.6f/TB" % (fps * pace, fps, fps))
        rate = "%.6f" % fps
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", dest, "-vf", vf,
           "-r", rate, "-c:v", "libx264", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp]
    try:
        subprocess.run(cmd, check=True)
        shutil.copyfile(tmp, dest)
    except Exception as e:  # noqa: BLE001
        # A failed retime must not lose the clip: keep the baked file and say so.
        log("  pace %.2fx FAILED (%s) — keeping the clip at rendered pace" % (pace, str(e)[:120]))
        return dest
    log("  paced %.2fx by %s" % (pace, "holding frames" if hold else "motion-compensated interpolation"))
    return dest


def colour_normalised(base, room, state, clip, log=print):
    """Flatten a whole-frame brightness/colour drift, if this clip's sidecar asks for it.

    OPT-IN, per clip, via `cine_<state>.mask.json` -> `"colourNormalise": true` (or a float strength
    0..1). Returns the path to use for the bake — the input unchanged when the flag is absent, which is
    every clip until someone sets it.

    WHY IT IS OPT-IN AND NOT A DEFAULT. `colour_normalise.py`'s own docstring is the warning: it is a
    GLOBAL per-frame gain, so it can only fix a defect that is itself global, and `colour_normalise` is
    listed in the motion skill as "NOT a default step — it can introduce visible brightness pumping".
    A night room lit by a fire is *supposed* to change brightness over the loop; flattening that would
    remove the thing the room is for.

    WHY IT IS WIRED AT ALL (anvil/night, 2026-09-06). This is the one defect class the mask provably
    cannot touch, and the overnight loop proved it rather than guessing: it simulated the bake at mask
    percentiles 46/60/75/85/90/93/96 and showed the bright pavement's brightening arc carries a LARGER
    temporal std than the village lamps, so any mask tight enough to kill the swing kills the subjects
    first (by p93 the pavement still swings 4.75 while `village_lamps` has collapsed to 0.45). It then
    measured this tool on the same clip: frame swing 3.86 -> 0.31, pavement 11.03 -> 2.61, with the
    subjects still alive (village_lamps 4.99 -> 4.37, river_glimmer 7.63 -> 6.60). And it could not act,
    because the tool was ORPHANED — `grep` found no importer anywhere in the bake chain. That is the
    "settled finding with no call site" failure this directory's AGENTS.md exists to prevent, hit for
    the sixth time, so it gets a call site.

    It is also why this belongs here rather than in the loop: with the loop hero-gated, a whole-frame
    swing is report-only and will never book a re-render. Flattening it is a bake decision, free, and
    re-runnable — the same shape as a pin.
    """
    sj = os.path.join(base, room, "cine_%s.mask.json" % state)
    if not os.path.isfile(sj):
        return clip
    try:
        cfg = json.load(open(sj, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return clip
    want = cfg.get("colourNormalise")
    if not want:
        return clip
    strength = 1.0 if want is True else max(0.0, min(1.0, float(want)))
    if strength <= 0:
        return clip
    work = os.path.join(WORK_ROOT, os.path.basename(base.rstrip("/")), room)
    os.makedirs(work, exist_ok=True)
    dst = os.path.join(work, "cn_%s.mp4" % state)
    try:
        sys.path.insert(0, HERE)
        from colour_normalise import normalise  # noqa: WPS433
        drift, n = normalise(clip, dst, strength)
    except Exception as e:  # noqa: BLE001
        # A failed normalise must not lose the clip — bake the un-normalised source and SAY SO, rather
        # than raising out of a bake the caller expects to produce a file.
        log("  colour-normalise FAILED (%s) — baking un-normalised" % str(e)[:120])
        return clip
    log("  colour-normalised at strength %.2f: input drift was %.2f over %d frames"
        % (strength, drift, n))
    return dst


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
    # `_raw` is kept UN-normalised on purpose: it is the record of what the render produced, and the
    # normalise is a reversible post step. Measure the mask against the same frames the bake sees.
    cur = colour_normalised(base, room, state, cur, log)
    still, mk = _mask_inputs(base, room, state, cur, log)
    bake_loop(cur, dest, log=log, still=still, mask=mk)
    paced(base, room, state, dest, log)
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
    final = colour_normalised(base, st["room"], st["state"], final, log)
    still, mk = _mask_inputs(base, st["room"], st["state"], final, log)
    bake_loop(final, dest, log=log, still=still, mask=mk)
    paced(base, st["room"], st["state"], dest, log)
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
