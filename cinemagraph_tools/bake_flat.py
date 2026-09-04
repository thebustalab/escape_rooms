#!/usr/bin/env python3
"""Bake a flat, self-contained loop: optional motion-mask composite + a crossfade at the join.

Two things that have only ever existed at PLAYBACK get baked into the file here, so the result can
be watched anywhere — phone, Quicktime, anything — with no viewer code:

  MASK COMPOSITE   show the generated video only where the scene should move, and the ORIGINAL
                   still everywhere else. This is the untried lever: at a low end-guide the model
                   produces far more life but the architecture drifts, and Lucas has rejected every
                   such clip for that reason. If the architecture is taken from the still, the
                   drift is not merely hidden - those pixels are never generated at all.

                   The mask comes from a STABLE clip's motion map, never the lively clip's own: a
                   drifting clip reads as "moving" everywhere, so its own map would free exactly
                   the regions we are trying to freeze.

  CROSSFADE        Lucas's preferred loop treatment, 0.5 s. The tail is dissolved into the head so
                   an ordinary loop plays seamlessly, and the clip shortens by the fade length.

  WRAP SEAM        (2026-08-31) The panorama's L/R join, repaired PER FRAME. Repairing the source
                   still is not enough and never was: LTX regenerates every pixel with no notion of
                   wrap continuity, so the discontinuity comes back in the video. Measured on canyon —
                   `j_c4` and `works` were both repaired to a seam of 0.00 before rendering and came
                   back at 8.33 and 3.66, the first WORSE than the 8.82 it started with. Lucas saw the
                   floodworks seam immediately. Done here because the frames are already decoded, so
                   it costs nothing extra, and it is the same pure-pixel gradient the still stage uses
                   (`seam_ops.gradient_arr`) — no model, no invented pixels.

Usage:
  bake_flat.py CLIP --out OUT.mp4 [--still S.png] [--mask M.png] [--fade 0.5] [--fps 24]
"""
import os, sys, subprocess, argparse, tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring_v2"))
import seam_ops  # noqa: E402


def frames_of(mp4):
    d = tempfile.mkdtemp(prefix="bk_", dir="/tmp/sweep")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, f"{d}/%04d.png"], check=True)
    fs = sorted(os.listdir(d))
    return d, fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--out", required=True)
    ap.add_argument("--still", default=None)
    ap.add_argument("--mask", default=None, help="greyscale: white = show the VIDEO")
    ap.add_argument("--fade", type=float, default=0.5)
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--seam", action="store_true",
                    help="repair the equirectangular L/R wrap seam on every frame (panoramas: yes)")
    ap.add_argument("--seam-span", type=int, default=64)
    a = ap.parse_args()

    d, fs = frames_of(a.clip)
    n = len(fs)
    W, H = Image.open(os.path.join(d, fs[0])).size
    still = mask = None
    if a.still and a.mask:
        still = np.asarray(Image.open(a.still).convert("RGB").resize((W, H)), dtype=np.float32)
        mask = np.asarray(Image.open(a.mask).convert("L").resize((W, H)),
                          dtype=np.float32)[:, :, None] / 255.0

    def frame(i):
        f = np.asarray(Image.open(os.path.join(d, fs[i])).convert("RGB"), dtype=np.float32)
        return f if mask is None else still * (1 - mask) + f * mask

    F = max(0, min(int(round(a.fade * a.fps)), n // 2 - 1))
    L = n - F                       # the baked loop is shorter by exactly the fade
    o = tempfile.mkdtemp(prefix="bo_", dir="/tmp/sweep")
    seam_before, seam_after = [], []
    for i in range(L):
        if i < F:
            # dissolve the tail into the head: at i=0 this is almost entirely the OLD last frame,
            # so the wrap lands on a near-identical pair; by i=F it is entirely the head.
            w = (i + 1) / (F + 1)
            img = w * frame(i) + (1 - w) * frame(L + i)
        else:
            img = frame(i)
        if a.seam:
            # AFTER the dissolve, never before: the crossfade mixes two frames whose seams differ, so
            # repairing first would leave the blend with a fresh step of its own.
            img, info = seam_ops.gradient_arr(img, span=a.seam_span)
            seam_before.append(info["seamBefore"]); seam_after.append(info["seamAfter"])
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f"{o}/{i:04d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", f"{o}/%04d.png",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", a.out], check=True)
    subprocess.run(["rm", "-rf", d, o], check=False)
    seam_note = ""
    if a.seam and seam_before:
        seam_note = (f"  seam {sum(seam_before)/len(seam_before):.2f} -> "
                     f"{sum(seam_after)/len(seam_after):.2f} (mean over {len(seam_before)} frames)")
    print(f"  {os.path.basename(a.out):<44} {n} -> {L} frames"
          f"{'  (masked)' if mask is not None else ''}  fade {F} frames{seam_note}")


main()
