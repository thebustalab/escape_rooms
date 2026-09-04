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
            if h.get("boxSource") == "review:lucas":
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
        if a.commit_boxes:
            n, notes = apply_room_committed(base, room, spec, pred, a.dry_run)
        else:
            n, notes = apply_room(base, a.chapter, a.scenario, room, spec, pred, a.dry_run)
        total += n
        rtxt = ("  [refined %d, kept %d, floored %d]"
                % (rstat["refined"], rstat["kept"], rstat["floored"])) if rstat else ""
        print("%-12s %d box(es)%s%s%s" % (room, n, rtxt, "  [dry-run]" if a.dry_run else "",
                                          ("  | " + "; ".join(notes[:2])) if notes else ""))
    print("\n%d draft boxes written across %d rooms%s"
          % (total, len(rooms) - len(failed), ("; FAILED: " + ", ".join(failed)) if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
