#!/usr/bin/env python3
"""Composite a repair TILE back into a full-frame cinemagraph, pasting the OBJECT, not the tile.

Lucas found the two failure modes of naive tiling immediately:
  "the awning moves but it wasn't selected in its entirety so the stitch would look weird"
  "part of the water is in their frame too, so a stitch could clash"

Both come from treating the tile rectangle as the paste region. It is not — the tile is a RENDERING
CONTEXT (it exists so the object dominates its frame and the model animates it), and the paste
region should be the OBJECT.

So:
  1. paste only where the TILE ITSELF MOVED — the tile's own per-pixel temporal std, thresholded.
     Content the tile happens to contain but did not animate (the water in the shrine tile, sky,
     stone) is simply never pasted, so it cannot clash with the base.
  2. optionally intersect with a caller-supplied region, when only part of what moved is wanted.
  3. FEATHER the edge, so the boundary falls where motion fades out rather than on a hard line.
  4. COLOUR-MATCH the tile to the base over the paste region before compositing — two independent
     renders drift apart in exposure, and a seam is far more visible as a brightness step than as
     a motion difference.

An object that extends beyond the tile still gets a visible discontinuity — half of it moving, half
static. That is a CROPPING error, not a compositing one: the tile must contain the whole object.
This script warns when the moving region touches the tile edge, which is the signature of it.
"""
import os, subprocess, argparse, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage


def frames(mp4):
    d = tempfile.mkdtemp(prefix="pt_", dir="/tmp")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, f"{d}/%04d.png"], check=True)
    return d, sorted(os.listdir(d))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("tile")
    ap.add_argument("--box", required=True, help="x0,y0,x1,y1 in BASE pixels")
    ap.add_argument("--out", required=True)
    ap.add_argument("--thresh", type=float, default=None, help="tstd cutoff; default = tile p70")
    ap.add_argument("--feather", type=int, default=24)
    ap.add_argument("--region", default=None,
                    help="x0,y0,x1,y1 in BASE px: paste ONLY inside this, intersected with the "
                         "tile's motion. Without it, everything the tile animated gets pasted — "
                         "including architecture the tile re-rendered slightly differently, which "
                         "reads as the building shifting.")
    ap.add_argument("--fps", type=float, default=24.0)
    a = ap.parse_args()
    x0, y0, x1, y1 = [int(v) for v in a.box.split(",")]

    bd, bf = frames(a.base)
    td, tf = frames(a.tile)
    n = min(len(bf), len(tf))
    bw, bh = Image.open(os.path.join(bd, bf[0])).size
    tw, th = x1 - x0, y1 - y0

    # where did the TILE actually move?
    ts = np.stack([np.asarray(Image.open(os.path.join(td, f)).convert("RGB"), dtype=np.float32)
                   for f in tf[::4]])
    tstd = ts.std(axis=0).mean(axis=2)
    thr = a.thresh if a.thresh is not None else float(np.percentile(tstd, 70))
    m = tstd > thr
    m = ndimage.binary_closing(m, np.ones((5, 5)))
    m = ndimage.binary_fill_holes(m)

    edge = (m[0, :].mean() + m[-1, :].mean() + m[:, 0].mean() + m[:, -1].mean()) / 4
    if edge > 0.10:
        print(f"  WARNING: the moving region touches the tile edge ({edge*100:.0f}% of the border). "
              f"The object probably extends beyond the crop — widen the tile, or the composite will "
              f"show half of it moving and half static.")

    if a.region:
        rx0, ry0, rx1, ry1 = [int(v) for v in a.region.split(",")]
        keep = np.zeros_like(m)
        sy, sx = m.shape[0] / (y1 - y0), m.shape[1] / (x1 - x0)
        keep[max(0, int((ry0 - y0) * sy)):int((ry1 - y0) * sy),
             max(0, int((rx0 - x0) * sx)):int((rx1 - x0) * sx)] = True
        m = m & keep
    mask = ndimage.gaussian_filter(m.astype(np.float32), a.feather)
    mask = np.clip(mask, 0, 1)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8)).resize((tw, th))
    mk = np.asarray(mask_img, dtype=np.float32)[:, :, None] / 255.0

    o = tempfile.mkdtemp(prefix="po_", dir="/tmp")
    for i in range(n):
        base = np.asarray(Image.open(os.path.join(bd, bf[i])).convert("RGB"), dtype=np.float32)
        tl = np.asarray(Image.open(os.path.join(td, tf[i])).convert("RGB").resize((tw, th)),
                        dtype=np.float32)
        region = base[y0:y1, x0:x1]
        # colour-match the tile to the base over the pasted area only
        w = mk[:, :, 0]
        if w.sum() > 1:
            bm = (region * w[:, :, None]).reshape(-1, 3).sum(0) / w.sum()
            tm = (tl * w[:, :, None]).reshape(-1, 3).sum(0) / w.sum()
            tl = tl * np.where(tm > 1e-3, bm / np.maximum(tm, 1e-3), 1.0)[None, None, :]
        base[y0:y1, x0:x1] = region * (1 - mk) + np.clip(tl, 0, 255) * mk
        Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).save(f"{o}/{i:04d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", f"{o}/%04d.png",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", a.out], check=True)
    subprocess.run(["rm", "-rf", bd, td, o], check=False)
    print(f"  pasted {float(mk.mean())*100:.1f}% of the tile area, threshold {thr:.2f} -> "
          f"{os.path.basename(a.out)}")


main()
