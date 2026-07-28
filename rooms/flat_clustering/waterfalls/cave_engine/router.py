#!/usr/bin/env python3
"""
River ROUTER + calibration for the waterfalls puzzle.

Model (Lucas, 2026-07-26):
  * 3 streams fall from sources at the top, each in a LANE = the gap between two
    columns (lane g sits between col g and col g+1).
  * A stream running straight DOWN a lane lies across the HORIZONTAL bridge in
    that gap at each row it passes  -> cuts H-r-g.
  * A diverter shifts a stream sideways by whole columns: "/" left 1, "|" none,
    "\" right 1 (D4 by 2, since the water has fallen two storeys). Running
    sideways, the stream lies across the VERTICAL ladders it crosses -> cuts V.
  * A bridge is cut if ANY stream covers it.

Diverters (lane, band) read from puzzle.json marker positions; band r = the
vertical span between row r and r+1:
  D2: lane0 band0   D3: lane1 band0   D1: lane0 band1   D4: lane1 band2
Position per config bit (bit 0 = start position):
  D1: /=-1  |=0     D2: |=0  \\=+1    D3: |=0  /=-1     D4: /=-2  |=0

We don't know the 3 source lanes for certain, so we SEARCH them and keep the
set that reproduces all five authored states.
"""
import json, math, os, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
PJSON = os.path.join(HERE, "..", "puzzle.json")
ROWS, COLS = 4, 3

# shift (in columns) applied by each diverter in each config bit (bit 0 = start)
SHIFT = {
    "D1": (-1, 0),   # /=-1  |=0
    "D2": (0, +1),   # |=0   \=+1
    "D3": (0, -1),   # |=0   /=-1
    "D4": (-2, 0),   # /=-2  |=0
}
DIVORDER = ["D1", "D2", "D3", "D4"]


def diverter_events():
    """(y, lane, label) for each diverter, read from puzzle.json marker xy.
    lane = gap index = floor(col); y = fractional row (for fall-order)."""
    pj = json.load(open(PJSON))
    evs = []
    for m in pj["markers"]:
        if m["kind"] != "diverter":
            continue
        col = (m["x"] - 74) / 118.0
        y = (m["y"] - 74) / 118.0
        evs.append((y, int(math.floor(col)), m["label"]))
    return evs

# the 5 authored states as diverter-bit configs (see notes)
CONFIGS = [
    (0, 0, 0, 0),   # start
    (1, 0, 0, 0),   # after S1
    (1, 1, 0, 0),   # after S2
    (1, 1, 1, 0),   # after S3
    (1, 1, 0, 1),   # after re-throw S3
]


def present_bridges(absent):
    b = set()
    for r in range(ROWS):
        for c in range(COLS):
            if c < COLS - 1: b.add(f"H-{r}-{c}")
            if r < ROWS - 1: b.add(f"V-{r}-{c}")
    return b - set(absent)


def crossed_cols(a, b):
    return range(a + 1, b + 1) if b > a else range(b + 1, a + 1)


def route_stream(src_lane, bits, present, divs):
    """Fall from src_lane through all events (rows + diverters) in height order.
    At a row: cover the horizontal bridge in the current gap. At a diverter in
    the current gap: shift sideways, covering the vertical ladders crossed."""
    lane, cov = src_lane, set()
    # event list: rows (integer heights) + diverters (fractional), sorted by height
    ev = [(float(r), "row", r) for r in range(ROWS)]
    ev += [(y, "div", (ln, lbl)) for (y, ln, lbl) in divs]
    ev.sort(key=lambda e: e[0])
    for y, kind, payload in ev:
        if kind == "row":
            hid = f"H-{payload}-{lane}"
            if hid in present:
                cov.add(hid)
        else:
            ln, lbl = payload
            if ln == lane:
                sh = SHIFT[lbl][bits[DIVORDER.index(lbl)]]
                if sh:
                    nl = lane + sh
                    band = int(math.floor(y))
                    for c in crossed_cols(lane, nl):
                        vid = f"V-{band}-{c}"
                        if vid in present:
                            cov.add(vid)
                    lane = nl
    return cov


def cuts_for(sources, bits, present, divs):
    out = set()
    for s in sources:
        out |= route_stream(s, bits, present, divs)
    return out


def main():
    pj = json.load(open(PJSON))
    absent = pj["absentBridges"]
    present = present_bridges(absent)
    authored = [set(st["cutBridges"]) for st in pj["states"]]
    divs = diverter_events()
    print("diverter events (height y, lane gap, label):")
    for y, ln, lbl in sorted(divs): print(f"   y={y:.2f}  lane={ln}  {lbl}")
    print()

    lanes = [-1, 0, 1, 2]
    best = None
    for combo in itertools.product(lanes, repeat=3):
        score, detail = 0, []
        for i, cfg in enumerate(CONFIGS):
            got = cuts_for(combo, cfg, present, divs)
            ok = (got == authored[i])
            score += ok
            detail.append((i, ok, got))
        if best is None or score > best[0]:
            best = (score, combo, detail)

    score, combo, detail = best
    print(f"best source lanes {combo}: matched {score}/5 authored states\n")
    for i, ok, got in detail:
        print(f"STATE {i+1}: {'MATCH' if ok else 'MISMATCH'}")
        if not ok:
            want = authored[i]
            print(f"   authored cut: {sorted(want)}")
            print(f"   router  cut : {sorted(got)}")
            print(f"   router extra: {sorted(got-want)}   missing: {sorted(want-got)}")
    print()
    matched_4plus = (score >= 4)
    if score == 5:
        print("FULL MATCH — the routing model reproduces every authored state.")
    elif score == 4 and best[2][0][1] is False and sorted(best[2][0][2] - authored[0]) == ["V-2-0"]:
        print("4/5 — the only miss is state 1 missing V-2-0, which the router (and your\n"
              "state 2) say a 2-column D4 diversion should cut. Very likely an authoring slip.")

    # ---- derive ALL states: distinct pictures over every diverter combination ----
    if matched_4plus:
        from collections import defaultdict
        groups = defaultdict(list)
        for m in range(16):
            bits = tuple((m >> i) & 1 for i in range(4))
            cut = frozenset(cuts_for(combo, bits, present, divs))
            groups[cut].append(bits)
        print(f"\nART BUDGET — distinct map pictures across all 2^4 = 16 diverter combinations:"
              f"  {len(groups)} distinct pictures")
        gl = lambda b: "".join(map(str, b))
        for i, (cut, cfgs) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
            print(f"  picture {i}: {len(cfgs)} combo(s) [{', '.join(gl(c) for c in cfgs)}]  "
                  f"— {len(cut)} bridges cut")
        print("\n(That 16 is the upper bound. The number students can actually REACH in play is\n"
              " likely fewer — that needs the play-reachability pass over these combinations.)")


if __name__ == "__main__":
    main()
