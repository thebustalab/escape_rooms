#!/usr/bin/env python3
"""prep_tiles.py — turn the raw generated figure art into the cut-out tiles the plates paste.

WHY (2026-09-20, Lucas: "use the image renderer for the pickup-clue images so they can be very
artistic while still accurate with the determinism needed for the escape to work").

The escape is solved by spotting that the frog in Ninestep's niche is the SAME frog as in Redsill's.
Generating nine beautiful plates would give nine separately-imagined frogs — the exact drift that sent
this scenario to deterministic plates in the first place (and still visible in the room panoramas,
where the maize-cake is a gilded loaf in one niche and a pale disc in another). So the art is generated
ONCE PER FIGURE TYPE (12 tiles), and every plate pastes the same file: not "drawn consistently" but
pixel-identical, which no prompt can promise.

This step is deliberately separate from `make_figures.py` and runs rarely:

    _scratch/figure_tiles/<name>.png   raw 1024x1024 generations, charcoal background   (source)
        -> prep_tiles.py ->
    figures/tiles/<name>.png           RGBA, background keyed out, trimmed, 512px        (committed)

Keying is a COLOUR-DISTANCE MATTE against the measured background colour, followed by a hole fill —
not a brightness threshold and not a flood fill. Both of those were tried on 2026-09-20 and both ate
the art: the objects' shaded sides sit within a few levels of the charcoal ground, so a flood fill
tunnelled straight into the frog and left fragments (the censer lost half its body). Measuring the
background colour from the border and matting on distance to it keeps shaded stone, and filling
enclosed holes afterwards keeps the frog's eyes and the censer's pierced lid opaque.

Deterministic: same inputs -> same outputs. `test_temple.py` checksums the results, so regenerated art
cannot silently replace a figure the verified board depends on.

    python3 prep_tiles.py            # rebuild every tile that is missing or out of date
    python3 prep_tiles.py --force    # rebuild all
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

import numpy as np
from PIL import Image
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "_scratch", "figure_tiles")
OUT = os.path.join(HERE, "figures", "tiles")
SIZE = 512          # long edge of the trimmed cut-out; plates draw it smaller still
PAD = 8             # transparent margin, so nothing touches the tile edge
T0, T1 = 10.0, 26.0  # Lab distance from the background colour: below T0 fully out, above T1 fully in


def cutout(path):
    """The object alone, on transparency, trimmed to its own bounding box."""
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"cannot read {path}")
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    h, w = lab.shape[:2]
    b = max(4, min(h, w) // 100)
    border = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                             lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(lab - bg, axis=2)
    alpha = np.clip((dist - T0) / (T1 - T0), 0, 1)

    # Fill enclosed holes: anything NOT reachable from the frame edge through background is interior
    # (an eye socket, a pierced hole's rim shadow) and must stay opaque.
    solid = (alpha > 0.5).astype(np.uint8)
    solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    ff = np.zeros((h + 2, w + 2), np.uint8)
    flood = solid.copy()
    cv2.floodFill(flood, ff, (0, 0), 1)              # 1 everywhere reachable background
    solid = solid | (1 - flood)                      # ... so the unreachable part is interior
    n, cc, st, _ = cv2.connectedComponentsWithStats(solid)
    if n > 1:                                        # keep the largest blob: drop stray flecks
        solid = (cc == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    alpha = np.maximum(alpha, solid.astype(np.float32))
    alpha = (cv2.GaussianBlur(alpha, (3, 3), 0) * 255).astype(np.uint8)
    obj = solid
    ys, xs = np.nonzero(obj)
    if not len(ys):
        raise SystemExit(f"{path}: nothing left after keying — check the background")
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), alpha])[y0:y1, x0:x1]
    im = Image.fromarray(rgba, "RGBA")
    scale = (SIZE - 2 * PAD) / max(im.size)
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2), im)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    made = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".png"):
            continue
        name = fn[:-4].replace("_", "-")          # maize_cake.png -> maize-cake (the board's name)
        src, dst = os.path.join(SRC, fn), os.path.join(OUT, name + ".png")
        if not a.force and os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            continue
        cutout(src).save(dst)
        made.append(name)
    for fn in sorted(os.listdir(OUT)):
        h = hashlib.sha1(open(os.path.join(OUT, fn), "rb").read()).hexdigest()[:12]
        print(f"  {fn:<22} {h}")
    print(f"{len(made)} tile(s) rebuilt" if made else "all tiles up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
