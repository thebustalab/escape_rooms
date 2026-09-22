#!/usr/bin/env python3
"""
basin_sort.py — WHERE THE WATER ENDS UP, per diverter configuration.

WHY THIS EXISTS (Lucas, 2026-09-20). The router answers "which spans does the water CUT", which is
the navigation question. It never answered "which basin does each stream END in", which is the
question the escape now turns on: the pair of streams falls into a different grouping of basins
depending on how the engine is set, and the student has to attribute each grouping to its setting.

That is `k` is a property of the question you asked, stated in stone and water instead of in a
debrief paragraph — and it needs NO new physics. The lane a stream ends in already falls out of the
router's own shift model; nobody had asked it for the final lane before.

THE MODEL, in one line: run each source lane through every diverter in height order, applying the
same `SHIFT[label][bit]` the router applies, and read off the lane it leaves the bottom in. Streams
sharing a final lane fall into the same basin; that is the grouping.

EVERY STREAM LANDS IN A BASIN — Lucas's ruling, 2026-09-20. The reachable configurations put water
into lanes -1, 0 and 1, and lane -1 is OUTSIDE the 3-column grid the platforms live on. It is not
"it pours away into the dark": the floor carries a basin for every lane the engine can reach,
including the outlying one, so the sort is always fully visible and countable. `FLOOR_LANES` below
is that set, computed rather than assumed, and it is the contract the basin ART owes.

Run: python3 basin_sort.py
"""
import collections
import json
import os

from router import DIVORDER, SHIFT, diverter_events, present_bridges, cuts_for
import reach_art as ra

HERE = os.path.dirname(os.path.abspath(__file__))
PJSON = os.path.join(HERE, "..", "puzzle.json")
BASIN = (3, 0)          # the escape room's platform — `reach_art`'s EXIT
START = (0, 0)          # catwalk


def final_lane(src_lane, bits):
    """The lane a stream launched in `src_lane` leaves the bottom of the shaft in.

    Same shift model as `router.route_stream` — a diverter standing in the stream's current lane
    moves it sideways by `SHIFT[label][bit]` columns — but we keep only the destination, not the
    spans crossed on the way.
    """
    lane = src_lane
    for y, ln, lbl in sorted(diverter_events(), key=lambda e: e[0]):
        if ln == lane:
            lane += SHIFT[lbl][bits[DIVORDER.index(lbl)]]
    return lane


def sort_at_basin(bits):
    """The grouping the floor shows for this configuration: {lane: [stream ids]}, lanes ascending."""
    out = collections.defaultdict(list)
    for i, src in enumerate(ra.SOURCES):
        out[final_lane(src, bits)].append(i)
    return dict(sorted(out.items()))


def pattern_key(bits):
    """A stable, art-facing name for a grouping — the lanes that RUN, in order (e.g. '-1+1')."""
    return "|".join(str(k) for k in sort_at_basin(bits))


def reachable_states():
    """Every (platform, config) the player can actually reach — `reach_art`'s exploration, reused."""
    pj = json.load(open(PJSON, encoding="utf-8"))
    present = present_bridges(set(pj["absentBridges"]))
    divs = diverter_events()
    seen, q = set(), collections.deque([(START, (0,) * len(DIVORDER))])
    while q:
        pos, bits = q.popleft()
        if (pos, bits) in seen:
            continue
        seen.add((pos, bits))
        passable = present - cuts_for(ra.SOURCES, bits, present, divs)
        for nb in ra.neighbors(pos, passable):
            q.append((nb, bits))
        if pos in ra.SWITCHES:
            lbl, idx = ra.SWITCHES[pos]
            flipped = list(bits)
            flipped[idx] = 1 - flipped[idx]
            q.append((pos, tuple(flipped)))
    return seen


def main():
    seen = reachable_states()
    all_configs = sorted({b for _, b in seen})
    at_basin = sorted({b for p, b in seen if p == BASIN})

    floor_lanes = sorted({lane for b in all_configs for lane in sort_at_basin(b)})
    print("FLOOR_LANES (every lane the engine can put water in, across all reachable configs):",
          floor_lanes)
    print("  -> the basin art must carry one basin per lane above. Lane -1 sits OUTSIDE the "
          "3-column platform grid and is still a basin (Lucas, 2026-09-20): nothing pours away "
          "into the dark.\n")

    print(f"configurations reachable WHILE STANDING IN THE BASIN: {len(at_basin)}")
    groups = collections.defaultdict(list)
    for bits in at_basin:
        groups[pattern_key(bits)].append(bits)
    for pat, cfgs in sorted(groups.items()):
        sort = sort_at_basin(cfgs[0])
        k = len(sort)
        print(f"  pattern {pat:8}  k={k}  basins running: "
              f"{ {lane: len(v) for lane, v in sort.items()} }")
        for b in cfgs:
            thrown = [DIVORDER[i] for i, v in enumerate(b) if v] or ["none"]
            print(f"      config {b}  (thrown: {', '.join(thrown)})")

    print(f"\ndistinct patterns visible from the basin: {len(groups)}")
    print("PLAY CONSEQUENCE: two different settings can produce the SAME sort — that is a feature, "
          "and the escape grid must allow two items to share one bucket.")

    # --- invariants the design leans on; assert them so a puzzle.json edit cannot quietly break it ---
    fails = []
    if len(groups) < 3:
        fails.append("fewer than 3 distinct basin patterns — the grid collapses")
    if not any(len(sort_at_basin(b)) == 1 for b in at_basin):
        fails.append("no configuration gathers both streams into ONE basin (k=1 case missing)")
    if not any(len(sort_at_basin(b)) > 1 for b in at_basin):
        fails.append("no configuration splits the streams (k>1 case missing)")
    ks = {len(sort_at_basin(b)) for b in at_basin}
    if len(ks) < 2:
        fails.append("k does not vary across reachable basin configs — the whole lesson is gone")
    pats_same_k = collections.defaultdict(set)
    for b in at_basin:
        pats_same_k[len(sort_at_basin(b))].add(pattern_key(b))
    if not any(len(v) > 1 for v in pats_same_k.values()):
        fails.append("no two patterns share a k — the grid would be solvable by COUNTING alone, "
                     "without reading which basins run")

    # STRONG CONNECTIVITY among the basin configurations. The escape asks the player to go up, re-throw a
    # lever, come back down and look — so every basin configuration must be reachable FROM every other.
    # `reachable_states()` only explores from the start, which does not prove this (audit, 2026-09-20).
    succ = _successors()
    for b in at_basin:
        got = _closure((BASIN, b), succ)
        back = {bb for p, bb in got if p == BASIN}
        if back != set(at_basin):
            fails.append("from basin config %s the player cannot return to %s" %
                         (b, sorted(set(at_basin) - back)))

    # THE ROOMLESS CELLS stay sealed. The grid is 4x3 = 12 cells but only 8 are rooms; spans run toward
    # the other 4. Unreachable today — but H-2-1 is DRY in four configurations and (2,2) stays shut only
    # because none of those four is occupiable from the spillway. True now, fragile under any edit to
    # puzzle.json, and nothing asserted it until this line (audit, 2026-09-20).
    roomless = {(r, c) for r in range(4) for c in range(3)} - set(ROOM_CELLS)
    leaked = sorted({p for p, _ in seen} & roomless)
    if leaked:
        fails.append("the player can reach a cell with NO ROOM in it: %s" % leaked)

    # TWO STREAMS, NOT THREE — pinned. `router.py`'s calibration matches Lucas's five authored states with
    # THREE source lanes (-1, 0, 1), but the lane -1 stream meets no diverter and cuts no span in any of the
    # 16 configurations: it is mechanically inert, which is why `reach_art` runs on two and why Lucas
    # remembered "the third wasn't necessary". It is NOT inert at the floor, though. Drawn, it would fall
    # straight into the OUTER basin in every setting and change every sort — and it would make the
    # "all three, one each" decoy a REAL answer for S1 thrown / S2 shut. So the world has two streams, the
    # basin art says "exactly 2 threads", and this line fails if anyone quietly restores the third.
    # Restoring it is a legitimate design choice, but then build_grid() and DECOYS must be redone with it.
    if tuple(ra.SOURCES) != (0, 1):
        fails.append("live streams are %s, not (0, 1): the third stream is back — the sorts, the grid, the "
                     "decoys and the basin art ('exactly 2 threads') all assume two" % (ra.SOURCES,))

    # THE DECOY BUCKETS must be genuinely unreachable, or the grid has two right answers for some row.
    for key, why in DECOYS.items():
        if any(_decoy_matches(key, b) for b in at_basin):
            fails.append("decoy bucket '%s' is actually produced by a reachable setting (%s)" % (key, why))

    print("\nINVARIANTS")
    for f in fails:
        print("  FAIL  " + f)
    if not fails:
        print("  ok    3+ patterns, k varies, a k=1 case exists, two patterns share a k (so counting "
              "alone does not solve the grid)")
        print("  ok    every basin configuration is reachable from every other (the look-again loop works)")
        print("  ok    no roomless cell is reachable")
        print("  ok    both decoy buckets are unreachable, so each row has exactly one right answer")
    return 1 if fails else 0


# ---- the rooms, the decoys, and the proof helpers ------------------------------------------------------

ROOM_CELLS = {(0, 0): "catwalk", (1, 0): "station1", (1, 1): "station3", (1, 2): "boss",
              (2, 0): "station2", (2, 1): "spillway", (3, 0): "basin", (3, 1): "sump"}

# Sorts the floor CAN NEVER show — offered on the grid as wrong answers so it cannot be brute-forced
# cheaply. An attempt cap is NOT an option: on an `endsEscape` grid the engine disables the card for good
# and `attemptCounts` persists with no re-arm, so a cap is a hard soft-lock (audit, 2026-09-20). Two
# unreachable buckets take the blind search from 3^4 = 81 assignments to 5^4 = 625, and every wrong
# answer they catch is DIAGNOSTIC: a student who picks one has not looked at the floor.
DECOYS = {
    "outer_middle": "the near basin is fed in EVERY reachable setting, so it can never stand dry",
    "all_three": "only two streams are live, so three basins can never run at once",
}


def _decoy_matches(key, bits):
    lanes = set(sort_at_basin(bits))
    if key == "outer_middle":
        return lanes == {-1, 0}
    if key == "all_three":
        return lanes == {-1, 0, 1}
    raise KeyError(key)


def _successors():
    pj = json.load(open(PJSON, encoding="utf-8"))
    present = present_bridges(set(pj["absentBridges"]))
    divs = diverter_events()

    def succ(state):
        pos, bits = state
        passable = present - cuts_for(ra.SOURCES, bits, present, divs)
        out = [(nb, bits) for nb in ra.neighbors(pos, passable)]
        if pos in ra.SWITCHES:
            _, idx = ra.SWITCHES[pos]
            flipped = list(bits)
            flipped[idx] = 1 - flipped[idx]
            out.append((pos, tuple(flipped)))
        return out
    return succ


def _closure(start, succ):
    seen, q = {start}, collections.deque([start])
    while q:
        for n in succ(q.popleft()):
            if n not in seen:
                seen.add(n)
                q.append(n)
    return seen


# ---- the escape grid, generated (never hand-typed) --------------------------------------------------

BASIN_NAME = {-1: "the outer basin", 0: "the middle basin", 1: "the near basin"}
BUCKETS = [
    ("outer_near", "The outer basin and the near basin, one thread into each", {-1, 1}),
    ("middle_near", "The middle basin and the near basin, one thread into each", {0, 1}),
    ("near_alone", "The near basin alone, both threads falling together", {1}),
    ("outer_middle", "The outer basin and the middle basin, one thread into each", {-1, 0}),
    ("all_three", "All three basins, one thread into each", {-1, 0, 1}),
]
LEVER_LABEL = {(0, 0): "S1 shut, S2 shut", (0, 1): "S1 shut, S2 thrown",
               (1, 0): "S1 thrown, S2 shut", (1, 1): "S1 thrown, S2 thrown"}


def build_grid():
    """The escape `grid` hotspot content, derived from the model. Items = the four settings of the two
    upper levers (every basin-reachable configuration has S3 shut and S4 thrown); buckets = the three
    real sorts plus the two unreachable decoys."""
    at_basin = sorted({b for p, b in reachable_states() if p == BASIN})
    items, answer = [], {}
    for bits in at_basin:
        key = "s%d%d" % (bits[0], bits[1])
        items.append({"key": key, "label": LEVER_LABEL[(bits[0], bits[1])]})
        lanes = set(sort_at_basin(bits))
        answer[key] = next(k for k, _, want in BUCKETS if want == lanes)
    return {
        "type": "grid",
        "label": "The reckoning frame",
        "prompt": ("<p>A brass frame stands against the vault: the settings of the two upper gates down one "
                   "side, the sorts this floor can make across the top.</p><p>Set each gate-setting against "
                   "the sort it makes on this floor. The engine is still running; you may go up and look "
                   "again as often as you like.</p>"),
        "items": items,
        "buckets": [{"key": k, "label": lbl} for k, lbl, _ in BUCKETS],
        "answer": answer,
        "maxAttempts": 0,
        # NOT endsEscape (2026-09-21): solving opens the vault; the vault DOOR ends it (_scratch/wiring/vault_open.py).
        "feedback": {"correct": "The frame settles, every setting against its sort, and the vault gives.",
                     "wrong": "The frame will not settle. One of those settings does not make that sort.",
                     "out": ""},
    }


if __name__ == "__main__":
    raise SystemExit(main())
