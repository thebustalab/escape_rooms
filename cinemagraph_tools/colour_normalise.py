#!/usr/bin/env python3
"""Remove a slow global colour/brightness drift from a clip, in post.

Longer clips at full resolution (97 frames @ 3072x1024) are clean on every measure EXCEPT a smooth
warm/bright arc through the middle of the loop — measured 7.8 to 14.6 units against ~1.0 for every
73-frame clip. Detail is unaffected: 97f scores 12.30-12.76 against 73f's 12.40-12.57, i.e. there is
NO resolution or sharpness cost at 97 frames. The colour swing is the only defect.

That defect is a *global* per-frame shift, which makes it removable after the fact: rescale each
frame so its channel means match frame 0. If it works, 33% more clip length becomes available at
full resolution.

Deliberately GAIN-based (multiplicative) rather than additive: an additive shift crushes blacks and
lifts them unevenly, whereas scaling preserves the ratio structure of the image, which is what
"the light changed" actually does.

NOTE — this cannot fix the small wiggle in supposedly-static pixels. That is LOCAL, per-pixel and
uncorrelated; a global gain moves every pixel of a frame together and leaves it untouched. The
post-processing mask is the tool for that.
"""
import os, subprocess, argparse, tempfile
import numpy as np
from PIL import Image


def normalise(src, dst, strength=1.0):
    d = tempfile.mkdtemp(prefix="cn_", dir="/tmp")
    o = tempfile.mkdtemp(prefix="co_", dir="/tmp")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, f"{d}/%04d.png"], check=True)
        fs = sorted(os.listdir(d))
        ref = None
        drift = []
        for i, f in enumerate(fs):
            a = np.asarray(Image.open(os.path.join(d, f)).convert("RGB"), dtype=np.float32)
            mean = a.reshape(-1, 3).mean(axis=0)
            if ref is None:
                ref = mean
            gain = np.where(mean > 1e-3, ref / np.maximum(mean, 1e-3), 1.0)
            gain = 1.0 + strength * (gain - 1.0)      # strength<1 for a partial correction
            drift.append(float(np.abs(mean - ref).max()))
            out = np.clip(a * gain[None, None, :], 0, 255).astype(np.uint8)
            Image.fromarray(out).save(f"{o}/{i:04d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", f"{o}/%04d.png",
                        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", dst], check=True)
        return max(drift), len(fs)
    finally:
        subprocess.run(["rm", "-rf", d, o], check=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("--out", required=True)
    ap.add_argument("--strength", type=float, default=1.0)
    a = ap.parse_args()
    mx, n = normalise(a.src, a.out, a.strength)
    print(f"  {os.path.basename(a.src)} -> {os.path.basename(a.out)}  "
          f"{n} frames, input drift was {mx:.2f}")
