#!/usr/bin/env python3
"""Deterministic NIGHT re-grade of a committed day panorama — no model involved.

Why not just generate night art? Every hotspot box in a room is stored as fractions of the panorama, and
a room has ONE set of boxes shared by day and night. So a night scene must keep the day scene's exact
composition or the doors, clues and puzzle land on the wrong objects after dark. A fresh generation drifts;
a local re-grade cannot, because it only changes pixel VALUES — never their positions.

The grade: scale everything down hard, push the shadows blue, then let pixels that are both bright AND
warm (lamps, braziers, fires) burn back through at close to full strength, so light sources survive as
pools instead of going flat grey. Gamma nudges the contrast back after the darkening.

Limitation, by construction: it can only darken what is there. It cannot ADD a light that the day image
doesn't contain — the Pharos crown, which should blaze after dark, comes out dimmed instead. Light that
needs adding is a small masked edit on that one box, not a whole-scene job.

    python3 night_grade.py <day.png> --out <night.png> [--strength 0.26] [--preview p.png]
"""
import argparse
import os

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def night(arr, strength=0.26, blue=1.55, green=1.12, lamp_keep=0.85, gamma=1.06):
    """day RGB float array in 0..1 -> night RGB float array in 0..1. Pure function, unit-testable."""
    lum = arr @ LUMA
    warm = np.clip((arr[..., 0] - arr[..., 2]) * 2.2, 0, 1)        # orange-ness: lamp/fire vs sky
    lamp = np.clip((lum - 0.55) / 0.45, 0, 1) * warm               # bright AND warm = a light source
    out = arr * strength
    out[..., 2] *= blue                                            # cool the shadows
    out[..., 1] *= green
    out = out + arr * lamp[..., None] * lamp_keep                  # lamps burn back through
    return np.clip(out, 0, 1) ** gamma


def grade_file(src, dst, strength=0.26, preview=None):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32) / 255.0
    out = (night(a, strength) * 255).astype(np.uint8)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    Image.fromarray(out).save(dst)
    if preview:
        Image.fromarray(out).resize((1200, max(1, round(1200 * im.height / im.width)))).save(preview)
    return {"src": src, "out": dst, "size": list(im.size)}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--strength", type=float, default=0.26, help="lower = darker night (default 0.26)")
    p.add_argument("--preview", help="also write a downscaled preview here")
    a = p.parse_args()
    print(grade_file(a.input, a.out, a.strength, a.preview))


if __name__ == "__main__":
    main()
