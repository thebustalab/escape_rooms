#!/usr/bin/env python3
"""make_figures.py — render each shrine's three votive figures as a clue plate.

WHY THIS EXISTS (2026-08-27). The escape asks the player to group nine shrines by the figures standing
in their niches, so the figures must be **individually identifiable and identical across rooms**. The
first gpt-image probe (`_scratch/l1_lamp_hall_1.png`) got the count and placement right — three objects
on the ledge under the banner — and the identities wrong: the bee rendered as a small pot, the monkey as
a cat, the maize-cake as a carved block. Beautiful room, unusable evidence. That is not a prompt bug to
grind at; it is the wrong tool for the job.

This is the same call `wrangling/egypt` made for its nine amphora seals: when the ART CARRIES THE ANSWER,
render it deterministically and let the image model do the room. The scene art keeps the niches, the
banners and the three-objects-on-a-ledge silhouette — flavour, and a box to click — and the *evidence*
lives on the clue plate the player opens.

SINGLE SOURCE OF TRUTH. The figure sets are imported from `_scratch/verify_temple_escape.py`, the file
whose brute force proves the grouping is unique, and the banner colours from `_scratch/build_scenario.py`,
which writes them into the scene prompts. So the plates cannot drift from either the verified board or
the art. Change a figure and the plate changes with it.

A CONSEQUENCE WORTH KNOWING: the engine partitions the field notebook into image entries and text entries
(`shared/pano-player.js` -> imgEntries / textEntries), and a clue carrying an image is excluded from the
flat text Clues list. So these plates land on the notebook's IMAGE BOARD — which is exactly where the
player wants them, since the ledger is a comparison across all nine and the board can be rearranged.

AND THEREFORE THE PLATE IS SQUARE (2026-08-27). A board tile is a 120px SQUARE painted with
`object-fit:cover`, so a non-square image is centre-cropped on the board. The first version of this plate
was a 900x360 strip — banner bar over three figures in a row — and on the board it showed the MIDDLE
FIGURE ONLY: two thirds of the evidence, silently gone, in the one place the player is meant to compare
all nine. Every other pickup set in the corpus is square already (egypt's seals 400x400, hospital's
postcards 800x800); this one was the outlier. Square, with the figures STACKED and named beside them, so
the whole plate survives the crop and the three silhouettes still read at thumbnail size.

The figures are NAMED on the plate. That is deliberate, and it is not a giveaway: the puzzle is grouping
shrines by *shared* figures, which needs reliable comparison across nine niches. Naming removes a
rendering lottery, not a deduction — the same reason Egypt prints the colour word under each seal.

Deterministic: same inputs -> same PNGs. Run:  python3 make_figures.py
Then:                                          python3 test_temple.py
"""
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle, Wedge, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_esc = _load("_verify_escape", os.path.join(HERE, "_scratch", "verify_temple_escape.py"))
_scn = _load("_build_scenario", os.path.join(HERE, "_scratch", "build_scenario.py"))
STATUES, NICHE = _esc.STATUES, _scn.NICHE

# The order figures are drawn in, so a shrine's plate is stable and two shrines sharing figures show
# them in the same left-to-right order — which is what makes the overlap readable at a glance.
ORDER = ["frog", "shell", "rain-jar", "paddle",
         "brazier", "maize-cake", "spindle-whorl", "censer",
         "seed-pod", "monkey", "macaw", "bee"]

STONE = "#cfc9ba"      # the carved-figure body: pale, high contrast against the plate ground
EDGE = "#3b3a33"
GROUND = "#20241f"     # plate ground: dark, so the pale figures read
LABEL = "#e8eef2"


def _frog(ax):
    ax.add_patch(Ellipse((0.5, 0.40), 0.52, 0.34, fc=STONE, ec=EDGE, lw=2))
    for dx in (-0.13, 0.13):                       # eyes, high and wide — the frog read
        ax.add_patch(Circle((0.5 + dx, 0.60), 0.09, fc=STONE, ec=EDGE, lw=2))
        ax.add_patch(Circle((0.5 + dx, 0.60), 0.035, fc=EDGE))
    for sx in (-1, 1):                             # splayed legs
        ax.add_patch(Polygon([(0.5 + sx * 0.22, 0.30), (0.5 + sx * 0.40, 0.22),
                              (0.5 + sx * 0.34, 0.16), (0.5 + sx * 0.18, 0.24)],
                             closed=True, fc=STONE, ec=EDGE, lw=2))


def _shell(ax):
    for i, r in enumerate([0.30, 0.225, 0.155, 0.095, 0.05]):
        ax.add_patch(Wedge((0.5 - i * 0.028, 0.42 + i * 0.030), r, 0, 360,
                           fc="none", ec=EDGE, lw=3))
    ax.add_patch(Wedge((0.5, 0.42), 0.30, 200, 340, fc=STONE, ec=EDGE, lw=2))


def _rain_jar(ax):
    ax.add_patch(Polygon([(0.30, 0.18), (0.70, 0.18), (0.62, 0.62), (0.38, 0.62)],
                         closed=True, fc=STONE, ec=EDGE, lw=2))
    ax.add_patch(Rectangle((0.42, 0.62), 0.16, 0.10, fc=STONE, ec=EDGE, lw=2))   # neck
    ax.add_patch(Ellipse((0.5, 0.745), 0.26, 0.09, fc=STONE, ec=EDGE, lw=2))     # stopper
    for y in (0.30, 0.42):                                                        # water bands
        ax.plot([0.335, 0.665], [y, y], color=EDGE, lw=2)


def _paddle(ax):
    ax.add_patch(Polygon([(0.5, 0.80), (0.60, 0.55), (0.56, 0.30), (0.44, 0.30), (0.40, 0.55)],
                         closed=True, fc=STONE, ec=EDGE, lw=2))
    ax.add_patch(Rectangle((0.465, 0.10), 0.07, 0.22, fc=STONE, ec=EDGE, lw=2))
    ax.plot([0.5, 0.5], [0.34, 0.74], color=EDGE, lw=2)


def _brazier(ax):
    ax.add_patch(Wedge((0.5, 0.42), 0.30, 180, 360, fc=STONE, ec=EDGE, lw=2))   # bowl
    ax.plot([0.20, 0.80], [0.42, 0.42], color=EDGE, lw=3)
    for sx in (-1, 0, 1):                                                        # three legs
        ax.plot([0.5 + sx * 0.16, 0.5 + sx * 0.22], [0.14, 0.14], color=EDGE, lw=3)
        ax.plot([0.5 + sx * 0.16, 0.5 + sx * 0.19], [0.14, 0.30], color=EDGE, lw=3)
    for dx, h in ((-0.10, 0.62), (0.0, 0.72), (0.10, 0.60)):                     # flames
        ax.add_patch(Polygon([(0.5 + dx - 0.05, 0.44), (0.5 + dx, h), (0.5 + dx + 0.05, 0.44)],
                             closed=True, fc=STONE, ec=EDGE, lw=2))


def _maize_cake(ax):
    ax.add_patch(Circle((0.5, 0.44), 0.30, fc=STONE, ec=EDGE, lw=2))
    for i in range(-2, 3):                                                       # cross-hatch
        ax.plot([0.5 + i * 0.10 - 0.14, 0.5 + i * 0.10 + 0.14],
                [0.44 - 0.22, 0.44 + 0.22], color=EDGE, lw=1.6)
        ax.plot([0.5 + i * 0.10 - 0.14, 0.5 + i * 0.10 + 0.14],
                [0.44 + 0.22, 0.44 - 0.22], color=EDGE, lw=1.6)
    ax.add_patch(Circle((0.5, 0.44), 0.30, fc="none", ec=EDGE, lw=3))


def _spindle_whorl(ax):
    ax.plot([0.5, 0.5], [0.08, 0.86], color=EDGE, lw=4)                          # the shaft
    ax.add_patch(Ellipse((0.5, 0.36), 0.54, 0.20, fc=STONE, ec=EDGE, lw=2))      # the whorl
    ax.add_patch(Ellipse((0.5, 0.36), 0.10, 0.05, fc=GROUND, ec=EDGE, lw=2))     # its hole
    ax.plot([0.5, 0.62], [0.86, 0.78], color=EDGE, lw=3)                          # a wisp of thread


def _censer(ax):
    ax.add_patch(Wedge((0.5, 0.36), 0.30, 0, 180, fc=STONE, ec=EDGE, lw=2))      # perforated dome
    ax.add_patch(Rectangle((0.30, 0.26), 0.40, 0.10, fc=STONE, ec=EDGE, lw=2))
    for dx, dy in ((-0.14, 0.46), (0.0, 0.52), (0.14, 0.46), (-0.07, 0.40), (0.07, 0.40)):
        ax.add_patch(Circle((0.5 + dx, dy), 0.030, fc=GROUND, ec=EDGE, lw=1.5))  # the holes
    ax.plot([0.5, 0.5], [0.66, 0.86], color=EDGE, lw=2)                           # hanging chain
    ax.plot([0.30, 0.70], [0.20, 0.20], color=EDGE, lw=3)


def _seed_pod(ax):
    ax.add_patch(Ellipse((0.5, 0.44), 0.26, 0.62, fc=STONE, ec=EDGE, lw=2))      # elongated pod
    ax.plot([0.5, 0.5], [0.16, 0.72], color=EDGE, lw=2)
    for y in (0.26, 0.40, 0.54, 0.66):                                            # the seeds inside
        ax.add_patch(Circle((0.5, y), 0.045, fc=GROUND, ec=EDGE, lw=1.6))
    ax.plot([0.5, 0.5], [0.75, 0.86], color=EDGE, lw=3)                           # stalk


def _monkey(ax):
    ax.add_patch(Ellipse((0.46, 0.36), 0.30, 0.34, fc=STONE, ec=EDGE, lw=2))     # seated body
    ax.add_patch(Circle((0.46, 0.63), 0.16, fc=STONE, ec=EDGE, lw=2))            # head
    for dx in (-0.11, 0.11):
        ax.add_patch(Circle((0.46 + dx, 0.70), 0.055, fc=STONE, ec=EDGE, lw=2))  # round ears
    for dx in (-0.05, 0.05):
        ax.add_patch(Circle((0.46 + dx, 0.63), 0.022, fc=EDGE))                  # eyes
    t = [(0.60, 0.26), (0.76, 0.30), (0.82, 0.46), (0.74, 0.54)]                  # the curling tail
    ax.plot([p[0] for p in t], [p[1] for p in t], color=EDGE, lw=4,
            solid_capstyle="round")


def _macaw(ax):
    ax.add_patch(Ellipse((0.42, 0.52), 0.28, 0.34, fc=STONE, ec=EDGE, lw=2))     # body
    ax.add_patch(Circle((0.38, 0.72), 0.13, fc=STONE, ec=EDGE, lw=2))            # head
    ax.add_patch(Polygon([(0.27, 0.74), (0.16, 0.69), (0.27, 0.66)],             # hooked beak
                         closed=True, fc=STONE, ec=EDGE, lw=2))
    ax.add_patch(Circle((0.40, 0.75), 0.022, fc=EDGE))
    ax.add_patch(Polygon([(0.53, 0.46), (0.86, 0.20), (0.80, 0.14), (0.50, 0.34)],
                         closed=True, fc=STONE, ec=EDGE, lw=2))                   # long tail
    ax.plot([0.44, 0.44], [0.34, 0.20], color=EDGE, lw=3)                         # leg


def _bee(ax):
    ax.add_patch(Ellipse((0.5, 0.40), 0.40, 0.30, fc=STONE, ec=EDGE, lw=2))      # body
    for x in (0.42, 0.54):                                                        # the stripes
        ax.plot([x, x], [0.27, 0.53], color=EDGE, lw=4)
    ax.add_patch(Circle((0.26, 0.44), 0.10, fc=STONE, ec=EDGE, lw=2))            # head
    for dx, dy in ((-0.03, 0.53), (0.03, 0.55)):                                  # antennae
        ax.plot([0.26 + dx, 0.26 + dx * 3], [0.52, 0.68], color=EDGE, lw=2)
    for sy in (1, -1):                                                            # wings
        ax.add_patch(Ellipse((0.54, 0.40 + sy * 0.22), 0.30, 0.16,
                             angle=sy * 18, fc="none", ec=EDGE, lw=2))
    ax.add_patch(Polygon([(0.70, 0.40), (0.80, 0.44), (0.80, 0.36)],              # sting
                         closed=True, fc=STONE, ec=EDGE, lw=2))


GLYPH = {"frog": _frog, "shell": _shell, "rain-jar": _rain_jar, "paddle": _paddle,
         "brazier": _brazier, "maize-cake": _maize_cake, "spindle-whorl": _spindle_whorl,
         "censer": _censer, "seed-pod": _seed_pod, "monkey": _monkey, "macaw": _macaw, "bee": _bee}


def plate(shrine, path):
    """One shrine's three figures, in ORDER, on a ground banded with its banner colour."""
    figs = [f for f in ORDER if f in STATUES[shrine]]
    assert len(figs) == 3, "%s has %d figures, expected 3" % (shrine, len(figs))
    colour, _ = NICHE[shrine]

    # SQUARE — the notebook board crops tiles to a square (see the module docstring). Figures stack down
    # the plate in ORDER, each with its name beside it, so two shrines sharing a figure show it at the
    # same place on both plates and the overlap is readable by eye.
    fig = plt.figure(figsize=(9.0, 9.0), dpi=100)
    fig.patch.set_facecolor(GROUND)
    # the banner colour as a bar across the head of the plate — the ledger's row identifier, carried
    # on the same image as the evidence so the two can never be separated in the player's notebook
    bar = fig.add_axes([0, 0.875, 1, 0.125]); bar.set_axis_off()
    bar.add_patch(Rectangle((0, 0), 1, 1, transform=bar.transAxes,
                            fc=_BANNER_HEX[colour], ec="none"))
    bar.text(0.5, 0.45, colour.upper(), transform=bar.transAxes, ha="center", va="center",
             fontsize=34, fontweight="bold", color=_BAR_TEXT[colour], family="DejaVu Sans")

    for i, name in enumerate(figs):
        y0 = 0.60 - i * 0.28
        ax = fig.add_axes([0.07, y0, 0.34, 0.265])
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_axis_off()
        ax.set_facecolor(GROUND)
        GLYPH[name](ax)
        fig.text(0.48, y0 + 0.13, name, ha="left", va="center", fontsize=32, color=LABEL,
                 family="DejaVu Sans")
    fig.savefig(path, facecolor=GROUND)
    plt.close(fig)
    return path


# Banner hexes: strongly saturated, and readable against the dark plate ground. These are the same nine
# names the scene prompts use, so the plate and the painted banner agree.
_BANNER_HEX = {"crimson": "#c1272d", "white": "#f2f2ef", "orange": "#e07a1f", "deep blue": "#27418f",
               "black": "#141414", "magenta": "#b5288a", "yellow": "#e8c31c", "violet": "#7b3fbf",
               "turquoise": "#1fa89b"}
_BAR_TEXT = {"white": "#20241f", "yellow": "#20241f", "turquoise": "#20241f", "orange": "#20241f"}
_BAR_TEXT = {k: _BAR_TEXT.get(k, "#f4f4f0") for k in _BANNER_HEX}


def main():
    os.makedirs(OUT, exist_ok=True)
    assert set(GLYPH) == set(ORDER), "glyph table and draw order disagree"
    drawn = set()
    for shrine in sorted(STATUES):
        p = plate(shrine, os.path.join(OUT, "%s.png" % shrine.lower()))
        drawn |= STATUES[shrine]
        print("  wrote", os.path.relpath(p, HERE), "-", ", ".join(sorted(STATUES[shrine])))
    missing = set(ORDER) - drawn
    assert not missing, "figure types never drawn (dead glyphs): %s" % sorted(missing)
    print("%d plates, %d figure types, all used" % (len(STATUES), len(ORDER)))


if __name__ == "__main__":
    main()
