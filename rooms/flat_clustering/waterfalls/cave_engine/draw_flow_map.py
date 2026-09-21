#!/usr/bin/env python3
"""
draw_flow_map.py — render the shaft's layout and its water, one PNG per configuration.

WHY: the layout lives in `puzzle.json` + `router.py` and could only be read by running code or
squinting at `player_map.html` (which needs a browser). These PNGs are flat images, so they open in
the mobile file viewer — which is how Lucas actually reads things.

WHAT IS DRAWN, per configuration:
  * the 8 platforms, each labelled with its ROOM, at its (row, col);
  * the bridges that EXIST (`puzzle.json.absentBridges` removed) — solid grey when passable,
    dashed red when the water is lying on them (`router.cuts_for`), which is what "cut" means;
  * each stream's path down its lane, shifting sideways at each diverter that stands in it;
  * the three floor basins (engine lanes -1, 0, 1) and which of them the streams end in.

Run: python3 draw_flow_map.py     (writes into ../_scratch/flow_maps/)
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from router import DIVORDER, SHIFT, diverter_events, present_bridges, cuts_for, ROWS, COLS
import reach_art as ra
import basin_sort as bs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "_scratch", "flow_maps")
PJSON = os.path.join(HERE, "..", "puzzle.json")

ROOM = {(0, 0): "catwalk", (1, 0): "station1", (1, 1): "station3", (1, 2): "boss",
        (2, 0): "station2", (2, 1): "spillway", (3, 0): "basin", (3, 1): "sump"}
SWITCH_AT = {(1, 0): "S1", (2, 0): "S2", (1, 1): "S3", (1, 2): "S4"}
BASIN_NAME = {-1: "OUTER", 0: "MIDDLE", 1: "NEAR"}

X = lambda c: c * 2.0            # platform x
Y = lambda r: -r * 2.0           # platform y (row 0 at top)
LANE_X = lambda g: X(g) + 1.0    # a lane sits in the gap between col g and g+1


def stream_path(src_lane, bits):
    """[(lane, y_at_which_it_shifts), …] — the polyline of one stream down the shaft."""
    pts, lane = [(src_lane, Y(0) + 1.5)], src_lane
    for y, ln, lbl in sorted(diverter_events(), key=lambda e: e[0]):
        if ln == lane:
            sh = SHIFT[lbl][bits[DIVORDER.index(lbl)]]
            if sh:
                yy = Y(0) - y * 2.0
                pts.append((lane, yy))
                lane += sh
                pts.append((lane, yy))
    pts.append((lane, Y(ROWS - 1) - 1.2))
    return pts


def draw(bits, title, path):
    pj = json.load(open(PJSON, encoding="utf-8"))
    present = present_bridges(set(pj["absentBridges"]))
    cuts = cuts_for(ra.SOURCES, bits, present, diverter_events())

    fig, ax = plt.subplots(figsize=(7.2, 8.6))
    ax.set_facecolor("#0e1116")
    fig.patch.set_facecolor("#0e1116")

    for bid in sorted(present):
        kind, a, b = bid.split("-")
        a, b = int(a), int(b)
        if kind == "H":                      # row a, gap b: joins (a,b)-(a,b+1)
            xs, ys = [X(b), X(b + 1)], [Y(a), Y(a)]
        else:                                # band a, col b: joins (a,b)-(a+1,b)
            xs, ys = [X(b), X(b)], [Y(a), Y(a + 1)]
        wet = bid in cuts
        ax.plot(xs, ys, lw=5 if not wet else 4,
                color="#e05a5a" if wet else "#8b95a3",
                ls="--" if wet else "-", zorder=2, alpha=0.95)

    for (r, c), name in ROOM.items():
        ax.add_patch(plt.Circle((X(c), Y(r)), 0.42, color="#1b2430", ec="#d8b26a", lw=2, zorder=3))
        sw = SWITCH_AT.get((r, c))
        ax.text(X(c), Y(r) + 0.62, name, ha="center", va="bottom", color="#e8e3d8",
                fontsize=10, zorder=4)
        if sw:
            thrown = bits[DIVORDER.index("D" + sw[1])]
            ax.text(X(c), Y(r), sw, ha="center", va="center", zorder=5, fontsize=9,
                    color="#8fd694" if thrown else "#7b8794",
                    fontweight="bold" if thrown else "normal")

    for i, src in enumerate(ra.SOURCES):
        pts = stream_path(src, bits)
        xs = [LANE_X(l) for l, _ in pts]
        ys = [y for _, y in pts]
        ax.plot(xs, ys, lw=3.5, color=["#5ec8e0", "#c8a0ff"][i], zorder=6, alpha=0.95,
                solid_capstyle="round")
        ax.text(xs[0], ys[0] + 0.35, "stream %d" % (i + 1), ha="center",
                color=["#5ec8e0", "#c8a0ff"][i], fontsize=9)

    sort = bs.sort_at_basin(bits)
    floor_y = Y(ROWS - 1) - 2.0
    for lane in sorted(BASIN_NAME):
        fed = len(sort.get(lane, []))
        ax.add_patch(plt.Rectangle((LANE_X(lane) - 0.55, floor_y - 0.3), 1.1, 0.6,
                                   color="#2a4a3a" if fed else "#1b2430",
                                   ec="#d8b26a" if fed else "#4a5361", lw=2, zorder=3))
        ax.text(LANE_X(lane), floor_y - 0.75, BASIN_NAME[lane], ha="center", va="top",
                color="#e8e3d8" if fed else "#6b7480", fontsize=9)
        if fed:
            ax.text(LANE_X(lane), floor_y, "%d" % fed, ha="center", va="center",
                    color="#e8e3d8", fontsize=11, fontweight="bold", zorder=4)

    k = len(sort)
    ax.set_title(title + "\nk = %d  (%s)" % (k, ", ".join(
        "%s x%d" % (BASIN_NAME[l], len(v)) for l, v in sort.items())),
        color="#e8e3d8", fontsize=12, pad=14)
    ax.legend(handles=[Line2D([], [], color="#8b95a3", lw=4, label="span you can cross"),
                       Line2D([], [], color="#e05a5a", lw=4, ls="--", label="span the water is lying on")],
              loc="upper left", facecolor="#1b2430", edgecolor="#4a5361", labelcolor="#e8e3d8",
              fontsize=9)
    ax.set_xlim(-1.6, X(COLS - 1) + 1.8)
    ax.set_ylim(floor_y - 1.6, Y(0) + 2.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", os.path.relpath(path, HERE))


def main():
    os.makedirs(OUT, exist_ok=True)
    draw((0, 0, 0, 0), "START — as you find the engine (nothing thrown)",
         os.path.join(OUT, "00_start.png"))
    labels = {(1, 1, 0, 1): "ARRIVAL at the basin — S1 thrown, S2 thrown, S3 shut, S4 thrown",
              (0, 0, 0, 1): "BASIN SORT A — S1 shut, S2 shut",
              (1, 0, 0, 1): "BASIN SORT B — S1 thrown, S2 shut",
              (0, 1, 0, 1): "BASIN SORT C — S1 shut, S2 thrown"}
    for i, (bits, title) in enumerate(labels.items(), start=1):
        draw(bits, title, os.path.join(OUT, "%02d_%s.png" % (i, "".join(map(str, bits)))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
