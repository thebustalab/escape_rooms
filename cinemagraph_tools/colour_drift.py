#!/usr/bin/env python3
"""Mean-RGB drift across a clip — the defect Lucas spotted in K1 that every existing metric missed.

"In K1 the colors are changing strangely." Measured: K1 swings 14.6 RGB units, rising to +11.8 by
mid-clip and returning to +0.4 by the end. Every other clip we have made sits near 1.0.

Nothing we measured could see it. live%, band motion, incoherence, detail and the loop junction are
all computed from per-pixel VARIATION or gradients, and a slow global colour shift changes none of
them appreciably. It is the fifth defect class Lucas has caught that the metrics cannot: the
temporal cross-fade, the U4 ripple, C1's camera drift, dev's water texture ramp, and now this.

Reported as the max deviation of the frame's mean RGB from frame 0. Under ~2 is unnoticeable; K1's
14.6 reads as the scene visibly warming and brightening through the middle of the loop.
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image


def colour_drift(mp4):
    d = tempfile.mkdtemp(prefix="cc_", dir="/tmp/sweep")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "scale=384:128",
                        f"{d}/%04d.png"], check=True)
        fs = sorted(os.listdir(d))
        means = np.stack([np.asarray(Image.open(os.path.join(d, f)).convert("RGB"),
                                     dtype=np.float32).mean(axis=(0, 1)) for f in fs])
    finally:
        subprocess.run(["rm", "-rf", d], check=False)
    dev = means - means[0]
    return float(np.abs(dev).max()), means


if __name__ == "__main__":
    print(f"{'clip':<34} {'maxdRGB':>8}  verdict")
    print("-" * 62)
    for p in sys.argv[1:]:
        if not os.path.isfile(p):
            print(f"{os.path.basename(p):<34} {'--':>8}  missing"); continue
        mx, _ = colour_drift(p)
        v = "ok" if mx < 2 else ("noticeable" if mx < 5 else "BAD — visible colour swing")
        print(f"{os.path.basename(p):<34} {mx:8.2f}  {v}")
