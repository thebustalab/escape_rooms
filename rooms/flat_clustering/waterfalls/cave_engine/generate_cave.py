#!/usr/bin/env python3
"""
Cave engine -- Option A ("watershed assignment") prototype.

Designs a self-contained, NON-quantitative escape-puzzle instance for the
waterfall / flat-clustering ("waterfall") scenario. The player's cognitive
task is pure k-means ASSIGNMENT: sort each falling stream into the correct
one of k floor basins (its watershed = nearest basin centre). That maps
directly onto the harness's existing `grid` escape mechanic
({itemKey: bucketKey}), so NOTHING new is needed engine-side. This script
only DESIGNS a fair, unique instance and emits the answer + a layout spec
+ a top-down map for eyeballing / art reference.

Difficulty knobs:
  --k        number of basins (clusters)
  --streams  number of falling streams (items to assign)
  --traps    streams parked near a Voronoi boundary so BOTH floor axes are
             needed to resolve them -> the "k-means needs two dimensions"
             lesson, made physical. A trap is only accepted if judging by a
             single axis would send you to the WRONG basin.
  --seed     reproducibility

Uniqueness: assignment is nearest-basin with a strictly positive margin for
every stream, so the solution is unique by construction. Fairness: obvious
streams keep a wide margin; traps sit in a controlled narrow-margin band.

stdlib only. No physics, no dataset, no numbers shown to the student.
"""
import argparse, json, math, random

FLOOR = 100.0  # square cave floor, [0,FLOOR] x [0,FLOOR]
BASIN_NAMES = ["A", "B", "C", "D", "E", "F"]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def rank_dists(centroids, p):
    ds = sorted((dist(c, p), i) for i, c in enumerate(centroids))
    return ds  # [(dist, idx), ...] ascending


def place_centroids(k, rng, min_sep):
    best = None
    for _ in range(4000):
        pts = [(rng.uniform(16, FLOOR - 16), rng.uniform(16, FLOOR - 16)) for _ in range(k)]
        seps = [dist(pts[i], pts[j]) for i in range(k) for j in range(i + 1, k)]
        m = min(seps)
        if m >= min_sep:
            return pts
        if best is None or m > best[0]:
            best = (m, pts)
    return best[1]  # relaxed fallback


def one_axis_misleads(centroids, own_idx, p):
    """True if judging by x-only OR y-only picks a basin other than own_idx."""
    for axis in (0, 1):
        near = min(range(len(centroids)), key=lambda i: abs(centroids[i][axis] - p[axis]))
        if near != own_idx:
            return True
    return False


def make_obvious(centroids, own_idx, rng, min_sep):
    c = centroids[own_idx]
    for _ in range(400):
        r = rng.uniform(0.06, 0.30) * min_sep
        a = rng.uniform(0, 2 * math.pi)
        p = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
        if not (4 < p[0] < FLOOR - 4 and 4 < p[1] < FLOOR - 4):
            continue
        ds = rank_dists(centroids, p)
        if ds[0][1] == own_idx and (ds[1][0] - ds[0][0]) >= 0.35 * min_sep:
            return p
    return (c[0], c[1])


def make_trap(centroids, own_idx, rng, min_sep):
    """A point near the bisector with 'own' side, in a narrow margin band, that
    a single-axis judgement gets wrong."""
    c_own = centroids[own_idx]
    others = sorted((dist(c_own, centroids[j]), j) for j in range(len(centroids)) if j != own_idx)
    lo, hi = 0.04 * min_sep, 0.14 * min_sep
    fallback = None
    for _ in range(1500):
        _, j = others[rng.randrange(min(2, len(others)))]  # a near neighbour
        c_oth = centroids[j]
        mid = ((c_own[0] + c_oth[0]) / 2, (c_own[1] + c_oth[1]) / 2)
        d = (c_oth[0] - c_own[0], c_oth[1] - c_own[1])
        L = math.hypot(*d) or 1.0
        u = (d[0] / L, d[1] / L)          # toward the other basin
        perp = (-u[1], u[0])
        back = rng.uniform(0.03, 0.10) * min_sep  # nudge onto own side
        side = rng.uniform(-0.55, 0.55) * min_sep  # slide along the boundary
        p = (mid[0] - back * u[0] + side * perp[0],
             mid[1] - back * u[1] + side * perp[1])
        if not (4 < p[0] < FLOOR - 4 and 4 < p[1] < FLOOR - 4):
            continue
        ds = rank_dists(centroids, p)
        if ds[0][1] != own_idx:
            continue
        margin = ds[1][0] - ds[0][0]
        if lo <= margin <= hi:
            if one_axis_misleads(centroids, own_idx, p):
                return p, True
            if fallback is None:
                fallback = (p, False)
    if fallback:
        return fallback
    return make_obvious(centroids, own_idx, rng, min_sep), False


def generate(k, n_streams, n_traps, seed):
    rng = random.Random(seed)
    min_sep = min(36.0, 130.0 / (k + 1))
    centroids = place_centroids(k, rng, min_sep)

    # round-robin cluster ownership for balance
    owners = [i % k for i in range(n_streams)]
    rng.shuffle(owners)
    trap_slots = set(rng.sample(range(n_streams), min(n_traps, n_streams)))

    streams = []
    for i in range(n_streams):
        own = owners[i]
        if i in trap_slots:
            p, misleads = make_trap(centroids, own, rng, min_sep)
            kind = "trap"
        else:
            p = make_obvious(centroids, own, rng, min_sep)
            misleads = one_axis_misleads(centroids, own, p)
            kind = "obvious"
        ds = rank_dists(centroids, p)
        streams.append({
            "id": f"S{i+1}",
            "xy": (round(p[0], 1), round(p[1], 1)),
            "basin": BASIN_NAMES[own],
            "kind": kind,
            "margin": round(ds[1][0] - ds[0][0], 1),
            "one_axis_misleads": misleads,
            "inlet_deg": round(math.degrees(math.atan2(p[1] - 50, p[0] - 50)) % 360, 0),
        })

    # verify uniqueness (strict nearest-basin, positive margin)
    assert all(s["margin"] > 0 for s in streams), "ambiguous stream produced"

    answer = {s["id"]: s["basin"] for s in streams}
    return {
        "params": {"k": k, "streams": n_streams, "traps": n_traps, "seed": seed,
                   "min_sep": round(min_sep, 1)},
        "basins": [{"name": BASIN_NAMES[i], "xy": (round(c[0], 1), round(c[1], 1))}
                   for i, c in enumerate(centroids)],
        "streams": streams,
        "grid_answer": answer,
    }


def ascii_map(spec, W=52, H=24):
    grid = [[" "] * W for _ in range(H)]

    def cell(x, y):
        col = round(x / FLOOR * (W - 1))
        row = round((FLOOR - y) / FLOOR * (H - 1))
        return max(0, min(H - 1, row)), max(0, min(W - 1, col))

    for s in spec["streams"]:
        r, c = cell(*s["xy"])
        grid[r][c] = s["id"][1:]  # the number
    for b in spec["basins"]:
        r, c = cell(*b["xy"])
        grid[r][c] = f"({b['name']})"[1]  # the letter; overwrite streams
        # write parens around it if room
        if c > 0:
            grid[r][c - 1] = "("
        if c < W - 1:
            grid[r][c + 1] = ")"
    top = "+" + "-" * W + "+"
    lines = [top] + ["|" + "".join(row) + "|" for row in grid] + [top]
    return "\n".join(lines)


def report(spec):
    p = spec["params"]
    out = []
    out.append(f"CAVE INSTANCE  k={p['k']} basins, {p['streams']} streams, "
               f"{p['traps']} traps  (seed {p['seed']})")
    out.append("")
    out.append("Basins (floor centres):")
    for b in spec["basins"]:
        out.append(f"  ({b['name']})  at {b['xy']}")
    out.append("")
    out.append("Streams  (id: landing xy -> correct basin | kind | margin | 1-axis-trap):")
    for s in spec["streams"]:
        flag = "  <-- one axis misleads" if s["one_axis_misleads"] else ""
        out.append(f"  {s['id']}: {s['xy']} -> {s['basin']}  | {s['kind']:7s} "
                   f"| margin {s['margin']:5.1f}{flag}")
    out.append("")
    out.append("Top-down floor map  (letters = basins, numbers = streams):")
    out.append(ascii_map(spec))
    out.append("")
    out.append("grid escape answer  {stream: basin}:")
    out.append("  " + json.dumps(spec["grid_answer"]))
    out.append("")
    # complexity read
    traps = [s for s in spec["streams"] if s["kind"] == "trap"]
    real_traps = [s for s in traps if s["one_axis_misleads"]]
    tight = min(s["margin"] for s in spec["streams"])
    out.append("COMPLEXITY READ:")
    out.append(f"  items to assign : {p['streams']}  (buckets: {p['k']})")
    out.append(f"  genuine 2D traps: {len(real_traps)} of {len(traps)} requested "
               f"(need both axes; single-axis judgement fails)")
    out.append(f"  tightest margin : {tight}  (0 would be unfair/ambiguous; this is >0 so unique)")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--streams", type=int, default=7)
    ap.add_argument("--traps", type=int, default=2)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--json", action="store_true", help="dump spec JSON to cave_instance.json")
    a = ap.parse_args()
    spec = generate(a.k, a.streams, a.traps, a.seed)
    print(report(spec))
    if a.json:
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "cave_instance.json"), "w") as f:
            json.dump(spec, f, indent=2)
        print(f"\n[wrote {os.path.join(here, 'cave_instance.json')}]")
