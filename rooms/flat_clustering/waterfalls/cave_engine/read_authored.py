#!/usr/bin/env python3
"""
Read an author-made puzzle.json (the bridge-cut model) and play it back:
for each state, compute passable edges (bridge present AND not cut), find where
the player can reach from their entry position, and render an ASCII + PNG grid.
Confirms the no-shortcut property (bottom row unreachable until the final state).
"""
import json, os, sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "..", "puzzle.json")

# the intended traversal spine (player entry position + narrative per state)
SPINE = [
    ((0, 0), "START", "only the ladder to (1,0) is open → reach S1"),
    ((1, 0), "after S1 / D1", "the (1,0)-(2,0) ladder opens → drop to S2 at (2,0)"),
    ((2, 0), "after S2 / D2", "(1,0)-(1,1) opens → climb back, cross to S3 at (1,1)"),
    ((1, 1), "after S3 / D3", "(1,1)-(1,2) opens, (1,1)-(1,0) cuts behind you → reach S4 (boss)"),
    ((1, 1), "re-throw S3 (state 5)", "left column opens → descend (1,0)-(2,0)-(3,0), ESCAPE"),
]


def load():
    with open(PATH) as f:
        return json.load(f)


def all_bridges(rows, cols):
    b = {}
    for r in range(rows):
        for c in range(cols):
            if c < cols - 1:
                b[f"H-{r}-{c}"] = ((r, c), (r, c + 1))
            if r < rows - 1:
                b[f"V-{r}-{c}"] = ((r, c), (r + 1, c))
    return b


def passable(bridges, absent, cut):
    """edge id -> (a,b) for bridges that are present AND not cut."""
    return {bid: ab for bid, ab in bridges.items()
            if bid not in absent and bid not in cut}


def reach(passable_edges, start):
    adj = {}
    for a, b in passable_edges.values():
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen = {start}; q = deque([start])
    while q:
        n = q.popleft()
        for m in adj.get(n, []):
            if m not in seen:
                seen.add(m); q.append(m)
    return seen


def switch_at(markers, rows, cols):
    """map platform (r,c) -> switch label, using nearest platform to marker xy."""
    MARG, CELL = 74, 118
    out = {}
    for m in markers:
        if m["kind"] != "switch":
            continue
        c = round((m["x"] - MARG) / CELL); r = round((m["y"] - MARG) / CELL)
        out[(r, c)] = m["label"]
    return out


def ascii_state(g, absent, cut, entry, reachable, sw):
    rows, cols = g["grid"]["rows"], g["grid"]["cols"]
    def cell(r, c):
        if (r, c) == entry:      s = " P "
        elif (r, c) in sw:       s = sw[(r, c)].center(3)
        elif (r, c) == (3, 0):   s = "EX "
        else:                    s = " o " if (r, c) in reachable else " . "
        return s
    def hb(r, c):
        bid = f"H-{r}-{c}"
        if bid in absent: return "   "
        return "=X=" if bid in cut else "==="
    def vb(r, c):
        bid = f"V-{r}-{c}"
        if bid in absent: return " "
        return "X" if bid in cut else "|"
    lines = []
    for r in range(rows):
        row = "".join(cell(r, c) + (hb(r, c) if c < cols - 1 else "") for c in range(cols))
        lines.append(row)
        if r < rows - 1:
            inter = "".join((" " + vb(r, c) + " ") + ("   " if c < cols - 1 else "")
                            for c in range(cols))
            lines.append(inter)
    return "\n".join(lines)


def to_grid(x, y, MARG=74, CELL=118):
    """editor pixel xy -> (plot_x, plot_y) in the grid's (col, -row) frame."""
    return ((x - MARG) / CELL, -(y - MARG) / CELL)


def render_png(g, absent, cut, entry, reachable, sw, markers, rivers, title, path):
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception:
        return None
    rows, cols = g["grid"]["rows"], g["grid"]["cols"]
    bridges = all_bridges(rows, cols)
    fig, ax = plt.subplots(figsize=(1.4 + cols * 1.3, 1.2 + rows * 1.1))
    # rivers (illustrative polylines), drawn under everything
    for riv in rivers:
        pts = [to_grid(p["x"], p["y"]) for p in riv["points"]]
        if len(pts) > 1:
            ax.plot([p[0] for p in pts], [p[1] for p in pts],
                    color=riv.get("color", "#2e6fb0"), lw=3, alpha=0.5, zorder=0,
                    solid_capstyle="round")
    for bid, (a, b) in bridges.items():
        (ra, ca), (rb, cb) = a, b
        xa, ya, xb, yb = ca, -ra, cb, -rb
        if bid in absent:
            ax.plot([xa, xb], [ya, yb], color="#dde5eb", lw=1, ls=(0, (1, 4)), zorder=1)
        elif bid in cut:
            ax.plot([xa, xb], [ya, yb], color="#c0392b", lw=3, ls=(0, (2, 2)), zorder=1)
        else:
            ax.plot([xa, xb], [ya, yb], color="#7a8a97", lw=3, zorder=1)
    for r in range(rows):
        for c in range(cols):
            fc = "#bfe6c8" if (r, c) in reachable else "#ffffff"
            ax.scatter([c], [-r], s=430, facecolor=fc, edgecolor="0.35", lw=1.4, zorder=3)
            lbl = sw.get((r, c), "")
            if (r, c) == (3, 0): lbl = "EXIT"
            if lbl:
                ax.text(c, -r, lbl, ha="center", va="center", fontsize=8, fontweight="bold", zorder=4)
    # diverters (triangles) at their fractional positions
    MARG, CELL = 74, 118
    for m in markers:
        if m["kind"] != "diverter":
            continue
        c = (m["x"] - MARG) / CELL; r = (m["y"] - MARG) / CELL
        ax.scatter([c], [-r], marker="^", s=90, color="#58d68d", edgecolor="#1e7d47", zorder=5)
        ax.text(c, -r + 0.16, m["label"], ha="center", fontsize=6, zorder=6)
    ax.scatter([entry[1]], [-entry[0]], marker="*", s=260, color="gold", edgecolor="0.3", zorder=6)
    ax.set_title(title, fontsize=9); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, dpi=115, bbox_inches="tight"); plt.close(fig)
    return path


def main():
    g = load()
    rows, cols = g["grid"]["rows"], g["grid"]["cols"]
    absent = set(g["absentBridges"])
    bridges = all_bridges(rows, cols)
    markers = g["markers"]
    sw = switch_at(markers, rows, cols)
    states = g["states"]
    print(f"puzzle.json — {rows} rows x {cols} cols, {len(states)} states, "
          f"{len(absent)} missing bridges, switches at {sorted(sw.items())}\n")
    for i, (entry, name, gain) in enumerate(SPINE):
        st = states[i]
        cut = set(st["cutBridges"])
        pe = passable(bridges, absent, cut)
        rr = reach(pe, entry)
        bottom = sorted(n for n in rr if n[0] == rows - 1)
        print(f"===== STATE {i+1}: {name} =====")
        print(f"  player enters at {entry};  {gain}")
        print(ascii_state(g, absent, cut, entry, rr, sw))
        print(f"  reachable: {sorted(rr)}")
        print(f"  bottom-row reachable: {bottom if bottom else 'NONE (sealed)'}")
        p = render_png(g, absent, cut, entry, rr, sw, markers, st.get("rivers", []),
                       f"state {i+1}: {name}", os.path.join(HERE, f"authored_s{i+1}.png"))
        print()
    print("NO-SHORTCUT CHECK: bottom row must be unreachable in states 1-4, reachable only in state 5.")


if __name__ == "__main__":
    main()
