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
  LAYOUT
    - elements run in left→right sweep order (the prompt is rendered in FILE order, so an out-of-order
      spec describes the panorama as jumping backwards)
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
# Canonical left→right spatial phrases (SCENE_SPEC_GUIDE rule 1), in sweep order. Ranked by the same
# x the box mapper uses, so two phrases that resolve to one position (e.g. "just right of centre" and
# "to the centre-right", both 0.64) are treated as equal rather than as an ordering violation.
def _x_rank(at):
    return scene_spec._x_from_at(at)


ENGINE_TYPES = {"puzzle", "clue", "door", "lock", "grid", "ledger", "elevmap", "dial", "mapview", "ambient"}
GAMEPLAY = {"puzzle", "clue", "door", "lock", "grid", "ledger", "elevmap", "dial", "switch", "mapview"}
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
        has_gate = any(e.get("puzzle") or e.get("lock") or e.get("grid") or e.get("ledger") for e in els)   # elevmap is a TOOL, not a gate
        dials = {e.get("dial") and (e.get("key") or e["id"]) for e in els if e.get("dial")}
        # a dial's world-state key is authored in plannedHotspots (the spec carries only the role)
        planned = {slug(h.get("label")): h for h in (r.get("plannedHotspots") or []) if isinstance(h, dict)}
        committed = {h.get("id"): h for h in (r.get("hotspots") or []) if isinstance(h, dict) and h.get("id")}
        dial_keys = {h.get("key") for h in planned.values() if h.get("type") == "dial" and h.get("key")}

        # ---- PLANNED HOTSPOT WITH NO SPEC ELEMENT (added 2026-09-07) ----
        # `place_hotspots.py` matches a planned hotspot to a spec element BY LABEL SLUG. A planned entry
        # whose label matches nothing in the spec therefore gets NO BOX, silently — the run reports
        # "no spec element matched" in its log and carries on, and the room ends up short of hotspots
        # with every other check green. That is exactly how `networks/subway` lost every train door and
        # ten clues at once when its stations were split: the ART was always right, because the prompt
        # is derived from the spec elements; it was the separate hand-kept plannedHotspots list that
        # drifted. Cheap to check here, and it is the only place that compares the two lists.
        #
        # `noElement: true` on a planned hotspot is the honest opt-out, for something that is genuinely
        # not an object in the still (subway's ghost-station "sighting", live only during a ride).
        spec_labels = {slug(e.get("label")) for e in els if e.get("label")}
        for sl, h in planned.items():
            if not sl or h.get("noElement"):
                continue
            if sl in spec_labels:
                continue
            # Calibration matters here or the check is noise. On a room that is ALREADY BUILT the
            # planned list is largely historical — the boxes were placed long ago and live in
            # `hotspots` — so a stale planned entry is worth a word, not a gate. It is a FAIL only
            # where it can still do damage: a room whose art has not been committed yet, which is
            # exactly when place_hotspots is about to run and silently skip it.
            msg = (f"{rk}: plannedHotspot '{h.get('label')}' matches no spec element label — "
                   f"place_hotspots keys on the label, so this one gets NO BOX. Rename it to the "
                   f"element's label, add the element, or set noElement:true if it is deliberately "
                   f"not in the picture.")
            if r.get("built") or sl in {slug(c.get("label")) for c in committed.values()}:
                warns.append(msg)
            else:
                fails.append(msg)

        if not str(spec.get("seam") or "").strip():
            warns.append(f"{rk}: no `seam` set — the L/R wrap has no named backdrop to join on")

        # ---- left→right sweep order (rule 1) ----
        # `render_prompt` joins elements in FILE order, so a spec whose `at` phrases run out of sequence
        # emits a prompt that sweeps across the panorama and then jumps backwards. The boxes are fine
        # (those come from the phrase, not the order), so nothing downstream complains — the only symptom
        # is worse art. Pure reorder to fix; no content changes.
        placed = [e for e in els if _x_rank(e.get("at")) is not None]
        ranks = [_x_rank(e.get("at")) for e in placed]
        # Report each ADJACENT INVERSION as an ordered pair. Naming one side alone is ambiguous — either
        # element could be the one that moved — so say "A before B", which reads the same way the fix does.
        inversions = [f"{placed[i].get('id') or '?'} before {placed[i + 1].get('id') or '?'}"
                      for i in range(len(ranks) - 1) if ranks[i] > ranks[i + 1]]
        if inversions:
            warns.append(f"{rk}: elements are not in left→right order ({'; '.join(inversions)}) — "
                         f"`render_prompt` joins them in file order, so the prompt sweeps backwards; "
                         f"reorder to match their own `at` phrases")

        seen_slugs, seen_x = {}, {}
        for e in els:
            eid = e.get("id") or "?"
            for f in ("id", "at", "desc"):
                if not str(e.get(f) or "").strip():
                    fails.append(f"{rk}/{eid}: element has no `{f}`")

            # ---- SHAPE of the art-job fields ----------------------------------------------------------
            # These feed cinemagraph_jobs / dooropen_jobs / variant_jobs. A field written with the wrong
            # SHAPE (2026-08-07: `opensOnto` authored as a bare reveal string instead of a list of
            # {state,reveal}) used to sail through this validator and then crash `_scenario_state` with a
            # bare "'str' object has no attribute 'get'" — naming neither the room nor the field, so the
            # whole scenario simply refused to load in the harness. The builders now skip a malformed
            # entry rather than raising; this says WHICH element is wrong so it gets fixed rather than
            # silently dropping its art.
            if "animate" in e and not isinstance(e.get("animate"), dict):
                fails.append(f"{rk}/{eid}: `animate` must be an object {{motion, loop}}, got "
                             f"{type(e.get('animate')).__name__} — its cinemagraph would be skipped")
            if "variants" in e and not isinstance(e.get("variants"), list):
                fails.append(f"{rk}/{eid}: `variants` must be a LIST of {{state, when?, reveal}}, got "
                             f"{type(e.get('variants')).__name__}")
            _d = e.get("door")
            if isinstance(_d, dict) and "opensOnto" in _d and not isinstance(_d.get("opensOnto"), list):
                fails.append(f"{rk}/{eid}: `door.opensOnto` must be a LIST of {{state, when?, reveal}}, got "
                             f"{type(_d.get('opensOnto')).__name__} — its open-door art would be skipped")
            h = hotspots.get(eid)
            typ = h.get("type") if h else None

            # ---- role -> engine type ----
            if typ == "switch":
                fails.append(f"{rk}/{eid}: role `switch` -> type 'switch', which the engine has NO handler "
                             f"for (inert hotspot) — use `dial:true` if the player turns it")
            elif typ and typ not in ENGINE_TYPES:
                fails.append(f"{rk}/{eid}: type '{typ}' is not dispatched by the engine")
            if typ == "lock":
                # `answer` is NOT a grid tell — it is the lock's OWN core field (`answer`, `length`,
                # `feedback`), so listing it here failed every correctly-wired lock the moment its answer
                # was mirrored onto plannedHotspots, which the wiring skill requires. It only stayed
                # hidden because canyon is the first scenario to have BOTH a spec `lock` role and a
                # planned answer. What actually distinguishes the two mechanics is the SHAPE: a grid's
                # answer maps items to buckets (a dict/list), a lock's is a scalar code.
                p = planned.get(slug(e.get("label") or e.get("desc", "")[:60]))
                gridish = p and (any(k in p for k in ("items", "buckets"))
                                 or isinstance(p.get("answer"), (dict, list)))
                if gridish:
                    fails.append(f"{rk}/{eid}: role `lock` but its content is GRID-shaped "
                                 f"(items/buckets, or a non-scalar answer) — use `grid:true`, "
                                 f"`openLock` can't render it")
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
            if isinstance(a, dict):     # a non-dict is already reported above; don't crash reading it
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
            # ---- x collisions, ONLY between elements that actually need a box ----
            # `approx_boxes` gives EVERY element a box, including pure backdrop, so warning on any shared
            # x flagged 35% of all authored rooms — most of them two bits of scenery that will never carry
            # a hotspot or a crop, and none of which can conflict with anything. That noise pushes authors
            # to invent an eighth position (there are only seven — see SCENE_SPEC_GUIDE rule 1) or to split
            # a room's ring for no reason. A box is only contended if BOTH sides need one: a gameplay role
            # (it becomes a real hotspot) or `animate` (it becomes a measured motion subject). Scenery may
            # share a position freely. (2026-09-03)
            needs_box = bool(typ) or bool(e.get("animate"))
            bx = boxes.get(eid)
            if bx and needs_box:
                cx = round((bx[0] + bx[2]) / 2, 3)
                if cx in seen_x:
                    warns.append(f"{rk}/{eid}: same approximate position (x={cx}) as {seen_x[cx]} — both "
                                 f"need a box (hotspot or animate), so they will overlap; vary the `at` phrase")
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
                # A MULTI-VIEW DOOR'S ALTERNATE DESTINATIONS ARE REAL EDGES (2026-09-06).
                # `to` names only the door's default target, so on a MESH network (networks/subway: five
                # line-cars, each of which alights at two or three different stations) every station that
                # is not some car's default read as UNREACHABLE. A view whose `state` — or explicit `to` —
                # names a real room is a destination that door can actually deliver you to, so it counts.
                # Conservative by construction: a state that is not a room key (trees' "open",
                # "to_station1") adds nothing, so no existing scenario's graph changes.
                for _v in views:
                    if not isinstance(_v, dict):
                        continue
                    _t = _v.get("to") or _v.get("state")
                    if _t in keys:
                        adj.setdefault(rk, set()).add(_t)
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
