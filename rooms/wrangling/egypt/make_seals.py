#!/usr/bin/env python3
"""make_seals.py — render the nine collectable amphora seals as notebook-board tiles.

The escape is a hand-done `group_by(trait) |> summarise()`: the player must pile the nine seals by
colour, then by shape, then by size, and reduce each pile. Rendering the seals as IMAGES puts them on
the field notebook's draggable collected-items board (`shared/pano-player.js` -> "COLLECTED-ITEMS
BOARD"), so the regrouping is a physical drag rather than arithmetic held in the head off a text list.
Text-only pickups land in the flat Clues list instead, which cannot be rearranged — that is what
confused the first playtest (2026-08-13; full record in notes.md).

SINGLE SOURCE OF TRUTH: the traits are PARSED OUT OF scenario.json's own seal pickup lines, the very
strings `test_egypt.py` re-derives the escape key from. The art therefore cannot drift from the
verified key — change a seal's traits and the tile changes with it.

Deterministic: same scenario.json -> same PNGs. Square 400x400 (the board renders them at 120px with
object-fit:cover, so a square source is required).

Run:  python3 make_seals.py        (needs matplotlib)
Then: python3 test_egypt.py        (asserts every seal carries an existing image)
"""
import json, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
SCEN = os.path.join(HERE, "scenario.json")
OUT = os.path.join(HERE, "seals")

SEAL_RE = re.compile(r"Seal (\d+) — (\w+) · (\w+) · (\w+) · numeral (\d+)")

# Fired-clay palette. The three clays are kept far apart in BOTH hue and lightness so red/amber stay
# separable for a red-green colourblind player; the colour WORD is printed on every tile as the
# authoritative cue (the board tile has no hover tooltip on mobile).
CLAY = {
    "red":   {"fill": "#a8412c", "dark": "#5f2013", "rim": "#c4614a"},
    "blue":  {"fill": "#2d5f8c", "dark": "#16324f", "rim": "#4a80ad"},
    "amber": {"fill": "#d59a2a", "dark": "#7d5410", "rim": "#e8b955"},
}
PAPYRUS, EDGE = "#e9dcbe", "#c3b18a"

# half-extents as a fraction of the tile, before the shape's aspect is applied
SIZE_R = {"small": 0.185, "medium": 0.250, "large": 0.315}
# (x, y) aspect multipliers — round is the reference; tall is drawn up, squat is drawn wide
SHAPE_A = {"round": (1.00, 1.00), "tall": (0.72, 1.30), "squat": (1.32, 0.70)}

CX, CY = 0.50, 0.575          # seal centre; the lower band is left for the colour word
WORD_Y = 0.075


def read_seals():
    """[(n, colour, shape, size, numeral)] parsed from the scenario's own pickup strings."""
    doc = json.load(open(SCEN, encoding="utf-8"))
    out = []
    for room in doc["rooms"]:
        for h in (room.get("plannedHotspots") or []):
            m = SEAL_RE.match(str(h.get("pickup", "")))
            if m:
                out.append((int(m.group(1)), m.group(2), m.group(3), m.group(4), int(m.group(5))))
    out.sort()
    return out


def seal_tile(n, colour, shape, size, numeral, path):
    """One 400x400 tile: papyrus ground, the clay seal at its true shape+size, the numeral on its face."""
    c = CLAY[colour]
    ax_, ay_ = SHAPE_A[shape]
    r = SIZE_R[size]
    rx, ry = r * ax_, r * ay_

    fig = plt.figure(figsize=(4, 4), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor=PAPYRUS, edgecolor="none"))
    ax.add_patch(Rectangle((0.012, 0.012), 0.976, 0.976, facecolor="none", edgecolor=EDGE, linewidth=3))

    # the seal: a soft cast shadow, the clay body, and a lighter rim so the form reads at tile scale
    ax.add_patch(Ellipse((CX + 0.012, CY - 0.014), rx * 2, ry * 2,
                         facecolor="#00000022", edgecolor="none"))
    ax.add_patch(Ellipse((CX, CY), rx * 2, ry * 2,
                         facecolor=c["fill"], edgecolor=c["dark"], linewidth=3))
    ax.add_patch(Ellipse((CX, CY), rx * 1.74, ry * 1.74,
                         facecolor="none", edgecolor=c["rim"], linewidth=2, alpha=0.85))

    # the tally numeral, pressed into the face: sized off the seal's SHORT axis so it always fits
    fs = min(rx * 1.45, ry) * 320
    ax.text(CX, CY - 0.004, str(numeral), ha="center", va="center",
            fontsize=fs, fontweight="bold", color="#f7edd6", zorder=5)

    # the colour word — the non-visual cue, and the only reliable one on a phone (no hover tooltip)
    ax.text(CX, WORD_Y, colour.upper(), ha="center", va="center",
            fontsize=21, fontweight="bold", color=c["dark"], family="DejaVu Sans")

    fig.savefig(path, facecolor=PAPYRUS)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    seals = read_seals()
    if len(seals) != 9:
        print(f"FAIL  expected 9 seals in scenario.json, parsed {len(seals)}")
        return 1
    for n, colour, shape, size, numeral in seals:
        p = os.path.join(OUT, f"seal_{n}.png")
        seal_tile(n, colour, shape, size, numeral, p)
        print(f"  wrote  seals/seal_{n}.png   {colour} · {shape} · {size} · numeral {numeral}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
