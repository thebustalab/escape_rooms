#!/usr/bin/env python3
"""
validate_scenes.py — the MECHANICAL half of the pre-art scene check (stdlib only).

Run this BEFORE generating any art, alongside the `escape_room_scene_validator` skill. The split is
deliberate:

  * THIS SCRIPT owns everything decidable from the data alone — a role that maps to an engine type
    nothing handles, a missing label, a gateless room whose forward door can never open, a variant with
    no carrier or no dial to fire it, an animatable parked on the wrap seam. These fail SILENTLY: the art
    generates, the boxes place, the harness reports success, and the break only surfaces when a student
    clicks the thing. They must not depend on anyone remembering to look.
  * THE SKILL owns the judgement — does the prompt actually depict what the map says, is the ship in the
    lighthouse view recognisably the *same* ship, does the light arc read as one day.

Checks (all against each room's `authoring.sceneSpec`; rooms without one are skipped):

  ROLE → ENGINE TYPE
    - a `switch` role: the player engine has NO `switch` handler, so the hotspot is inert — use `dial`
    - a `lock` whose planned content is grid-shaped (items/buckets/answer) — `openLock` != `openGrid`
    - a role that emits a type the engine never dispatches on
    - (built rooms) the spec role and the COMMITTED hotspot type disagree — the spec has drifted, so a
      re-generation would recreate the wrong mechanic
  LABELS
    - every gameplay element carries an explicit `label` (it is the play-time modal title AND the key
      pre-art `plannedHotspots` content slug-matches on when it attaches at commit)
    - no two elements in a room share a label slug (content would attach to the wrong box)
  DOORS / TOPOLOGY
    - every door names a `to` that exists
    - a GATELESS room (no puzzle/lock/grid) must not carry a `forward` door — it gates on a primary
      gate that does not exist, so it is locked forever
    - every non-start room has a `back` door (a missed opt-in pickup must stay retrievable) — a monorail
      SWITCH-DOOR counts, since its target flips with the lever
    - every room is reachable from the first room
  VARIANTS
    - a declared variant needs a CARRIER: its element must have a role, or it gets no hotspot to hang on
    - a variant `when` of the form {eq:[key, val]} must match a `dial` in the SAME room that sets that key
    - every variant declares a `reveal` (else no art is ever queued for it)
  ANIMATION / SEAM
    - `seam` is set on every room
    - an `animate` element is not parked at the extreme wrap edges (needs a hand-drawn wrap box)
    - `animate.loop` is boomerang|crossfade and `animate.motion` is non-empty
    - no two elements collide on the same approximate x position
  MISC
    - every element has `id`, `at`, `desc`; the scenario has a cover prompt

Usage:
    python3 authoring_v2/validate_scenes.py                    # every scenario
    python3 authoring_v2/validate_scenes.py wrangling/egypt    # just one

Exit 0 if nothing FAILS (warnings never gate). A `ready` scenario's warnings are printed loudly.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOMS = os.path.join(os.path.dirname(HERE), "rooms")
sys.path.insert(0, HERE)
import scene_spec  # noqa: E402  (sibling module; no side effects on import)

# Hotspot types the runtime player actually dispatches on (shared/pano-player.js `onHotspot`).
# `switch` is deliberately absent — that is the whole point of the check.
ENGINE_TYPES = {"puzzle", "clue", "door", "lock", "grid", "dial", "mapview", "ambient"}
GAMEPLAY = {"puzzle", "clue", "door", "lock", "grid", "dial", "switch", "mapview"}
LOOPS = {"boomerang", "crossfade"}
EDGE_X = (0.08, 0.92)   # the far-left / far-right slots — the ±180° wrap seam


def slug(s):
    return (re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_") or "obj")


def check_scenario(path):
    doc = json.load(open(path, encoding="utf-8"))
    fails, warns = [], []
    rooms = [r for r in doc.get("rooms", []) if isinstance(r, dict)]
    spec_rooms = [r for r in rooms if (r.get("authoring") or {}).get("sceneSpec")]
    if not spec_rooms:
        return fails, warns, doc.get("status") == "ready", True   # nothing spec'd yet — nothing to check

    keys = {r.get("key") for r in rooms}
    start = rooms[0].get("key") if rooms else None
    adj, doors_by_room, switch_door_back = {}, {}, {}

    for r in spec_rooms:
        rk = r.get("key")
        spec = r["authoring"]["sceneSpec"]
        els = spec.get("elements") or []
        hotspots = {h["id"]: h for h in scene_spec.to_hotspots(spec)}
        boxes = scene_spec.approx_boxes(spec)
        # A room's PRIMARY GATE is its first puzzle, else its first lock/grid (pano-player `primaryGate`),
        # so an escape room whose only gate is a keypad still has one — a `forward` door there is fine.
        has_gate = any(e.get("puzzle") or e.get("lock") or e.get("grid") for e in els)
        dials = {e.get("dial") and (e.get("key") or e["id"]) for e in els if e.get("dial")}
        # a dial's world-state key is authored in plannedHotspots (the spec carries only the role)
        planned = {slug(h.get("label")): h for h in (r.get("plannedHotspots") or []) if isinstance(h, dict)}
        committed = {h.get("id"): h for h in (r.get("hotspots") or []) if isinstance(h, dict) and h.get("id")}
        dial_keys = {h.get("key") for h in planned.values() if h.get("type") == "dial" and h.get("key")}

        if not str(spec.get("seam") or "").strip():
            warns.append(f"{rk}: no `seam` set — the L/R wrap has no named backdrop to join on")

        seen_slugs, seen_x = {}, {}
        for e in els:
            eid = e.get("id") or "?"
            for f in ("id", "at", "desc"):
                if not str(e.get(f) or "").strip():
                    fails.append(f"{rk}/{eid}: element has no `{f}`")
            h = hotspots.get(eid)
            typ = h.get("type") if h else None

            # ---- role -> engine type ----
            if typ == "switch":
                fails.append(f"{rk}/{eid}: role `switch` -> type 'switch', which the engine has NO handler "
                             f"for (inert hotspot) — use `dial:true` if the player turns it")
            elif typ and typ not in ENGINE_TYPES:
                fails.append(f"{rk}/{eid}: type '{typ}' is not dispatched by the engine")
            if typ == "lock":
                p = planned.get(slug(e.get("label") or e.get("desc", "")[:60]))
                if p and any(k in p for k in ("items", "buckets", "answer")):
                    fails.append(f"{rk}/{eid}: role `lock` but its content is GRID-shaped "
                                 f"(items/buckets/answer) — use `grid:true`, `openLock` can't render it")
            # Once a room is BUILT its committed hotspot is the truth — the spec having drifted from it means
            # a re-generation would silently recreate the wrong mechanic (trees' levers + vault gate, 2026-08).
            if typ and eid in committed and committed[eid].get("type") != typ:
                fails.append(f"{rk}/{eid}: spec role gives type '{typ}' but the COMMITTED hotspot is "
                             f"'{committed[eid].get('type')}' — the spec has drifted; a re-gen would "
                             f"recreate the wrong mechanic")

            # ---- labels ----
            if typ in GAMEPLAY and not str(e.get("label") or "").strip():
                warns.append(f"{rk}/{eid}: no explicit `label` — falls back to desc[:60], which becomes the "
                             f"player-facing modal title AND the key pre-art content attaches by")
            if typ:
                sl = slug(e.get("label") or e.get("desc", "")[:60])
                if sl in seen_slugs:
                    fails.append(f"{rk}/{eid}: label slug '{sl}' collides with {seen_slugs[sl]} — pre-art "
                                 f"content would attach to the wrong box")
                seen_slugs[sl] = eid

            # ---- animation / seam ----
            a = e.get("animate")
            if a:
                if not str(a.get("motion") or "").strip():
                    fails.append(f"{rk}/{eid}: `animate` with no motion")
                if a.get("loop") and a["loop"] not in LOOPS:
                    fails.append(f"{rk}/{eid}: animate.loop '{a['loop']}' not in {sorted(LOOPS)}")
                bx = boxes.get(eid)
                if bx:
                    cx = round((bx[0] + bx[2]) / 2, 2)
                    if cx in EDGE_X:
                        warns.append(f"{rk}/{eid}: animated object sits at the wrap edge (x={cx}) — a "
                                     f"seam-crossing cinemagraph needs a hand-drawn wrap box; move it inboard")
            # ---- x collisions ----
            bx = boxes.get(eid)
            if bx:
                cx = round((bx[0] + bx[2]) / 2, 3)
                if cx in seen_x:
                    warns.append(f"{rk}/{eid}: same approximate position (x={cx}) as {seen_x[cx]} — their "
                                 f"boxes will overlap; vary the `at` phrase")
                seen_x[cx] = eid

            # ---- variants ----
            for v in (e.get("variants") or []):
                if not isinstance(v, dict):
                    continue
                st = v.get("state") or "?"
                if not h:
                    fails.append(f"{rk}/{eid}: declares variant '{st}' but the element has NO role, so it "
                                 f"gets no hotspot to carry the art (give it `animate` for a marker-less one)")
                if not str(v.get("reveal") or "").strip():
                    warns.append(f"{rk}/{eid}: variant '{st}' has no `reveal` — no art will ever be queued")
                w = v.get("when")
                if isinstance(w, dict) and isinstance(w.get("eq"), list) and len(w["eq"]) == 2:
                    k = w["eq"][0]
                    if dial_keys and k not in dial_keys:
                        warns.append(f"{rk}/{eid}: variant '{st}' fires on '{k}', which no dial in this room "
                                     f"sets (room dials set {sorted(dial_keys)})")

            # ---- doors ----
            d = e.get("door")
            if isinstance(d, dict):
                to, direction = d.get("to"), d.get("direction", "forward")
                doors_by_room.setdefault(rk, []).append((to, direction))
                if to and to not in keys:
                    fails.append(f"{rk}/{eid}: door targets '{to}', which is not a room")
                if to:
                    adj.setdefault(rk, set()).add(to)
                views = d.get("opensOnto") or []
                cvars = (committed.get(eid) or {}).get("variants") or []
                if len(views) > 1 or any(v.get("direction") == "back" for v in cvars if isinstance(v, dict)):
                    switch_door_back[rk] = True
                if direction == "forward" and not has_gate:
                    fails.append(f"{rk}/{eid}: `forward` door in a room with NO gate (no puzzle/lock/grid) — "
                                 f"a forward door gates on the room's primary gate, so it can never open. "
                                 f"Use `open`.")

    # ---- topology across rooms ----
    for rk, ds in doors_by_room.items():
        # A switch-door (a door with >1 declared open-view, or a committed door carrying a `back` variant)
        # IS the way back — a monorail car's single door leads back or onward depending on the lever, so
        # such a room legitimately has no separate `back` door.
        if switch_door_back.get(rk):
            continue
        if rk != start and not any(direction == "back" for _, direction in ds):
            warns.append(f"{rk}: no `back` door — a missed opt-in pickup here could not be retrieved")
    if start:
        seen, stack = {start}, [start]
        while stack:
            n = stack.pop()
            for m in adj.get(n, ()):
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        for r in spec_rooms:
            if r.get("key") not in seen:
                fails.append(f"{r.get('key')}: not reachable from the start room '{start}'")

    if not str(doc.get("coverPrompt") or "").strip():
        warns.append("scenario has no coverPrompt")
    return fails, warns, doc.get("status") == "ready", False


def main():
    want = sys.argv[1:]
    any_bad = False
    for p in sorted(glob.glob(os.path.join(ROOMS, "*", "*", "scenario.json"))):
        rel = os.path.relpath(p, ROOMS).replace(os.sep + "scenario.json", "")
        if want and rel not in want:
            continue
        try:
            fails, warns, ready, skipped = check_scenario(p)
        except Exception as e:                                  # a malformed spec must not kill the sweep
            print(f"ERROR {rel}: {e}")
            any_bad = True
            continue
        if skipped:
            print(f"skip  {rel}  (no scene specs — pre-design)")
            continue
        if not fails and not warns:
            print(f"PASS  {rel}" + ("" if ready else "  (in-dev)"))
            continue
        tag = "" if ready else " (in-dev)"
        for f in fails:
            print(f"FAIL{tag}  {rel}: {f}")
        for w in warns:
            print(f"warn{tag}  {rel}: {w}")
        if fails:
            any_bad = True
    return 1 if any_bad else 0


if __name__ == "__main__":
    sys.exit(main())
