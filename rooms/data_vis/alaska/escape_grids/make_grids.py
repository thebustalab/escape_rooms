#!/usr/bin/env python3
"""
make_grids.py — render the four grids for the Alaska "Claire's filtered glass" escape.

Claire (the station pilot whose helicopter you borrow) leaves a note in each of the three puzzle
rooms; each note is a 4x4 sheet of coloured glass (red / green / blue) in which SOME panes are clear
windows and the rest are filled with coloured glass. Superimpose the three sheets — Secret-of-the-
Unicorn style — and EXACTLY ONE position is a clear window through all three. The beacon room (the
boss) holds a fourth note: the same 4x4 grid, every cell a helicopter tail number. The tail number
that stays clear through all three sheets is the code for the helicopter keypad (the escape1 lock).

Pedagogy — the escape IS the filter() lesson made physical. Each sheet is one filter(): its coloured
panes are the rows that condition REMOVES (covered up), its clear windows the rows that PASS. Stack the
three and you have a logical AND — every non-answer gets covered by at least one filter, and the single
cell left uncovered through all three is the row that survives every filter. filter(), filter(),
filter() → the one that remains is the answer. (No code / no data — the move, transferred onto the
room's world.)

RENDER CONTRACT (fixed 2026-07-22): a PASS/open cell is a genuinely TRANSPARENT window (alpha 0) so the
tail number beneath reads straight through; a filtered-out cell is an opaque coloured pane that COVERS
the number. The masks are picked up with overlay:true (tiles render translucent and stack in the field
notebook), so the answer is the ONE cell still clear once all three are laid over the board — NOT a cell
the panes cover. The earlier build had this inverted (open cells were painted solid, covering the
winner); if you ever see the answer getting hidden under the panes, this contract was broken again.

Outputs (this dir): mask_room1.png (red), mask_room2.png (green), mask_room3.png (blue),
code_grid.png, and grids.json (the machine-readable answer key for wiring + a regression check).

Deterministic: same source in, same PNGs + same winning code out. Self-verifying: asserts each pair
of masks shares >= 2 open cells (so no pair gives it away) and the triple intersection is exactly one.

CACHE NOTE: these PNGs are regenerated IN PLACE under a stable filename, so a browser holds onto the
old ones. The scenario.json clue `image` refs therefore carry a ?v= cache token (currently ?v=4). When
you regenerate the masks with a visible change, BUMP that token on all four escape_grids image refs in
scenario.json so players re-fetch — otherwise the stale images keep showing (this bit us 2026-07-22).

Run:  python3 make_grids.py    (needs Pillow)
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

# --- The masks: sets of OPEN (clear-window) cells as (row, col), 1-indexed, row 1 = top ------------
# An OPEN cell is a transparent window (the code shows through); every other cell is a coloured pane
# that covers the code. Designed so pairwise intersections are 2 cells each and the triple is exactly
# (3,2): that single cell is a window in ALL three sheets, so it is the only tail number left clear.
TARGET = (3, 2)
MASK = {
    "room1": {(3, 2), (1, 1), (4, 4), (1, 4), (4, 1), (2, 2)},          # red
    "room2": {(3, 2), (1, 1), (2, 3), (1, 3), (4, 2), (3, 4)},          # green
    "room3": {(3, 2), (4, 4), (2, 3), (1, 2), (4, 3), (2, 4)},          # blue
}
COLOUR = {  # (glass RGB, room label)
    "room1": ((225, 74, 74), "RED"),
    "room2": ((74, 205, 120), "GREEN"),
    "room3": ((96, 165, 250), "BLUE"),
}

# --- The 16 tail numbers, row-major (row1 left->right, then row2, ...) ----------------------------
# All same shape (N + 3 alphanumerics) so the winning one doesn't stand out. Winner sits at TARGET.
CODES = [
    "N2GA", "N7RX", "N4KP", "N9TL",   # row 1
    "N3WQ", "N6BZ", "N1VC", "N8HM",   # row 2
    "N5PD", "N0KR", "N2FJ", "N7SY",   # row 3   (col 2 -> N0KR -> WINNER)
    "N4XW", "N9NB", "N3LT", "N6CE",   # row 4
]

def verify():
    keys = list(MASK)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            shared = MASK[keys[i]] & MASK[keys[j]]
            assert len(shared) >= 2, f"pair {keys[i]}&{keys[j]} shares only {shared} (would leak answer)"
    triple = MASK["room1"] & MASK["room2"] & MASK["room3"]
    assert triple == {TARGET}, f"triple intersection must be exactly {{{TARGET}}}, got {triple}"
    for k, cells in MASK.items():
        assert all(1 <= r <= 4 and 1 <= c <= 4 for (r, c) in cells), f"{k} has an out-of-range cell"
    # Every non-winner cell must be covered (filtered out) by at least one sheet, else more than one
    # cell would read clear through all three. (Follows from the triple being a single cell, but assert
    # it directly so a future MASK edit that breaks it fails loudly here.)
    for r in range(1, 5):
        for c in range(1, 5):
            if (r, c) == TARGET:
                continue
            covered = any((r, c) not in MASK[k] for k in MASK)
            assert covered, f"cell {(r, c)} is open in all three sheets — a second clear cell"

def code_at(cell):
    r, c = cell
    return CODES[(r - 1) * 4 + (c - 1)]

# --- Rendering ------------------------------------------------------------------------------------
CELL, PAD, LAB = 120, 28, 34          # cell px, outer padding, label gutter
BG = (10, 20, 28)                     # matches the house dark panel
INK = (207, 230, 216)
DIM = (110, 132, 122, 170)            # faint labels (RGBA) — legible on one sheet, quiet when stacked
LINE = (60, 90, 120, 90)             # faint grid lines (RGBA) — help registration without going heavy
COVER_ALPHA = 255                     # coloured panes: opaque so a single filter decisively covers (the
                                      # notebook tile's own translucency does the glass/layering blend)

def _font(sz, bold=False):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    try:
        return ImageFont.truetype(p, sz)
    except OSError:
        return ImageFont.load_default()

def _canvas(transparent=False):
    side = LAB + PAD + 4 * CELL + PAD
    img = Image.new("RGBA", (side, side), (0, 0, 0, 0) if transparent else BG + (255,))
    return img, ImageDraw.Draw(img), side

def _origin():
    return LAB + PAD, LAB + PAD          # top-left of the cell grid

def _labels(d, side):
    f = _font(20, bold=True)
    ox, oy = _origin()
    for c in range(4):                   # column numbers along the top
        cx = ox + c * CELL + CELL // 2
        d.text((cx, oy - LAB // 2 - 2), str(c + 1), fill=DIM, font=f, anchor="mm")
    for r in range(4):                   # row numbers down the left
        cy = oy + r * CELL + CELL // 2
        d.text((ox - LAB // 2 - 2, cy), str(r + 1), fill=DIM, font=f, anchor="mm")

def _grid_lines(d):
    ox, oy = _origin()
    for i in range(5):
        d.line([(ox + i * CELL, oy), (ox + i * CELL, oy + 4 * CELL)], fill=LINE, width=2)
        d.line([(ox, oy + i * CELL), (ox + 4 * CELL, oy + i * CELL)], fill=LINE, width=2)

def render_mask(key):
    open_cells = MASK[key]
    (gr, gg, gb), name = COLOUR[key]
    img, d, side = _canvas(transparent=True)
    ox, oy = _origin()
    for r in range(1, 5):
        for c in range(1, 5):
            x0, y0 = ox + (c - 1) * CELL, oy + (r - 1) * CELL
            x1, y1 = x0 + CELL, y0 + CELL
            if (r, c) in open_cells:
                # A CLEAR WINDOW — completely transparent, nothing painted at all (no rim, no grid line),
                # so the code beneath reads straight through with no tint or frame whatsoever. Alignment
                # comes from the coloured panes' own rims and the board's grid showing through the holes.
                pass
            else:
                # COLOURED GLASS — an opaque-ish pane that covers (filters out) the code beneath. Darkened
                # body + brighter rim so stacked panes read as deepening layers of glass.
                d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2],
                            fill=(gr // 3 + 12, gg // 3 + 12, gb // 3 + 12, COVER_ALPHA))
                d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], outline=(gr, gg, gb, 235), width=2)
    # No grid lines on the mask: they would frame the clear windows and read as "not fully transparent".
    # The coloured panes' rims and the board's own grid (visible through the holes) carry the alignment.
    _labels(d, side)
    img.save(os.path.join(HERE, f"mask_{key}.png"))
    return name

def render_codes():
    img, d, side = _canvas(transparent=False)
    ox, oy = _origin()
    f = _font(30, bold=True)
    for r in range(1, 5):
        for c in range(1, 5):
            x0, y0 = ox + (c - 1) * CELL, oy + (r - 1) * CELL
            x1, y1 = x0 + CELL, y0 + CELL
            d.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], fill=(16, 28, 38, 255))
            d.text(((x0 + x1) // 2, (y0 + y1) // 2), code_at((r, c)), fill=INK, font=f, anchor="mm")
    _grid_lines(d)
    _labels(d, side)
    img.save(os.path.join(HERE, "code_grid.png"))

def main():
    verify()
    names = {k: render_mask(k) for k in MASK}
    render_codes()
    winner = code_at(TARGET)
    key = {
        "target_cell": {"row": TARGET[0], "col": TARGET[1]},
        "winning_code": winner,
        "mask_open_cells": {k: sorted(list(v)) for k, v in MASK.items()},
        "mask_colours": {k: COLOUR[k][1] for k in MASK},
        "codes_row_major": CODES,
        "render": "open cell = transparent window; other cells = coloured glass that covers the code",
        "note": "escape1 lock answer = winning_code; keep length 4. Escape is out of the codec.",
    }
    json.dump(key, open(os.path.join(HERE, "grids.json"), "w"), indent=2)
    print("Masks:", names)
    print("Triple-intersection cell:", TARGET, "-> winning code:", winner)
    print("Wrote mask_room1/2/3.png, code_grid.png, grids.json")

if __name__ == "__main__":
    main()
