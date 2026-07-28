#!/usr/bin/env python3
"""
Cave engine v4 -- the DYNAMIC DESCENT MAZE (clean-lever rebuild).

Redesign agreed 2026-07-26, resolving the v3 review:
  RULE 1 -- EXACTLY ONE DIVERTER PER STREAM. Each lever owns one stream and
    moves it independently and reversibly; throwing it back restores that
    stream exactly. (v3 had several levers steering one stream -> unpredictable,
    "won't undo" behaviour, and redundant/dead levers.)
  RULE 2 -- ONE FUSED GOAL. The win is simply "every stream resting in its
    correct basin" (the k-means assignment), which you can SEE on the map.
    There is no separate, invisible "reach the bottom" condition. (v3 let you
    reach the basins while the sort was still wrong -> looked solved when it
    wasn't.)

Shape (matches the 4-puzzle scenario):
  * FOUR diverters, one per stream, each unlocked by solving one data puzzle
    (modelled here as: a lever is thrown while standing on its platform).
  * Every lever starts in the WRONG position, so all four must be thrown -> no
    dead levers. The solution throws each exactly once (a forced ORDER +
    navigation puzzle); instances needing a re-throw are rejected to keep it to
    four clean throws.
  * Levers sit at four different depths, so setting them walks you down the shaft.
  * Streams MEANDER as they fall (baseline column per level) so no free chute;
    throwing a lever reroutes its stream, flooding/clearing platforms and
    opening the way to the next lever.

k = number of distinct basins the streams settle into (the guess-k lock at the
bottom is a separate hotspot, not part of this generator; k is reported here).

Renders both diagram styles (rings + side-on grid) for every water-state.
stdlib for logic; matplotlib only for PNGs.
"""
import argparse, math, random
from collections import deque


class Instance:
    def __init__(self, C, L, baseline, delta, tbit, levers, basins, edges):
        self.C, self.L = C, L
        self.baseline = baseline      # baseline[s] = [col per level 0..L]
        self.delta = delta            # delta[s]  = column shift when lever s is ON
        self.tbit = tbit              # tbit[s]   = correct final position (1 here)
        self.levers = levers          # levers[s] = (level, col) platform
        self.basins = basins          # basins[s] = correct basin column
        self.edges = edges
        self.start = None
        self.diverters = [dict(idx=s, stream=s, level=1, delta=delta[s],
                               lever=levers[s], tbit=tbit[s], kind="sort")
                          for s in range(len(baseline))]
        self.adj = {}
        for a, b in edges:
            self.adj.setdefault(a, []).append(b)
            self.adj.setdefault(b, []).append(a)

    def start_state(self):
        return tuple(1 - self.tbit[s] for s in range(len(self.baseline)))  # all wrong

    def col_at(self, s, level, sw):
        col = self.baseline[s][level] + (self.delta[s] if (sw[s] and level >= 1) else 0)
        return max(0, min(self.C - 1, col))

    def drowned(self, node, sw):
        lvl, col = node
        return any(self.col_at(s, lvl, sw) == col for s in range(len(self.baseline)))

    def flooded_set(self, sw):
        return frozenset((lvl, col)
                         for lvl in range(self.L + 1) for col in range(self.C)
                         if self.drowned((lvl, col), sw))

    def sort_ok(self, sw):
        return sw == tuple(self.tbit)

    def neighbors(self, node):
        return self.adj.get(node, [])

    def reach(self, sw, blocked=True):
        """nodes reachable from start under sw (dry-only if blocked)."""
        if self.drowned(self.start, sw):
            return set()
        seen = {self.start}; q = deque([self.start])
        while q:
            n = q.popleft()
            for m in self.neighbors(n):
                if m not in seen and (not blocked or not self.drowned(m, sw)):
                    seen.add(m); q.append(m)
        return seen


def _transitions(inst, node, sw):
    """Every (action, next-state) a player can legally take from (node, sw):
    step to an adjacent DRY platform, or throw the lever on this platform."""
    out = []
    for nn in inst.neighbors(node):
        if not inst.drowned(nn, sw):
            out.append((("move", nn), (nn, sw)))
    for s in range(len(inst.baseline)):
        if inst.levers[s] == node:
            nsw = list(sw); nsw[s] ^= 1; nsw = tuple(nsw)
            if not inst.drowned(node, nsw):
                out.append((("flip", s), (node, nsw)))
    return out


def reach_states(inst):
    """EXHAUSTIVE reachability: every (player-node, switch-vector) state the
    player can get into from the start, over all move/throw sequences. This is
    what lets us prove there is no shortcut to the bottom."""
    start = (inst.start, inst.start_state())
    if inst.drowned(*start):
        return set()
    seen = {start}; q = deque([start])
    while q:
        node, sw = q.popleft()
        for _, ns in _transitions(inst, node, sw):
            if ns not in seen:
                seen.add(ns); q.append(ns)
    return seen


def solve_path(inst, goal):
    """Shortest action sequence from start to any state satisfying goal(node, sw)."""
    start = (inst.start, inst.start_state())
    if inst.drowned(*start):
        return None
    seen = {start}; q = deque([start]); parent = {start: None}
    while q:
        node, sw = q.popleft()
        if goal(node, sw):
            path, cur = [], (node, sw)
            while parent[cur] is not None:
                prev, act = parent[cur]; path.append(act); cur = prev
            return path[::-1]
        for act, ns in _transitions(inst, node, sw):
            if ns not in seen:
                seen.add(ns); parent[ns] = ((node, sw), act); q.append(ns)
    return None


def feedback_clean(inst, actions):
    sw = list(inst.start_state())
    for a in actions:
        if a[0] == "flip":
            before = inst.flooded_set(tuple(sw))
            sw[a[1]] ^= 1
            if inst.flooded_set(tuple(sw)) == before:
                return False
    return True


def build(C, L, N, k, rng, p_bridge):
    baseline = []
    for _ in range(N):
        col = rng.randrange(C); path = [col]
        for _ in range(L):
            col = max(0, min(C - 1, col + rng.choice([-1, 0, 1]))); path.append(col)
        baseline.append(path)
    # choose k distinct basin columns; assign each stream one (every basin used)
    if k > C:
        return None
    basin_cols = rng.sample(range(C), k)
    assign = list(range(k)) + [rng.randrange(k) for _ in range(N - k)]
    rng.shuffle(assign)
    basins, delta = [], []
    for s in range(N):
        b = basin_cols[assign[s]]
        if b == baseline[s][L]:                      # lever must actually move it
            return None
        basins.append(b); delta.append(b - baseline[s][L])
    tbit = [1] * N                                    # correct = lever ON (sorted)
    # levers at N distinct depths (one per level 1..L), so solving descends
    # levers sit ABOVE the basins (levels 1..L-1), so the bottom is purely the exit
    depths = rng.sample(range(1, L), N) if N <= L - 1 else [rng.randint(1, L - 1) for _ in range(N)]
    levers = [(depths[s], rng.randrange(C)) for s in range(N)]
    ladders = [((l, c), (l + 1, c)) for l in range(L) for c in range(C)]
    bridges = [((l, c), (l, c + 1)) for l in range(L + 1) for c in range(C - 1)
               if rng.random() < p_bridge]
    inst = Instance(C, L, baseline, delta, tbit, levers, basins, ladders + bridges)
    start_sw = inst.start_state()
    top_dry = [c for c in range(C) if not inst.drowned((0, c), start_sw)]
    if not top_dry:
        return None
    inst.start = (0, rng.choice(top_dry))
    return inst


def generate(seed, C=5, L=5, N=4, k=3, p_bridge=0.4, attempts=40000):
    rng = random.Random(seed)
    allon = tuple([1] * N)
    best = None
    for _ in range(attempts):
        inst = build(C, L, N, k, rng, p_bridge)
        if inst is None:
            continue
        # every lever reachable on the skeleton (nothing walled off by missing bridges)
        skel = inst.reach(inst.start_state(), blocked=False)
        if not all(inst.levers[s] in skel for s in range(N)):
            continue
        R = reach_states(inst)                     # EXHAUSTIVE player-reachable states
        # NO SHORTCUT: you may not stand on ANY bottom platform unless all levers are thrown
        if any(node[0] == L and sw != allon for (node, sw) in R):
            continue
        # SOLVABLE: once all levers are thrown, a bottom platform IS reachable (the exit)
        if not any(node[0] == L and sw == allon for (node, sw) in R):
            continue
        actions = solve_path(inst, lambda node, sw: node[0] == L and sw == allon)
        if actions is None:
            continue
        flips = [a for a in actions if a[0] == "flip"]
        if len(flips) != N or not feedback_clean(inst, actions):   # 4 clean throws, all visible
            continue
        moves = len(actions) - len(flips)
        cand = (inst, actions, moves)
        if best is None or moves > best[2]:        # prefer more navigation (richer)
            best = cand
        if moves >= 2 * N + 2:                     # rich enough — take it
            return best
    return best


# ---------------------------------------------------------------- reporting ---
def ascii_levels(inst, sw):
    rows = []
    for lvl in range(inst.L + 1):
        cells = []
        for c in range(inst.C):
            ch = "#" if inst.drowned((lvl, c), sw) else "."
            if (lvl, c) == inst.start:
                ch = "S" if ch == "." else "s"
            cells.append(ch)
        tag = "catwalk" if lvl == 0 else ("basins " if lvl == inst.L else f"level {lvl}")
        rows.append(f"  ring {lvl} [{tag}]  " + "  ".join(cells))
    return "\n".join(rows) + "\n  ( # flooded, can't stand;  . dry;  S start )"


def fmt(inst, actions, moves):
    lab = lambda n: f"L{n[0]}C{n[1]}"
    N = len(inst.baseline)
    k = len(set(inst.basins))
    out = [f"DESCENT MAZE  C={inst.C} cols, L={inst.L} levels, {N} streams/levers, "
           f"k={k} basins, {sum(1 for e in inst.edges if e[0][0]==e[1][0])} bridges",
           f"start {lab(inst.start)}   goal: reach the basins floor L{inst.L} "
           f"(verified UNREACHABLE until all levers thrown)", ""]
    out.append("Streams (one lever each; baseline meander -> basin):")
    for s in range(N):
        out.append(f"  stream {s}: {inst.baseline[s]}  -> basin col {inst.basins[s]}  "
                   f"| lever g{s} at {lab(inst.levers[s])} (shift {inst.delta[s]:+d})")
    out.append("")
    order = [a[1] for a in actions if a[0] == "flip"]
    out.append(f"SOLUTION ({len(actions)} actions; throw order g{' -> g'.join(map(str, order))}):")
    for i, a in enumerate(actions, 1):
        if a[0] == "move":
            out.append(f"  {i:2d}. walk to {lab(a[1])}")
        else:
            out.append(f"  {i:2d}. THROW g{a[1]} (lever {lab(inst.levers[a[1]])}) — sorts stream {a[1]}")
    out += ["", "READ:", f"  throws: {len(order)} (one per lever)   navigation moves: {moves}",
            "  no-shortcut: VERIFIED — the bottom is unreachable in every throw-state but all-on",
            f"  k (basins) = {k}   <- the guess-k lock answer"]
    return "\n".join(out)


# ------------------------------------------------------------- diagram core ---
def _ring_xy(inst, level, col, R_out=1.0, R_in=0.30):
    r = R_out - level * (R_out - R_in) / inst.L if inst.L else R_out
    th = 2 * math.pi * col / inst.C - math.pi / 2
    return (r * math.cos(th), r * math.sin(th))


def _draw(ax, inst, sw, coord):
    import matplotlib.pyplot as plt
    cmap = plt.get_cmap("tab10")
    for a, b in inst.edges:
        xa, ya = coord(*a); xb, yb = coord(*b)
        ax.plot([xa, xb], [ya, yb], color="0.82", lw=1.3, zorder=1)
    N = len(inst.baseline)
    for s in range(N):
        off = s - (N - 1) / 2.0
        xs, ys = [], []
        for lvl in range(inst.L + 1):
            x, y = coord(lvl, inst.col_at(s, lvl, sw))
            xs.append(x + off * 0.07); ys.append(y + off * 0.05)
        ax.plot(xs, ys, color=cmap(s), lw=2.2, marker="o", ms=3, alpha=0.9,
                zorder=2, label=f"stream {s}")
        ax.text(xs[-1], ys[-1], f" {s}", color=cmap(s), fontsize=9, fontweight="bold", zorder=6)
    for lvl in range(inst.L + 1):
        for c in range(inst.C):
            x, y = coord(lvl, c)
            fl = inst.drowned((lvl, c), sw)
            ax.scatter([x], [y], s=120, zorder=4,
                       facecolor=("#3a6ea5" if fl else "white"),
                       edgecolor=("#3a6ea5" if fl else "0.4"), lw=1.3)
    for s in range(N):
        x, y = coord(*inst.levers[s])
        on = sw[s] == inst.tbit[s]
        ax.scatter([x], [y], marker="^", s=70, zorder=5,
                   color=("#27ae60" if on else "#c0392b"))
        ax.text(x, y + 0.06, f"g{s}", ha="center", va="bottom", fontsize=7, zorder=6)
    sx, sy = coord(*inst.start)
    ax.scatter([sx], [sy], marker="*", s=240, color="gold", edgecolor="0.3", zorder=7)


def _render(inst, sw, label, outdir, kind):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    import os
    if kind == "ring":
        fig, ax = plt.subplots(figsize=(5.2, 5.2))
        for lvl in range(inst.L + 1):
            rr = (_ring_xy(inst, lvl, 0)[0] ** 2 + _ring_xy(inst, lvl, 0)[1] ** 2) ** 0.5
            ax.add_patch(plt.Circle((0, 0), rr, fill=False, ls=":", color="0.8", lw=1))
        _draw(ax, inst, sw, lambda l, c: _ring_xy(inst, l, c))
        ax.set_title(f"rings (top-down) — {label}", fontsize=10)
    else:
        fig, ax = plt.subplots(figsize=(1.3 + inst.C, 1.0 + inst.L))
        _draw(ax, inst, sw, lambda l, c: (c, -l))
        ax.text(-0.8, 0, "top", fontsize=7, va="center", color="0.5")
        ax.text(-0.8, -inst.L, "basins", fontsize=7, va="center", color="0.5")
        ax.set_title(f"grid (side-on) — {label}", fontsize=10)
    ax.set_aspect("equal"); ax.axis("off")
    ax.legend(loc="upper right", fontsize=6, framealpha=0.6)
    p = os.path.join(outdir, f"{kind}_{label}.png")
    fig.savefig(p, dpi=118, bbox_inches="tight"); plt.close(fig)
    return p


def render_states(inst, actions, outdir):
    outs = []
    sw = list(inst.start_state()); step = 0
    def both(tag):
        outs.append(_render(inst, tuple(sw), tag, outdir, "ring"))
        outs.append(_render(inst, tuple(sw), tag, outdir, "grid"))
    both(f"step{step:02d}_start")
    for a in actions:
        if a[0] == "flip":
            sw[a[1]] ^= 1; step += 1; both(f"step{step:02d}_throw_g{a[1]}")
    return outs


if __name__ == "__main__":
    import os
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--levels", type=int, default=5)
    ap.add_argument("--streams", type=int, default=4)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--pbridge", type=float, default=0.4)
    ap.add_argument("--png", action="store_true")
    a = ap.parse_args()
    res = generate(a.seed, a.cols, a.levels, a.streams, a.k, a.pbridge)
    if res is None:
        print("no clean instance — change seed or loosen params"); raise SystemExit(1)
    inst, actions, moves = res
    print(fmt(inst, actions, moves))
    print("\nSHAFT AT START (all levers wrong; bottom not yet sorted):")
    print(ascii_levels(inst, inst.start_state()))
    print("\nSHAFT WHEN SOLVED (every stream home):")
    print(ascii_levels(inst, tuple(inst.tbit)))
    if a.png:
        here = os.path.dirname(os.path.abspath(__file__))
        outs = render_states(inst, actions, here)
        print(f"\nrendered {len(outs)} PNGs (ring + grid per state):")
        print("\n".join(f"  [{os.path.basename(p)}]" for p in outs))
