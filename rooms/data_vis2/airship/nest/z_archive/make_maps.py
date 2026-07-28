#!/usr/bin/env python3
"""
make_maps.py — render the crow's-nest ESCAPE charts for the airship (The Alembic) scenario.

The escape is the UNLABELLED / "alien" echo of the boss (find the solvent that is immiscible with
water, relative_polarity nearest 0.6, and density below water — verified answer: 1-butanol). The
crow's-nest `mapview` hotspot shows one of three charts depending on the room-1 sigil-dial state
(m1/m2/m3). Each chart is a DIFFERENT aesthetic mapping of the same solvents data, axes unmarked, every
bottle shown ONLY by a 4-char coded label (never its real name). The one code sitting in the right
region of ALL THREE is the answer — its code goes into the captain's-quarters lock.

Renders:
  nest/map_m1.png  — density (x) x relative_polarity (y)
  nest/map_m2.png  — relative_polarity (x) x miscible-with-water (two bands)
  nest/map_m3.png  — density (x) x miscible-with-water (two bands)
  nest/codes.json  — { solvent: code }  (reference; the lock answer = 1-butanol's code)

Deterministic codes (md5[:4], stable across runs) so the map labels and the lock stay in sync.
Run: python3 rooms/data_vis2/airship/nest/make_maps.py   (needs matplotlib; fetches solvents.csv)
"""
import csv, io, json, hashlib, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://thebustalab.github.io/phylochemistry/sample_data/solvents.csv"
ANSWER = "1-butanol"          # verified intersection solvent
BG, FG, DOT, INK = "#06111a", "#123", "#ffd88c", "#cfe6d8"


def code_for(name):
    return hashlib.md5(name.encode()).hexdigest()[:4].upper()


def load():
    raw = urllib.request.urlopen(URL, timeout=30).read().decode("utf-8")
    rows = []
    for r in csv.DictReader(io.StringIO(raw)):
        try:
            d = float(r["density"]); p = float(r["relative_polarity"])
        except (ValueError, KeyError):
            continue
        mis = str(r.get("miscible_with_water", "")).strip().lower() in ("true", "yes", "y", "1")
        rows.append({"solvent": r["solvent"], "density": d, "polarity": p,
                     "miscible": mis, "code": code_for(r["solvent"])})
    return rows


def scatter(ax, rows, xkey, ykey, jitter=None):
    import random
    for r in rows:
        x = r[xkey]
        y = r[ykey] if jitter is None else ((1 if r[ykey] else 0) + (hash(r["code"]) % 100 - 50) / 400.0)
        ax.scatter([x], [y], s=26, color=DOT, edgecolor="#a8791f", linewidth=0.6, zorder=3)
        ax.annotate(r["code"], (x, y), textcoords="offset points", xytext=(4, 3),
                    fontsize=6.5, color=INK, family="monospace", zorder=4)


def main():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        sys.exit("matplotlib not available — install it or run this where matplotlib exists.")

    rows = load()
    json.dump({r["solvent"]: r["code"] for r in rows},
              open(os.path.join(HERE, "codes.json"), "w"), indent=2)
    ans_code = code_for(ANSWER)

    specs = [
        ("map_m1.png", "density", "polarity", None),      # ◈ density x polarity
        ("map_m2.png", "polarity", "miscible", True),     # ⬢ polarity x miscibility (2 bands)
        ("map_m3.png", "density", "miscible", True),      # ✶ density x miscibility (2 bands)
    ]
    for fname, xk, yk, jit in specs:
        fig, ax = plt.subplots(figsize=(6.2, 4.6), dpi=150)
        fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
        scatter(ax, rows, xk, yk, jitter=jit)
        # UNLABELLED: strip all tick labels + axis titles (alien chart), keep faint frame
        ax.set_xticklabels([]); ax.set_yticklabels([])
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_color("#2a3a48")
        ax.grid(True, color="#16242f", linewidth=0.6)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, fname), facecolor=fig.get_facecolor())
        plt.close(fig)

    print("wrote map_m1/m2/m3.png + codes.json for %d solvents" % len(rows))
    print("ANSWER solvent '%s' → lock code: %s" % (ANSWER, ans_code))


if __name__ == "__main__":
    main()
