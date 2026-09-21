#!/usr/bin/env python3
"""
wire_maze.py — make scenario.json ENFORCE Lucas's hand-authored water puzzle, generated from the router.

WHY THIS EXISTS (2026-09-20). Lucas authored the descent by hand in `puzzle.json`: five water states,
the lever sequence S1 -> S2 -> S3 -> S4 -> re-S3, and a layout in which the basin is ONLY reachable once
the boss's wheel (S4) has been thrown. `router.py` reproduces all five of his states. So the design was
always sound. What was missing was the WIRING: every door in `scenario.json` was an ordinary
forward/back door gated on the room's PUZZLE, with no idea there was water on it. An audit found the
consequence — as wired, a student could walk station1 -> station2 -> basin and skip the boss entirely,
because the door onto the flooded ladder opened as soon as station2's analysis was solved.

The fix is not to hand-patch that one door. It is to derive EVERY door's gate from the same router that
reproduces Lucas's puzzle, so the scenario cannot drift from it:

  * each diverter lever is a `dial` writing a world-state key (`d1`..`d4`, "shut" | "thrown");
  * each lever is gated on its OWN room's analysis being solved (the design record: "solving a ledge's
    analysis is what unlocks that ledge's diverter") — the puzzles gate the LEVERS, never the doors;
  * each door is gated on its span being DRY: `availableWhen` = the set of lever configurations in which
    the router leaves that bridge uncut, minimised to a readable condition;
  * a gated door must be `direction: "open"`. The engine's `handleDoor` short-circuits `back` doors
    (they navigate before `doorIsOpen` is ever consulted), so a `back` door would walk straight up a
    flooded ladder. A span the water NEVER covers may keep its authored direction.

Then it PROVES the result by re-exploring the wired game — the scenario's own conditions, not the
router — and asserting the properties the puzzle exists for (see `prove()`).

Run: python3 wire_maze.py            # dry run: prints the plan + the proof, writes nothing
     python3 wire_maze.py --write    # applies it to ../scenario.json (timestamped backup first)
"""
import collections
import itertools
import json
import os
import shutil
import sys
import time

from router import DIVORDER, diverter_events, present_bridges, cuts_for
import reach_art as ra

HERE = os.path.dirname(os.path.abspath(__file__))
SCEN = os.path.join(HERE, "..", "scenario.json")
PJSON = os.path.join(HERE, "..", "puzzle.json")

ROOM_AT = {"catwalk": (0, 0), "station1": (1, 0), "station3": (1, 1), "boss": (1, 2),
           "station2": (2, 0), "spillway": (2, 1), "basin": (3, 0), "sump": (3, 1)}
LEVER_ROOM = {"station1": "d1", "station2": "d2", "station3": "d3", "boss": "d4"}   # Sx throws Dx
KEYS = ["d1", "d2", "d3", "d4"]                                                         # == DIVORDER
VAL = {0: "shut", 1: "thrown"}
LOCKED_WATER = ("Water is pouring straight across it. Nothing crosses while it runs — the stream has to "
                "be sent somewhere else first.")


def bridge_between(a, b):
    """The span joining two orthogonally adjacent platforms, in the router's naming, or None."""
    (r1, c1), (r2, c2) = a, b
    if r1 == r2 and abs(c1 - c2) == 1:
        return "H-%d-%d" % (r1, min(c1, c2))
    if c1 == c2 and abs(r1 - r2) == 1:
        return "V-%d-%d" % (min(r1, r2), c1)
    return None


def all_configs():
    return list(itertools.product((0, 1), repeat=len(DIVORDER)))


def dry_configs(bid, present, divs):
    return {b for b in all_configs() if bid not in cuts_for(ra.SOURCES, b, present, divs)}


def minimise(true_set):
    """Smallest-ish cover of `true_set` by cubes over 4 boolean vars (greedy set cover over every
    implicant). Returns a list of cubes; each cube is a tuple of 0 / 1 / None (don't care)."""
    cubes = []
    for cube in itertools.product((0, 1, None), repeat=len(DIVORDER)):
        members = {b for b in all_configs()
                   if all(c is None or c == bb for c, bb in zip(cube, b))}
        if members and members <= true_set:
            cubes.append((cube, members))
    left, chosen = set(true_set), []
    while left:
        cube, members = max(cubes, key=lambda cm: (len(cm[1] & left), -sum(c is not None for c in cm[0])))
        chosen.append(cube)
        left -= members
    return chosen


def cond_for(true_set):
    """The engine condition (shared/cond.js grammar) that holds exactly on `true_set`."""
    if len(true_set) == 2 ** len(DIVORDER):
        return None                                      # always dry: no gate at all
    terms = []
    for cube in minimise(true_set):
        clause = [{"eq": [KEYS[i], VAL[v]]} for i, v in enumerate(cube) if v is not None]
        terms.append(clause[0] if len(clause) == 1 else {"all": clause})
    return terms[0] if len(terms) == 1 else {"any": terms}


def holds(cond, state):
    """Evaluate a condition exactly as shared/cond.js does, for the proof below."""
    if cond is None or cond is True:
        return True
    if "eq" in cond:
        return str(state.get(cond["eq"][0])) == str(cond["eq"][1])
    if "all" in cond:
        return all(holds(c, state) for c in cond["all"])
    if "any" in cond:
        return any(holds(c, state) for c in cond["any"])
    if "solved" in cond:
        return cond["solved"] in state.get("__solved", ())
    raise ValueError("unhandled condition %r" % cond)


def plan():
    pj = json.load(open(PJSON, encoding="utf-8"))
    present = present_bridges(set(pj["absentBridges"]))
    divs = diverter_events()
    doc = json.load(open(SCEN, encoding="utf-8"))
    out = {}
    for r in doc["rooms"]:
        rk = r["key"]
        for e in r["authoring"]["sceneSpec"]["elements"]:
            door = e.get("door")
            if not door or not door.get("to"):
                continue
            bid = bridge_between(ROOM_AT[rk], ROOM_AT[door["to"]])
            if bid is None:
                raise SystemExit("%s/%s -> %s: rooms are not adjacent on the grid" % (rk, e["id"], door["to"]))
            if bid not in present:
                raise SystemExit("%s/%s: span %s does not exist in puzzle.json" % (rk, e["id"], bid))
            dry = dry_configs(bid, present, divs)
            if not dry:
                raise SystemExit("%s/%s: span %s is NEVER dry — the door could never open" % (rk, e["id"], bid))
            cond = cond_for(dry)
            out[(rk, e["id"])] = dict(label=e.get("label"), to=door["to"], bridge=bid,
                                      authored=door.get("direction"), cond=cond,
                                      direction="open" if cond is not None else
                                      ("open" if door.get("direction") == "forward" else door.get("direction")),
                                      dry=len(dry))
    return doc, out


def prove(doc, doors):
    """Re-explore the WIRED game — these conditions, not the router — and assert what the puzzle is for."""
    solved_puzzles = {"station1", "station2", "station3", "boss"}     # analyses the player can solve
    start = ("catwalk", ("shut",) * 4, frozenset())
    by_room = collections.defaultdict(list)
    for (rk, _), d in doors.items():
        by_room[rk].append(d)
    seen, q = {start}, collections.deque([start])
    while q:
        room, levers, solved = q.popleft()
        state = dict(zip(KEYS, levers))
        state["__solved"] = solved
        nxt = []
        if room in solved_puzzles and room not in solved:            # solve this room's analysis
            nxt.append((room, levers, solved | {room}))
        if room in LEVER_ROOM and room in solved:                    # throw its lever (gated on the solve)
            i = KEYS.index(LEVER_ROOM[room])
            flipped = list(levers)
            flipped[i] = "thrown" if levers[i] == "shut" else "shut"
            nxt.append((room, tuple(flipped), solved))
        for d in by_room[room]:                                      # walk through a dry span
            if holds(d["cond"], state):
                nxt.append((d["to"], levers, solved))
        for s in nxt:
            if s not in seen:
                seen.add(s)
                q.append(s)

    fails = []
    at_basin = [s for s in seen if s[0] == "basin"]
    if not at_basin:
        fails.append("the basin is UNREACHABLE in the wired game")
    if any("boss" not in s[2] for s in at_basin):
        fails.append("the basin is reachable WITHOUT solving the boss")
    if any(s[1][3] != "thrown" for s in at_basin):
        fails.append("the basin is reachable without the boss's wheel (S4) thrown")
    basin_cfgs = {s[1] for s in at_basin}
    rooms_reached = {s[0] for s in seen}
    missing = set(ROOM_AT) - rooms_reached
    if missing:
        fails.append("rooms never reachable: %s" % sorted(missing))

    # NO PERMANENT TRAPS. Water-gated returns have to be `open` doors (a `back` door ignores its gate), so
    # `validate_scenes.py` warns that these rooms have "no back door — a missed pickup could not be
    # retrieved". That warning's CONCERN is real and this is the answer to it: from EVERY reachable state,
    # every room must still be reachable. A room you cannot currently leave is the puzzle; a room you can
    # NEVER leave is a bug. (Checked 2026-09-20: 0 trapped states of 94.)
    def closure(s0):
        got, qq = {s0}, collections.deque([s0])
        while qq:
            cur = qq.popleft()
            for n in _step(cur, by_room, solved_puzzles):
                if n not in got:
                    got.add(n)
                    qq.append(n)
        return {x[0] for x in got}
    trapped = [s for s in seen if closure(s) != set(ROOM_AT)]
    if trapped:
        fails.append("%d reachable state(s) from which some room can NEVER again be reached, e.g. %s"
                     % (len(trapped), trapped[0][:2]))
    return fails, basin_cfgs, len(seen)


def _step(state, by_room, solved_puzzles):
    room, levers, solved = state
    st = dict(zip(KEYS, levers))
    st["__solved"] = solved
    out = []
    if room in solved_puzzles and room not in solved:
        out.append((room, levers, solved | {room}))
    if room in LEVER_ROOM and room in solved:
        i = KEYS.index(LEVER_ROOM[room])
        flipped = list(levers)
        flipped[i] = "thrown" if levers[i] == "shut" else "shut"
        out.append((room, tuple(flipped), solved))
    for d in by_room[room]:
        if holds(d["cond"], st):
            out.append((d["to"], levers, solved))
    return out


def apply(doc, doors):
    rooms = {r["key"]: r for r in doc["rooms"]}
    for (rk, eid), d in doors.items():
        spec_el = next(e for e in rooms[rk]["authoring"]["sceneSpec"]["elements"] if e["id"] == eid)
        spec_el["door"]["direction"] = d["direction"]
        for h in rooms[rk].get("plannedHotspots", []):
            if h.get("type") == "door" and h.get("label") == d["label"]:
                h["to"] = d["to"]
                h["direction"] = d["direction"]
                if d["cond"] is not None:
                    h["availableWhen"] = d["cond"]
                    h["lockedBody"] = LOCKED_WATER
                else:
                    h.pop("availableWhen", None)
                    h.pop("lockedBody", None)
                h["_waterGate"] = ("generated by cave_engine/wire_maze.py from span %s (dry in %d of 16 "
                                   "lever configurations) — regenerate, do not hand-edit" % (d["bridge"], d["dry"]))
    for rk, key in LEVER_ROOM.items():
        for h in rooms[rk].get("plannedHotspots", []):
            if h.get("type") == "dial":
                n = key[1]
                h["key"] = key
                h["states"] = [{"value": "shut", "label": "Leave the S%s gate shut" % n},
                               {"value": "thrown", "label": "Throw the S%s gate" % n}]
                h["availableWhen"] = {"solved": rk}
                h["lockedBody"] = ("The lever will not move. Whatever holds it is waiting on the reading "
                                   "at this landing's console.")
                h["hint"] = "Throw it, and somewhere below the water changes its course."
    st = doc.setdefault("state", {})
    for k in KEYS:
        st[k] = "shut"                                               # every lever starts shut (puzzle.json state 1)
    return doc


def main():
    doc, doors = plan()
    print("DOOR PLAN (each door's gate = the lever configurations in which its span is DRY)\n")
    for (rk, eid), d in sorted(doors.items()):
        print("  %-9s %-14s -> %-9s %-6s dry %2d/16  %-7s->%-5s  %s" % (
            rk, eid, d["to"], d["bridge"], d["dry"], d["authored"], d["direction"],
            "always open" if d["cond"] is None else json.dumps(d["cond"])))
    applied = apply(json.loads(json.dumps(doc)), doors)
    fails, basin_cfgs, n = prove(applied, doors)
    print("\nPROOF over the WIRED game (%d reachable states):" % n)
    print("  basin reachable under lever settings:", sorted(basin_cfgs))
    for f in fails:
        print("  FAIL  " + f)
    if not fails:
        print("  ok    the basin is reachable, never without the boss solved and its wheel thrown, and "
              "every room can be reached")
        print("  ok    no permanent traps: from every reachable state, every room can still be reached")
    if "--write" in sys.argv:
        if fails:
            print("\nREFUSING to write: the wired game breaks the puzzle.")
            return 1
        shutil.copy2(SCEN, SCEN + ".bak_%s_wire_maze" % time.strftime("%Y%m%d_%H%M%S"))
        json.dump(applied, open(SCEN, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("\nwrote", os.path.relpath(SCEN, HERE))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
