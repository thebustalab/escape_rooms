#!/usr/bin/env python3
"""
make_starchart.py — render the crow's-nest ESCAPE star charts for the airship (The Alembic) scenario.

The escape is the DATA-FREE meta-echo of the boss (2026-07-22 redesign; supersedes make_maps.py, which
plotted the SOLVENTS data with labels stripped). Here the captain's star-astrolabe carries three plates,
each projecting the SAME field of named stars a different way. The crow's-nest `mapview` shows one plate
depending on the astrolabe plate-dial state (m1/m2/m3). A captain's clue names one "homeward house" (the
Anchor — the box drawn on every plate). Exactly ONE star holds the Anchor in ALL THREE projections while
the others drift in and out; that invariant star's NAME goes into the captain's helm lock.

Cognitive move preserved from the boss: find the one member that stays in-region across multiple mappings.
Fully decoupled: no solvents, no CSV, no data values — just the ship's own sky.

Star field is HAND-CONSTRUCTED (deterministic, no RNG): each star has three celestial coordinates
(a, b, c). The three plates plot the coordinate PAIRS (a,b)/(b,c)/(a,c). A star is "in the Anchor" on a
plate iff both of that plate's coords fall in the house range -> so a star is in the Anchor on 0, 1, or
(only if all three coords are in range) 3 plates; being in exactly 2 is geometrically impossible. Exactly
one star (SOLIRA) has all three in range -> the unique invariant. Decoys sit in the Anchor on exactly one
plate; fillers on none. **All star names are the same length (6)** so the lock keeps a fixed length.

Renders:
  nest/map_m1.png  — plate I   (ascension x declination)
  nest/map_m2.png  — plate II  (declination x magnitude)
  nest/map_m3.png  — plate III (ascension x magnitude)
  nest/codes.json  — { answer_star, name_length, house, stars, ... }  (lock answer = answer_star)

Run: python3 rooms/data_vis2/airship/nest/make_starchart.py   (needs matplotlib; no network)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOUSE = (6.0, 8.0)            # the Anchor: coord range that defines "in the homeward house" on each axis
LO, HI = HOUSE
AXMIN, AXMAX = 0.0, 10.0
BG, FRAME, GRID = "#05090f", "#22303f", "#0e1922"
STAR, GLOW, INK = "#ffe6a6", "#ffcf6b", "#bcd0e0"
HOUSE_EDGE, HOUSE_FILL = "#7fd3c4", "#0f2b2b"  # the Anchor: pale-teal edge, deep-teal fill

# (name, a, b, c)  — a=ascension, b=declination, c=magnitude. Names all 6 letters.
STARS = [
    ("SOLIRA", 7.0, 7.0, 7.0),   # the invariant: all three in [6,8] -> in the Anchor on every plate
    # plate-I decoys (a,b in range, c out): in the Anchor on plate I only
    ("VANTIS", 6.6, 7.5, 2.1),
    ("MERROW", 7.6, 6.4, 9.2),
    # plate-II decoys (b,c in range, a out): in the Anchor on plate II only
    ("CALDER", 1.6, 6.7, 7.3),
    ("ORIVAS", 9.1, 7.4, 6.5),
    # plate-III decoys (a,c in range, b out): in the Anchor on plate III only
    ("THESSA", 6.5, 1.9, 7.1),
    ("NYXARA", 7.5, 9.3, 6.6),
    # fillers: at most one coord in range -> in the Anchor on no plate
    ("DRAVEN", 2.0, 3.1, 8.7),
    ("PERRIN", 9.0, 2.2, 3.3),
    ("MARISA", 3.4, 9.1, 2.0),
    ("CORVEL", 7.9, 1.2, 1.4),
    ("ELSTRA", 4.5, 4.6, 4.2),
    ("RAVENA", 1.5, 7.1, 1.6),
    ("OSTRIX", 5.2, 5.1, 9.4),
    ("BELUNE", 9.6, 9.5, 5.0),
    ("TORVIN", 2.7, 8.9, 9.7),
    ("HALEEN", 8.6, 3.0, 5.5),
]
# plate -> (x-coord index, y-coord index) into (a,b,c); filename; projection label
PLATES = [
    ("map_m1.png", 0, 1, "I"),
    ("map_m2.png", 1, 2, "II"),
    ("map_m3.png", 0, 2, "III"),
]


def in_range(v):
    return LO <= v <= HI


def in_house_on_plate(coords, xi, yi):
    return in_range(coords[xi]) and in_range(coords[yi])


def verify():
    """Assert a single invariant star and report per-plate Anchor membership. Raises on failure."""
    per_plate = {}
    all_three = []
    for name, a, b, c in STARS:
        coords = (a, b, c)
        hits = [lbl for (_, xi, yi, lbl) in PLATES if in_house_on_plate(coords, xi, yi)]
        if len(hits) == 3:
            all_three.append(name)
        # geometric guarantee: a star can never be in the Anchor on exactly two plates
        assert len(hits) != 2, "%s is in the Anchor on exactly 2 plates (should be impossible)" % name
    for fn, xi, yi, lbl in PLATES:
        inh = [nm for (nm, a, b, c) in STARS if in_house_on_plate((a, b, c), xi, yi)]
        per_plate[lbl] = inh
        assert len(inh) >= 2, "plate %s has <2 stars in the Anchor (%s) — no drift" % (lbl, inh)
    assert len(all_three) == 1, "need exactly one invariant star; got %s" % all_three
    return all_three[0], per_plate


def main():
    answer, per_plate = verify()

    json.dump({
        "answer_star": answer,
        "name_length": len(answer),
        "house": list(HOUSE),
        "axis_range": [AXMIN, AXMAX],
        "stars": {nm: [a, b, c] for (nm, a, b, c) in STARS},
        "per_plate_in_house": per_plate,
        "note": "escape lock answer = answer_star; make_starchart.py is the source of truth",
    }, open(os.path.join(HERE, "codes.json"), "w"), indent=2)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        sys.exit("matplotlib not available — install it or run this where matplotlib exists.")

    for fname, xi, yi, lbl in PLATES:
        fig, ax = plt.subplots(figsize=(6.2, 4.8), dpi=150)
        fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
        ax.set_xlim(AXMIN, AXMAX); ax.set_ylim(AXMIN, AXMAX)
        # faint star-chart grid (no numbers)
        ax.grid(True, color=GRID, linewidth=0.6)
        # the Anchor (homeward house): same corner on every plate
        ax.add_patch(Rectangle((LO, LO), HI - LO, HI - LO, facecolor=HOUSE_FILL,
                               edgecolor=HOUSE_EDGE, linewidth=1.4, alpha=0.85, zorder=1))
        ax.plot([(LO + HI) / 2], [HI - 0.28], marker="v", ms=6, color=HOUSE_EDGE, zorder=2)  # anchor mark
        # stars
        for nm, a, b, c in STARS:
            coords = (a, b, c)
            x, y = coords[xi], coords[yi]
            ax.scatter([x], [y], s=150, color=GLOW, alpha=0.18, zorder=3)          # glow
            ax.scatter([x], [y], s=42, marker="*", color=STAR,
                       edgecolor="#8a6a24", linewidth=0.4, zorder=4)               # star
            ax.annotate(nm, (x, y), textcoords="offset points", xytext=(5, 4),
                        fontsize=6.4, color=INK, family="serif", zorder=5)
        # unmarked celestial axes (no tick labels), faint frame + a plate mark
        ax.set_xticklabels([]); ax.set_yticklabels([]); ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_color(FRAME)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, fname), facecolor=fig.get_facecolor())
        plt.close(fig)

    print("wrote map_m1/m2/m3.png (star plates I/II/III) + codes.json for %d stars" % len(STARS))
    for lbl, inh in per_plate.items():
        print("  plate %-3s Anchor: %s" % (lbl, ", ".join(inh)))
    print("ANSWER star (invariant across all three plates) -> lock answer: %s" % answer)


if __name__ == "__main__":
    main()
