#!/usr/bin/env python3
"""make_postcards.py — deterministically render the facet-collage escape's load-bearing art.

Renders the nine collectable POSTCARDS (postcards/postcard_1.png .. postcard_9.png) and the DOOR COLLAGE
(postcards/collage_door.png). These carry exact content — the code digit, the three faceting tags, the
prose, and the highlighted middle row — so they are drawn deterministically (matplotlib, same as the old
escape make_map.py), NOT via gpt-image, which mangles text. The wrap/scene art (the summer break-room 360
etc.) is the separate gpt harness job; the editorial notes are plain text `clue` bodies (no art).

Single source of truth: everything (digit, season/remoteness/length tags, prose, sender, catalogue #) is
imported from escape2_facets.py — the same module the combinatorics verifier checks — so the printed
digits can never drift from the verified keypad code (729). Deterministic: same inputs -> same PNGs.

Run:  python3 make_postcards.py     (needs matplotlib). Re-run after any card/digit/prose edit, then
re-run escape2_facets.py to re-verify the code.
"""
import os, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

import escape2_facets as F   # CARDS, DIGIT, POSTCARD, SEASON, REMOTE, LENGTH, length_index, catalog

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "postcards")

# paper + ink, and one accent per SEASON (a faint visual echo of the season; the TAG is authoritative)
PAPER, INK, FAINT = "#f4ecdd", "#2c2317", "#e6d9c2"
SEASON_C = {0: "#6a9e6b", 1: "#e0a13c", 2: "#c0603a"}   # June green / July gold / August rust


def _rounded(ax, x, y, w, h, **kw):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.02", **kw))


def postcard(a, b, path):
    """One 800x800 postcard: seasonal band, prose, a postage-stamp code digit, a franked tag strip."""
    digit = F.DIGIT[(a, b)]
    c = F.length_index(a, b)
    msg, sender = F.POSTCARD[(a, b)]
    n = F.catalog(a, b)
    acc = SEASON_C[a]

    fig = plt.figure(figsize=(8, 8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor=PAPER, edgecolor="none"))
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor="none", edgecolor="#d8c9ad", linewidth=6))
    ax.add_patch(Rectangle((0, 0.985), 1, 0.02, facecolor=acc, edgecolor="none"))   # seasonal top band

    # postage stamp (top-right): season-filled, perforated look, the bold CODE DIGIT in white
    sx, sy, sw, sh = 0.70, 0.70, 0.22, 0.24
    ax.add_patch(Rectangle((sx, sy), sw, sh, facecolor="#fbf6ec", edgecolor=acc,
                           linewidth=2, linestyle=(0, (1, 1.4))))
    ax.add_patch(Rectangle((sx + 0.018, sy + 0.02), sw - 0.036, sh - 0.04, facecolor=acc, edgecolor="none"))
    ax.text(sx + sw / 2, sy + sh / 2 - 0.005, str(digit), ha="center", va="center",
            fontsize=64, fontweight="bold", color="#fbf6ec")
    ax.add_patch(Circle((sx + 0.02, sy + sh - 0.02), 0.075, fill=False, edgecolor="#7a6a4d",
                        linewidth=1.4, alpha=0.5))   # faint postmark

    # the message (handwritten-ish: italic ink), wrapped
    ax.text(0.07, 0.90, textwrap.fill(msg, width=30), ha="left", va="top",
            fontsize=15.5, style="italic", color=INK, linespacing=1.5, wrap=False)
    ax.text(0.07, 0.30, "- " + sender, ha="left", va="top", fontsize=17, style="italic",
            color=INK, fontweight="bold")

    # franked TAG strip along the bottom (the semi-structured faceting surface)
    ax.add_patch(Rectangle((0.05, 0.10), 0.90, 0.075, facecolor=FAINT, edgecolor="#cbbb9a", linewidth=1.5))
    tags = "   ·   ".join([F.SEASON[a], F.REMOTE[b], F.LENGTH[c]])
    ax.text(0.5, 0.1375, tags, ha="center", va="center", fontsize=17, color="#4a3d28",
            fontweight="bold", fontfamily="monospace")
    ax.text(0.93, 0.055, "#%d of 9" % n, ha="right", va="center", fontsize=11, color="#9c8b6c")

    fig.savefig(path, dpi=100); plt.close(fig)


def door_collage(path):
    """The back-of-door 'started layout': an empty 3x3 with the MIDDLE ROW highlighted (the code slots).
    No axis labels (the faceting variables come from the editorial notes, not this diagram)."""
    fig = plt.figure(figsize=(9, 7), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 9); ax.set_ylim(0, 7); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 9, 7, facecolor="#efe6d4", edgecolor="none"))
    ax.add_patch(Rectangle((0, 0), 9, 7, facecolor="none", edgecolor="#c9b892", linewidth=8))
    ax.text(4.5, 6.35, "Magazine Article Collage", ha="center", va="center", fontsize=24,
            color="#7a6a4d", fontweight="bold")

    cw, ch, gx, gy = 2.2, 1.35, 0.55, 0.42          # cell size + gaps
    x0 = (9 - (3 * cw + 2 * gx)) / 2
    y0 = 0.75
    for r in range(3):                               # r=0 bottom .. r=2 top (drawn); middle row r=1
        for cidx in range(3):
            x = x0 + cidx * (cw + gx)
            y = y0 + r * (ch + gy)
            mid = (r == 1)
            _rounded(ax, x, y, cw, ch,
                     facecolor="#f6e9c8" if mid else "#e3d7bd",
                     edgecolor=("#e0a13c" if mid else "#b7a884"),
                     linewidth=(3.5 if mid else 1.8), linestyle="-")
            if mid:                                  # glowing slot ring
                _rounded(ax, x + 0.12, y + 0.12, cw - 0.24, ch - 0.24,
                         facecolor="none", edgecolor="#e0a13c", linewidth=1.4, alpha=0.6)
    fig.savefig(path, dpi=100); plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    for (a, b) in F.CARDS:
        p = os.path.join(OUT, "postcard_%d.png" % F.catalog(a, b))
        postcard(a, b, p)
    door_collage(os.path.join(OUT, "collage_door.png"))
    print("wrote %d postcards + collage_door.png to %s" % (len(F.CARDS), os.path.relpath(OUT, HERE)))


if __name__ == "__main__":
    main()
