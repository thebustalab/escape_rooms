#!/usr/bin/env python3
"""
Reachability + ART BUDGET pass for the waterfalls puzzle.

The real art count is the number of distinct (player position x water-picture)
the student can actually reach in play — each is a different view to render.

Explores the full state space (player platform, diverter config) from the start:
  * move to an adjacent platform if the bridge between is PRESENT and NOT CUT
    (cut computed live by the router for that config),
  * throw the switch you're standing on (flips its diverter -> new config).
Then counts distinct configs, distinct pictures, and distinct (position,picture)
pairs reachable — that last number is the art budget.
"""
import json, os
from collections import deque
from router import present_bridges, cuts_for, diverter_events, DIVORDER

HERE = os.path.dirname(os.path.abspath(__file__))
PJSON = os.path.join(HERE, "..", "puzzle.json")
ROWS, COLS = 4, 3
SOURCES = (0, 1)                     # the two mechanically-active stream lanes (gaps)

# platform -> (switch label, diverter bit index).  S1@1,0  S2@2,0  S3@1,1  S4@1,2
SWITCHES = {
    (1, 0): ("S1", DIVORDER.index("D1")),
    (2, 0): ("S2", DIVORDER.index("D2")),
    (1, 1): ("S3", DIVORDER.index("D3")),
    (1, 2): ("S4", DIVORDER.index("D4")),
}


def neighbors(pos, passable):
    r, c = pos; out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            bid = f"V-{min(r, nr)}-{c}" if dr else f"H-{r}-{min(c, nc)}"
            if bid in passable:
                out.append((nr, nc))
    return out


def main():
    pj = json.load(open(PJSON))
    present = present_bridges(pj["absentBridges"])
    divs = diverter_events()

    # precompute cut set + picture for each of the 16 configs
    cut = {}
    for m in range(16):
        cfg = tuple((m >> i) & 1 for i in range(4))
        cut[cfg] = frozenset(cuts_for(SOURCES, cfg, present, divs))

    start = ((0, 0), (0, 0, 0, 0))
    seen = {start}; q = deque([start])
    while q:
        pos, cfg = q.popleft()
        passable = present - cut[cfg]
        for nb in neighbors(pos, passable):
            ns = (nb, cfg)
            if ns not in seen:
                seen.add(ns); q.append(ns)
        if pos in SWITCHES:
            bit = SWITCHES[pos][1]
            ncfg = tuple(b ^ (1 if i == bit else 0) for i, b in enumerate(cfg))
            ns = (pos, ncfg)
            if ns not in seen:
                seen.add(ns); q.append(ns)

    reachable_cfgs = {cfg for _, cfg in seen}
    reachable_pics = {cut[cfg] for cfg in reachable_cfgs}
    art_pairs = {(pos, cut[cfg]) for pos, cfg in seen}
    pics = sorted(reachable_pics, key=lambda p: len(p))
    picid = {p: i + 1 for i, p in enumerate(pics)}

    print(f"reachable (position, config) states : {len(seen)}")
    print(f"reachable diverter configs          : {len(reachable_cfgs)} of 16")
    print(f"distinct water-pictures reachable    : {len(reachable_pics)}")
    print(f"ART BUDGET  (position x picture)     : {len(art_pairs)}  <-- views to render\n")

    # how many distinct pictures each position is seen under
    bypos = {}
    for pos, pic in art_pairs:
        bypos.setdefault(pos, set()).add(picid[pic])
    print("views per platform (platform : which pictures it's seen under):")
    for pos in sorted(bypos):
        sw = f"  [{SWITCHES[pos][0]}]" if pos in SWITCHES else ""
        exit_ = "  [EXIT]" if pos == (ROWS - 1, 0) else ""
        print(f"   {pos}: {sorted(bypos[pos])}{sw}{exit_}")

    exit_reached = any(pos == (ROWS - 1, 0) for pos, _ in seen)
    print(f"\nexit (3,0) reachable in play: {exit_reached}")

    # ---- REFINEMENT: a player only sees changes ON their floor (no looking up/down) ----
    def floor_bridges(r, mode):
        vis = {f"H-{r}-{c}" for c in range(COLS - 1)}          # horizontals on this floor
        if mode == "B":
            vis |= {f"V-{r}-{c}" for c in range(COLS)}          # ladder leaving this floor
            if r - 1 >= 0:
                vis |= {f"V-{r-1}-{c}" for c in range(COLS)}    # ladder arriving at this floor
        return vis

    print("\n--- ART REFINED: only water changes visible ON the player's floor count ---")
    for mode, label in [("A", "horizontals on the floor only (strict 'no up/down')"),
                        ("B", "floor's horizontals + the ladders touching it")]:
        perpos = {}
        for pos, cfg in seen:
            vis = frozenset(cut[cfg] & floor_bridges(pos[0], mode))
            perpos.setdefault(pos, set()).add(vis)
        total = sum(len(v) for v in perpos.values())
        print(f"\n  [{mode}] {label}:  {total} views  (was 33)")
        for pos in sorted(perpos):
            sw = f"  [{SWITCHES[pos][0]}]" if pos in SWITCHES else ""
            ex = "  [EXIT]" if pos == (ROWS - 1, 0) else ""
            print(f"     {pos}: {len(perpos[pos])} view(s){sw}{ex}")


if __name__ == "__main__":
    main()
