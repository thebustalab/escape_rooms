#!/usr/bin/env python3
"""place_hotspots.py — DRAFT hotspot boxes for every room of a scenario, from its scene specs.

Runs `localizer.py` per room and writes the results onto each room's `plannedHotspots` as draft boxes,
matched by the spec element's own `label`. Explicitly DRAFT: Lucas drags them in the test play, and his
corrections are the first real ground truth (see `notes/scenario_pipeline_vision.md` → *Who should place
hotspots*). Nothing here is treated as final.

THE COLLAPSE CHECK, and why it exists. Grounding DINO — the localizer's default engine — was run on
canyon `j_c1` and returned **five of seven elements as the same box** (~[0.61,0.39,0.71,0.89]). Distinct
objects cannot share a box, so that is machine-detectable nonsense, and writing it as drafts would put
five hotspots on one rock. `--engine gpt4o` did not collapse and returned the elements in the spec's own
left-to-right order. So: refuse to write any room whose predictions collapse, and say so loudly rather
than degrading quietly.

WHAT IT DOES NOT DO. It does not place `ambient` carriers (full-frame, no box needed) and it does not
touch a room whose hotspots are already committed — a draft must never overwrite authored work.

`--commit-boxes` (2026-09-04) RELAXES THAT REFUSAL, PRECISELY. The blanket "has committed hotspots"
test conflates two different things: boxes a human placed, and boxes that were committed unplaced. A
scenario reaches the latter state normally — `_apply_spec` commits hotspots carrying `scene_spec`'s
`approx_boxes`, which are uniform stubs derived from an `at` phrase, and doors commit with no box at
all. `networks/beacons` sat in exactly that state: 17 of 43 non-ambient hotspots had a stub box (mostly
a literal 0.1x0.2 rectangle) and the other 26 — every door — had `box: null`. Refusing those rooms
protects nothing and leaves the scenario unplaceable.

So the guard becomes the thing it was always proxying for: **`boxSource`**. A hotspot marked
`review:lucas` is a box a human dragged and is never overwritten; a stub, a `draft:localizer` or a
boxless hotspot may be re-drafted. This mode writes to `hotspots` (what the game reads) and mirrors the
same box onto the matching `plannedHotspots` entry so the two layers cannot disagree, and it writes
scenario.json DIRECTLY rather than through `/api/room-patch` — a long-running harness may be serving
older code than the tree, and the placement pass must not depend on which.

  place_hotspots.py --chapter hierarchical_clustering --scenario canyon [--rooms j_c1,j_c4] [--dry-run]

Needs OPENAI_API_KEY. It lives in ~/.bashrc BELOW the non-interactive guard, so a plain subprocess does
not have it: resolve it at call time from a login shell, exactly as the harness's `gen_env()` does.
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOMS = os.path.join(HERE, "..", "rooms")
HARNESS = "http://127.0.0.1:8752"

# Two boxes this close in every coordinate are the same box. DINO's collapse put five elements within
# ~0.002 of each other; genuinely distinct objects in these panoramas are never that close.
COLLAPSE_TOL = 0.02
COLLAPSE_MAX_SHARE = 0.4      # fraction of elements allowed to share one cluster before the room fails


def _same(a, b, tol=COLLAPSE_TOL):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def collapsed(pred):
    """(is_collapsed, biggest_cluster). A run where most elements land on one box is a failed run."""
    boxes = [(k, v["box"]) for k, v in pred.items() if v and v.get("box")]
    if len(boxes) < 3:
        return False, []
    best = []
    for _k, b in boxes:
        grp = [k2 for k2, b2 in boxes if _same(b, b2)]
        if len(grp) > len(best):
            best = grp
    return (len(best) > max(2, len(boxes) * COLLAPSE_MAX_SHARE)), best


def _key_env():
    """Environment for the localizer subprocess, carrying OPENAI_API_KEY even when ours doesn't.

    The key is exported from `~/.bashrc` BELOW the "if not running interactively, return" guard, so it
    reaches an interactive terminal and nothing else — not a plain subprocess, not `bash -lc`, not this
    script when an agent runs it. The module docstring said to resolve it "exactly as the harness's
    `gen_env()` does" and then never did, so every room failed with a flat "OPENAI_API_KEY not set"
    (all nine canyon rooms, 2026-08-31). `-i` is the part that reads `~/.bashrc`; the value is only ever
    put in the child environment, never printed or written.
    """
    env = os.environ.copy()
    if env.get("OPENAI_API_KEY"):
        return env
    try:
        r = subprocess.run(["bash", "-lic", 'printf %s "${OPENAI_API_KEY:-}"'],
                           capture_output=True, text=True, timeout=20)
        key = (r.stdout or "").strip()
    except Exception:  # noqa: BLE001
        key = ""
    if key:
        env["OPENAI_API_KEY"] = key
    return env


def localize_room(base, room, engine="gpt4o"):
    node = next((r for r in json.load(open(os.path.join(base, "scenario.json"),
                                            encoding="utf-8")).get("rooms", []) if r.get("key") == room), None)
    spec = ((node or {}).get("authoring") or {}).get("sceneSpec")
    if not spec:
        raise RuntimeError("%s has no sceneSpec" % room)
    tmp = "/tmp/_place_%s.json" % room
    json.dump(spec, open(tmp, "w"), indent=1)
    scene = os.path.join(base, room, "scene.png")
    if not os.path.isfile(scene):
        raise RuntimeError("%s has no committed scene.png" % room)
    out = subprocess.run([sys.executable, os.path.join(HERE, "localizer.py"),
                          "--scene", scene, "--spec", tmp, "--engine", engine],
                         capture_output=True, text=True, timeout=300, env=_key_env())
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout).strip()[-300:])
    pred = {}
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith("["):
            try:
                box = json.loads(line[line.index("["):line.index("]") + 1])
                pred[parts[0]] = {"box": [round(float(v), 4) for v in box]}
            except Exception:  # noqa: BLE001
                pass
    return spec, pred


def _slug(x):
    return " ".join((x or "").strip().lower().split())


# Corpus floor for a clickable box. Measured across the 251 non-ambient boxes in the eleven shipped
# scenarios: width p05 0.020, height p05 0.061 (medians 0.066 / 0.254). The refine pass measures the
# object's actual pixels, which is right for accuracy and can be too small to TAP — it returned a
# 0.016-wide box for a spyglass tube. So a refined box below the floor is grown around its own measured
# centre, never re-placed: the position stays the model's, only the target area changes.
MIN_W, MIN_H = 0.020, 0.061


def _floor_box(b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = max(MIN_W, x1 - x0), max(MIN_H, y1 - y0)
    nx0, nx1 = max(0.0, cx - w / 2), min(1.0, cx + w / 2)
    ny0, ny1 = max(0.0, cy - h / 2), min(1.0, cy + h / 2)
    return [round(nx0, 4), round(ny0, 4), round(nx1, 4), round(ny1, 4)]


def refine_pred(base, room, spec, pred, env):
    """Second pass: re-measure each first-pass box on a native-resolution crop (localizer.refine_box).

    Returns (pred, stats). A refusal (the crop did not contain the object) KEEPS the first-pass box and
    is counted — a first pass that landed on the wrong side of the room cannot be rescued by a crop of
    the wrong place, and silently substituting the nearest similar object is exactly the failure the
    refine prompt forbids.
    """
    sys.path.insert(0, HERE)
    import localizer as L
    scene = os.path.join(base, room, "scene.png")
    byid = {e["id"]: e for e in spec.get("elements", [])}
    key = env.get("OPENAI_API_KEY")
    refined = kept = floored = 0
    for eid, v in pred.items():
        if not v.get("box"):
            continue
        e = byid.get(eid) or {}
        target = {"id": eid, "desc": e.get("desc") or e.get("label") or eid, "label": e.get("label")}
        try:
            nb = L.refine_box(scene, v["box"], target, api_key=key)
        except Exception:  # noqa: BLE001
            nb = None
        if not nb:
            kept += 1
            continue
        fb = _floor_box(nb)
        if fb != nb:
            floored += 1
        v["box"] = fb
        refined += 1
    return pred, {"refined": refined, "kept": kept, "floored": floored}


def art_fingerprint(base, room):
    """A short digest of the room's committed panorama — the identity boxes are measured AGAINST.

    WHY THIS EXISTS (2026-09-15). Beacons' 43 boxes were placed on 09-04 and every base panorama was
    regenerated on 09-14. `/api/commit-room` deliberately KEEPS a room's boxes when its art is swapped
    (so a re-roll does not throw away hand-placement), and nothing else re-measured them — so every
    hotspot in the scenario pointed at a picture that no longer existed, for eleven days, silently. A
    puzzle box sat on a window ledge above its desk; a door box sat on a stone wall. Nothing in the
    pipeline could tell, because a box carries no record of what it was measured on.

    mtime is not enough (Syncthing rewrites it); the bytes are the identity.
    """
    p = os.path.join(base, room, "scene.png")
    if not os.path.isfile(p):
        return None
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def stamp_boxes_from(node, base, room):
    """Record the art the boxes were just measured against, on the room's `authoring` block."""
    fp = art_fingerprint(base, room)
    if not fp:
        return
    node.setdefault("authoring", {})["boxesFrom"] = {
        "art": fp, "at": datetime.datetime.now().isoformat(timespec="seconds")}


def boxes_are_stale(node, base, room):
    """True when the committed art is NOT the art the boxes were measured on.

    Unknown (no stamp) is NOT stale — every scenario predating the stamp would otherwise scream. Those
    are caught by the stamp being absent, which `validate_scenes` reports separately.
    """
    rec = ((node.get("authoring") or {}).get("boxesFrom") or {})
    if not rec.get("art"):
        return False
    fp = art_fingerprint(base, room)
    return bool(fp and fp != rec["art"])


def apply_room_committed(base, room, spec, pred, dry_run=False):
    """Write boxes onto the COMMITTED hotspots, mirroring onto plannedHotspots. See `--commit-boxes`.

    Matches on the spec element's `label` first and its `id` second: labels are the harness's own
    planned->placed key and are unique within a room, but a door committed from an older spec can carry
    the id while the label has since been reworded.
    """
    P = os.path.join(base, "scenario.json")
    doc = json.load(open(P, encoding="utf-8"))
    node = next((r for r in doc.get("rooms", []) if r.get("key") == room), None)
    if node is None:
        return 0, ["no such room"]
    by_label, by_id = {}, {}
    for e in spec.get("elements", []):
        box = (pred.get(e.get("id")) or {}).get("box")
        if not box:
            continue
        by_id[e["id"]] = box
        if e.get("label"):
            by_label[_slug(e["label"])] = box
    n, notes, skipped = 0, [], 0
    for layer in ("hotspots", "plannedHotspots"):
        for h in (node.get(layer) or []):
            if h.get("type") == "ambient":
                continue
            if str(h.get("boxSource") or "").startswith("review:"):
                # ANY reviewed box is left alone, not just Lucas's. `review:agent-vision` marks a box an
                # agent measured off the art by eye after the localiser got it wrong — 16 of 43 on
                # beacons — and re-running the draft pass would silently undo exactly the corrections
                # that were worth making. If the ART changes, the `boxesFrom` stamp stops matching and
                # `validate_scenes` fails the room, which is the right way to find out.
                skipped += 1
                continue
            box = by_label.get(_slug(h.get("label"))) or by_id.get(h.get("id"))
            if not box:
                if layer == "hotspots":
                    notes.append("no prediction for %r" % (h.get("label") or h.get("id")))
                continue
            h["box"] = box
            h["boxSource"] = "draft:localizer"
            if layer == "hotspots":
                n += 1
    if skipped:
        notes.append("%d hand-reviewed box(es) left alone" % skipped)
    if not dry_run and n:
        stamp_boxes_from(node, base, room)
        json.dump(doc, open(P, "w", encoding="utf-8"), indent=2)
    return n, notes


def apply_room(base, chapter, scenario, room, spec, pred, dry_run=False):
    """Write boxes onto plannedHotspots, matched by the spec element's `label`."""
    doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    node = next((r for r in doc.get("rooms", []) if r.get("key") == room), None)
    if node is None:
        return 0, ["no such room"]
    if node.get("hotspots"):
        return 0, ["already has committed hotspots — refusing to overwrite authored work"]
    by_label = {}
    for e in spec.get("elements", []):
        if e.get("label") and pred.get(e["id"], {}).get("box"):
            by_label[e["label"].strip().lower()] = (e["id"], pred[e["id"]]["box"])
    planned = [dict(h) for h in (node.get("plannedHotspots") or [])]
    n, notes = 0, []
    for h in planned:
        lab = (h.get("label") or "").strip().lower()
        if lab in by_label:
            eid, box = by_label[lab]
            h["box"] = box
            h["boxSource"] = "draft:localizer"      # so the test play can show which are unreviewed
            h.setdefault("id", eid)
            n += 1
        else:
            notes.append("no spec element matched %r" % h.get("label"))
    if dry_run or not n:
        return n, notes
    r = urllib.request.urlopen(urllib.request.Request(
        HARNESS + "/api/room-patch",
        data=json.dumps({"chapter": chapter, "scenario": scenario, "roomKey": room,
                         "fields": {"plannedHotspots": planned}}).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)
    if not json.load(r).get("ok"):
        notes.append("room-patch failed")
    return n, notes


def write_motion_boxes(base, room, spec, pred, dry_run=False):
    """Copy the measured box of each `animate` element into `authoring.motionSpec.subjects[].box`.

    WHY IT BELONGS HERE AND NOT AT CINE TIME. The motion subject's box has to be MEASURED off the
    committed image — guessing it from the element's `at` phrase puts the mask over the wrong region,
    and `cine_scenario` will happily animate whatever is inside it. This pass has already paid for that
    measurement: `localizer.py` measures every element in the spec, and the `animate` element is in
    there even though it gets no hotspot (box cinemagraphs were retired 2026-09-02). So the box is free.

    Subjects are matched to elements BY ID, which is how `motion_spec_from()` names them.
    """
    path = os.path.join(base, "scenario.json")
    doc = json.load(open(path, encoding="utf-8"))
    node = next((r for r in doc.get("rooms", []) if r.get("key") == room), None)
    ms = ((node or {}).get("authoring") or {}).get("motionSpec")
    if not ms or not ms.get("subjects"):
        return []
    written = []
    for sub in ms["subjects"]:
        box = (pred.get(sub.get("name")) or {}).get("box")
        if not box:
            continue
        sub["box"] = [round(float(v), 4) for v in box]
        sub["boxSource"] = "measured:localizer"
        written.append("%s %s" % (sub["name"], sub["box"]))
    if written and not dry_run:
        json.dump(doc, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return written


def contact_sheet(base, room, out_dir="/tmp/hs_sheets", width=980, tile_h=460):
    """One image per room: every box drawn on the CURRENT art, with context, labelled.

    The localiser is right about two thirds of the time here — reliable on framed architecture
    (doorways, gates, flights of steps) and on large near objects, unreliable on a small object sitting
    on a support (it boxes the tripod, not the spyglass) and on a path across open ground (it boxes the
    nearest object instead). So a placement pass is not finished until someone has LOOKED. This makes
    looking one command instead of a hand-rolled crop script.
    """
    from PIL import Image, ImageDraw
    doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    node = next((r for r in doc.get("rooms", []) if r.get("key") == room), None)
    png = os.path.join(base, room, "scene.png")
    if node is None or not os.path.isfile(png):
        return None
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(png).convert("RGB")
    W, H = im.size
    tiles = []
    for h in (node.get("hotspots") or []):
        b = h.get("box")
        if not b or len(b) != 4 or list(b) == [0, 0, 1, 1]:
            continue                       # a full-frame ambient carrier has nothing to look at
        x0, y0, x1, y1 = b
        bw, bh = (x1 - x0) * W, (y1 - y0) * H
        px0, px1 = max(0, int(x0 * W - bw)), min(W, int(x1 * W + bw))
        py0, py1 = max(0, int(y0 * H - bh)), min(H, int(y1 * H + bh))
        crop = im.crop((px0, py0, px1, py1))
        dr = ImageDraw.Draw(crop)
        dr.rectangle([int(x0 * W) - px0, int(y0 * H) - py0, int(x1 * W) - px0, int(y1 * H) - py0],
                     outline=(255, 165, 0), width=max(2, crop.width // 200))
        sc = min(width / crop.width, tile_h / crop.height)
        crop = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))), Image.LANCZOS)
        canvas = Image.new("RGB", (width, crop.height), (0, 0, 0))
        canvas.paste(crop, ((width - crop.width) // 2, 0))
        bar = Image.new("RGB", (width, 24), (12, 18, 24))
        ImageDraw.Draw(bar).text((6, 6), "%s · %s · %s" % (h.get("type"), h.get("id"),
                                                          (h.get("label") or "")[:60]),
                                 fill=(255, 200, 120))
        tiles.append((bar, canvas))
    if not tiles:
        return None
    sheet = Image.new("RGB", (width, sum(b.height + c.height + 5 for b, c in tiles)), (0, 0, 0))
    y = 0
    for bar, c in tiles:
        sheet.paste(bar, (0, y)); y += bar.height
        sheet.paste(c, (0, y)); y += c.height + 5
    out = os.path.join(out_dir, "%s.png" % room)
    sheet.save(out)
    return out


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--rooms", default=None, help="comma-separated; default every room with art")
    ap.add_argument("--engine", default="gpt4o", choices=["gpt4o"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refine", action="store_true",
                    help="SECOND PASS: re-measure every first-pass box on a native-resolution crop. "
                         "The single pass reads a 0.1 grid on a 1536-px downscale and returns "
                         "region-accurate, object-inaccurate boxes; this fixes that. One extra vision "
                         "call per hotspot.")
    ap.add_argument("--motion", action="store_true",
                    help="ALSO write each room's hero-motion subject box into `authoring.motionSpec`, "
                         "measured in the SAME pass. The localizer already measures every element in "
                         "the spec — including the `animate` one, which gets no hotspot since box "
                         "cinemagraphs were retired — so the box is free once the pass has run. "
                         "Without this the motion subject has to be measured by hand at cine time, "
                         "which is how a subject box comes to be guessed from its `at` phrase instead "
                         "of read off the committed image.")
    ap.add_argument("--sheet", action="store_true",
                    help="ALSO write a per-room contact sheet (every box drawn on the current art, "
                         "with context) to /tmp/hs_sheets/<room>.png. A placement pass is not done "
                         "until someone has looked: the localiser is reliable on framed architecture "
                         "and large near objects, and unreliable on a small object on a support (it "
                         "boxes the tripod, not the spyglass) and on a path across open ground.")
    ap.add_argument("--commit-boxes", action="store_true",
                    help="write onto the COMMITTED hotspots (and mirror to plannedHotspots) instead of "
                         "drafting onto plannedHotspots only. Never overwrites a box tagged "
                         "review:lucas. Use when a scenario committed stub/boxless hotspots.")
    a = ap.parse_args()
    base = os.path.join(ROOMS, a.chapter, a.scenario)
    doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    rooms = (a.rooms.split(",") if a.rooms else
             [r["key"] for r in doc.get("rooms", []) if r.get("panorama")])

    total, failed = 0, []
    for room in rooms:
        try:
            spec, pred = localize_room(base, room, a.engine)
        except Exception as e:  # noqa: BLE001
            print("%-12s LOCALIZE FAILED — %s" % (room, str(e)[:160]))
            failed.append(room)
            continue
        rstat = None
        if a.refine:
            pred, rstat = refine_pred(base, room, spec, pred, _key_env())
        bad, cluster = collapsed(pred)
        if bad:
            print("%-12s COLLAPSED — %d elements share one box (%s); NOT written"
                  % (room, len(cluster), ", ".join(cluster[:4])))
            failed.append(room)
            continue
        if a.motion:
            mv = write_motion_boxes(base, room, spec, pred, a.dry_run)
            if mv:
                print("%-12s motion subject box%s: %s" % (room, "" if len(mv) == 1 else "es",
                                                          ", ".join(mv)))
        if a.commit_boxes:
            n, notes = apply_room_committed(base, room, spec, pred, a.dry_run)
        else:
            n, notes = apply_room(base, a.chapter, a.scenario, room, spec, pred, a.dry_run)
        total += n
        if a.sheet and not a.dry_run:
            try:
                sheet = contact_sheet(base, room)
                if sheet:
                    notes.append("sheet: %s" % sheet)
            except Exception as e:  # noqa: BLE001 — a missing Pillow must not lose the placement
                notes.append("sheet failed: %s" % str(e)[:60])
        rtxt = ("  [refined %d, kept %d, floored %d]"
                % (rstat["refined"], rstat["kept"], rstat["floored"])) if rstat else ""
        print("%-12s %d box(es)%s%s%s" % (room, n, rtxt, "  [dry-run]" if a.dry_run else "",
                                          ("  | " + "; ".join(notes[:2])) if notes else ""))
    print("\n%d draft boxes written across %d rooms%s"
          % (total, len(rooms) - len(failed), ("; FAILED: " + ", ".join(failed)) if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
