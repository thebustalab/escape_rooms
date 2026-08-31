#!/usr/bin/env python3
"""variant_box.py — derive a state variant's composite region by DIFFING it against the base art.

WHY (Lucas, 2026-08-31): *"I want to avoid having to draw hotspot boxes."* For a state variant you never
have to. A variant panorama is the base scene with one thing changed — a door swung open, a beam laid
across the water — so **the region where the two images differ IS the region to composite**. It is
deterministic arithmetic, not a model call.

MEASURED against Lucas's own hand-drawn boxes on `wrangling/egypt/pharos`:

    lantern_door "open"          derived [0.438,0.139,0.548,0.763]  vs authored [0.443,0.142,0.543,0.754]  IoU 0.89
    harbour_below "beam_on_ship" derived [0.634,0.323,0.919,0.449]  vs authored [0.636,0.295,0.915,0.449]  IoU 0.80

i.e. IoU 0.89 and 0.80 — better than the vision-based hotspot localisation measured in
`notes/scenario_pipeline_vision.md` (0.83 on a prominent object, 0.39 and 0.21 on harder ones, two
outright misses), and with no API cost.

TWO SHAPES OF CHANGE, AND WHY THE MASK MATTERS MORE THAN THE BOX
The door change fills **97%** of its bounding rectangle: the box is an honest description of it. The beam
fills only **42%** — a light shaft across water is diffuse, so its rectangle sweeps in a lot of untouched
sea. Compositing that whole rectangle would replace pixels that never changed, which is exactly the
mistake `cinemagraph_tools/paste_tile.py` documents ("the tile rectangle is NOT the paste region"): a
first attempt there pasted everything that moved, including architecture the re-render had drawn
slightly differently, and the scene appeared to shift between frames.

So this returns BOTH: a `box` for schema/authoring use, and a `fill` telling you how honest that box is.
Below `SPARSE_FILL` the caller should composite the soft mask (`--mask-out`), not the rectangle.

WHAT IT DELIBERATELY DOES NOT DO
It does not decide whether a variant *should* exist, and it cannot invent a box for art that does not yet
exist — it needs both images. It is a measuring tool for already-generated variant art.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageFilter

# Per-pixel mean |RGB| difference above which a pixel counts as changed. 25/255 sits well clear of
# JPEG/PNG re-encode noise and of the 1-2 level dither two gpt-image renders differ by in flat sky,
# while still catching the beam's soft edge (which reads ~30-60 at its core).
DIFF_THRESHOLD = 25.0
# Ignore specks: a connected change smaller than this fraction of the frame is re-render noise, not a
# state change. Applied by an opening (erode->dilate) rather than true connected components, to stay
# dependency-free (no scipy).
MIN_BLOB_FRAC = 0.0002
# HYSTERESIS. A plain opening at one threshold erodes a DIFFUSE change: measured on the beam variant it
# pulled the extent in from y[0.283,0.472] to y[0.343,0.430] and dropped agreement with the authored box
# from 0.78 to 0.55. A hard object (the door) is unaffected because its edges are crisp. So find the
# CORE at the high threshold, then grow it back out over pixels that merely exceed this softer one —
# keeping faint tails that touch the core while still rejecting specks that stand alone.
SOFT_RATIO = 0.4
# Below this box-fill fraction the bounding rectangle is a poor description of the change and the
# caller should composite the MASK instead. The beam variant measured 0.42; the door 0.97.
SPARSE_FILL = 0.55


def _load(path, size=None):
    im = Image.open(path).convert("RGB")
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, dtype=np.float32)


def diff_mask(base_png, variant_png, threshold=DIFF_THRESHOLD):
    """Boolean changed-pixel mask, plus the raw per-pixel difference. The variant is resized to the
    base's dimensions first: an image-edit round trip does not always return the source size (the
    night route comes back 1536x1024 and is restretched), and comparing mismatched arrays would
    otherwise raise rather than degrade."""
    b = _load(base_png)
    v = _load(variant_png, size=(b.shape[1], b.shape[0]))
    d = np.abs(v - b).mean(axis=2)
    core = d > threshold
    # opening on the CORE only: drop isolated specks, then restore the survivors' extent
    k = max(1, int(round((core.shape[0] * core.shape[1] * MIN_BLOB_FRAC) ** 0.5 / 4)))
    if k > 1 and core.any():
        img = Image.fromarray((core * 255).astype(np.uint8), "L")
        img = img.filter(ImageFilter.MinFilter(2 * k + 1)).filter(ImageFilter.MaxFilter(2 * k + 1))
        core = np.asarray(img, dtype=np.uint8) > 127
    if not core.any():
        return core, d
    # Apply hysteresis ONLY to a diffuse change. Measured both ways on pharos: growing a CRISP change
    # (the door) over-expands it and agreement with the authored box falls 0.89 -> 0.76, while growing a
    # DIFFUSE one (the beam) recovers its tails and lifts agreement 0.55 -> 0.80. So decide from the
    # core's own box-fill — a crisp object fills its rectangle, a light shaft does not — and leave hard
    # edges alone.
    ys, xs = np.where(core)
    cfill = core[ys.min():ys.max() + 1, xs.min():xs.max() + 1].mean()
    if cfill >= SPARSE_FILL:
        return core, d
    grow = max(3, int(round(min(core.shape) * 0.02)))
    reach = np.asarray(Image.fromarray((core * 255).astype(np.uint8), "L")
                       .filter(ImageFilter.MaxFilter(2 * grow + 1)), dtype=np.uint8) > 127
    m = reach & (d > threshold * SOFT_RATIO)
    return m, d


def variant_box(base_png, variant_png, threshold=DIFF_THRESHOLD, pad=0.004):
    """Derive the composite region for a variant.

    Returns a dict:
        box        [x0,y0,x1,y1] image fractions, padded slightly (a hair generous is safe; a hair
                   tight leaves a seam of un-replaced base pixels along the object's edge)
        fill       fraction of that box that actually changed — how honest the rectangle is
        changed    fraction of the WHOLE frame that changed
        sparse     True when `fill` < SPARSE_FILL, i.e. composite the mask, not the rectangle
        touches_border  True if the change reaches the frame edge — the signature of a partially
                   cropped object (the same warning paste_tile.py raises), or of a whole-frame
                   restyle such as a night variant, which is not a box change at all
    """
    m, _d = diff_mask(base_png, variant_png, threshold)
    H, W = m.shape
    if not m.any():
        return {"box": None, "fill": 0.0, "changed": 0.0, "sparse": False,
                "touches_border": False, "note": "no change above threshold"}
    ys, xs = np.where(m)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    fill = float(m[y0:y1 + 1, x0:x1 + 1].mean())
    box = [max(0.0, x0 / W - pad), max(0.0, y0 / H - pad),
           min(1.0, (x1 + 1) / W + pad), min(1.0, (y1 + 1) / H + pad)]
    return {
        "box": [round(v, 4) for v in box],
        "fill": round(fill, 3),
        "changed": round(float(m.mean()), 4),
        "sparse": fill < SPARSE_FILL,
        "touches_border": bool(x0 == 0 or y0 == 0 or x1 == W - 1 or y1 == H - 1),
    }


def write_mask(base_png, variant_png, out_png, threshold=DIFF_THRESHOLD, feather=9):
    """Write the soft composite mask (white = take the VARIANT pixel). Feathered, because a hard edge
    cutting through a light shaft reads worse than a generous soft one — the same reasoning as
    `cinemagraph_tools/motion_mask.py`."""
    m, _ = diff_mask(base_png, variant_png, threshold)
    img = Image.fromarray((m * 255).astype(np.uint8), "L")
    if feather > 1:
        img = img.filter(ImageFilter.GaussianBlur(feather / 3.0))
    img.save(out_png)
    return out_png


def iou(a, b):
    """Overlap of two [x0,y0,x1,y1] boxes — used to compare a derived box against an authored one."""
    if not a or not b:
        return 0.0
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _main():
    ap = argparse.ArgumentParser(description="derive a variant's composite box by diffing it against the base")
    ap.add_argument("base_png")
    ap.add_argument("variant_png")
    ap.add_argument("--threshold", type=float, default=DIFF_THRESHOLD)
    ap.add_argument("--mask-out", default=None, help="also write the soft composite mask here")
    ap.add_argument("--compare", default=None, help="authored box as x0,y0,x1,y1 — reports IoU")
    a = ap.parse_args()
    r = variant_box(a.base_png, a.variant_png, a.threshold)
    if a.compare and r["box"]:
        r["authored"] = [float(x) for x in a.compare.split(",")]
        r["iou"] = round(iou(r["box"], r["authored"]), 3)
    if a.mask_out and r["box"]:
        r["mask"] = write_mask(a.base_png, a.variant_png, a.mask_out, a.threshold)
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
