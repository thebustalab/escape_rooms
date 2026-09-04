#!/usr/bin/env python3
"""Derive a per-pixel MOTION MASK from a clip's own movement, not from authored hotspot boxes.

Lucas's idea: show the generated video only where it actually moves, and the ORIGINAL still
everywhere else. That is the classic cinemagraph construction, and it fixes several things at once:

  * static regions keep the source panorama's full detail — no generative softening, no drift,
    no invented content, because those pixels are never generated at all;
  * the region is derived per clip, so it needs no authoring and adapts to whatever the model
    actually animated;
  * a clip that drifts slightly in the architecture stops mattering, because the architecture is
    taken from the still.

Method: sample frames, take per-pixel temporal standard deviation, then map it through a SOFT ramp
(lo -> transparent, hi -> opaque) rather than a hard threshold, so edges of moving regions blend
instead of cutting. Dilate slightly and blur, because a hard mask edge cutting through moving water
reads worse than a generous soft one.

Writes a greyscale PNG the viewer multiplies the video against.
"""
import os, sys, subprocess, argparse
import numpy as np
from PIL import Image, ImageFilter


def clip_frames(mp4):
    """Actual frame count. The stride below was hardcoded to 73 — our old clip length — so a
    169-frame clip sampled only its first third and any motion late in the clip was invisible to
    the mask. Ask the file instead of assuming."""
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                              "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", mp4],
                             capture_output=True, text=True, check=True).stdout.strip()
        return max(1, int(out.split(",")[0]))
    except Exception:
        return 73


def sample_frames(mp4, n=16):
    # Unique scratch dir per call: a FIXED path meant two concurrent callers (the auto-register
    # watcher and a manual run) deleted each other's frames mid-extract, and the second one died
    # on a missing file. Any of these helpers can now run in parallel safely.
    import tempfile
    d = tempfile.mkdtemp(prefix="mm_", dir="/tmp/sweep")
    # Spread the samples across the WHOLE clip: motion that only happens late still counts.
    total = clip_frames(mp4)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf",
                    f"select='not(mod(n\\,{max(1, total // n)}))'", "-vsync", "0",
                    f"{d}/%03d.png"], check=True)
    fs = sorted(os.listdir(d))[:n]
    ims = [np.asarray(Image.open(os.path.join(d, f)).convert("RGB"), dtype=np.float32) for f in fs]
    subprocess.run(["rm", "-rf", d], check=False)
    return np.stack(ims)


def mask_from_tstd(tstd, lo=3.0, hi=12.0, dilate=9, blur=21, floor=0.0):
    """The mask itself, from an ALREADY-COMPUTED temporal-std map.

    Split out from `motion_mask` so a caller that already has the tstd — the harness, serving live
    threshold previews — runs the exact same ramp, dilate and blur as a bake would, instead of an
    approximation. A preview that merely resembles the bake is worse than none: thresholds get chosen
    against it. An in-browser emulation was tried first and reported ~1/3 of the real coverage
    (2026-08-31), which is precisely the kind of number you would trust and be misled by."""
    a = np.clip((tstd - lo) / max(1e-6, hi - lo), 0, 1)     # soft ramp, not a hard threshold
    m = Image.fromarray((a * 255).astype(np.uint8), "L")
    if dilate > 1:
        m = m.filter(ImageFilter.MaxFilter(dilate if dilate % 2 else dilate + 1))
    if blur > 0:
        m = m.filter(ImageFilter.GaussianBlur(radius=blur))
    if floor > 0:
        arr = np.asarray(m, dtype=np.float32) / 255.0
        arr = floor + (1 - floor) * arr
        m = Image.fromarray((arr * 255).astype(np.uint8), "L")
    cov = float((np.asarray(m, dtype=np.float32) / 255.0).mean() * 100)
    return m, cov


def motion_mask(mp4, lo=3.0, hi=12.0, dilate=9, blur=21, floor=0.0):
    """lo/hi: temporal-std values mapping to fully still / fully moving.
    dilate+blur: grow and soften, so the boundary never cuts a hard edge through moving water.
    floor: minimum alpha everywhere (0 = pure still outside motion; try 0.15 for a subtle base)."""
    st = sample_frames(mp4)
    tstd = st.std(axis=0).mean(axis=2)                      # H,W  per-pixel temporal variation
    m, cov = mask_from_tstd(tstd, lo, hi, dilate, blur, floor)
    return m, cov, tstd


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--lo", type=float, default=3.0)
    ap.add_argument("--hi", type=float, default=12.0)
    ap.add_argument("--dilate", type=int, default=9)
    ap.add_argument("--blur", type=int, default=21)
    ap.add_argument("--floor", type=float, default=0.0)
    ap.add_argument("--out", default=None, help="output dir (default: alongside each clip)")
    a = ap.parse_args()
    for c in a.clips:
        m, cov, tstd = motion_mask(c, a.lo, a.hi, a.dilate, a.blur, a.floor)
        d = a.out or os.path.dirname(c)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, os.path.splitext(os.path.basename(c))[0] + "_mask.png")
        m.save(dst)
        print(f"{os.path.basename(c):<46} coverage={cov:5.1f}%  "
              f"tstd p50={np.percentile(tstd,50):5.2f} p95={np.percentile(tstd,95):5.2f}  -> "
              f"{os.path.basename(dst)}")
