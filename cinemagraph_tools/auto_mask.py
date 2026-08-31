#!/usr/bin/env python3
"""Choose the post-processing mask threshold automatically, by OBJECT COMPLETENESS.

This is the mask Lucas actually uses: after generation, show the clip where it genuinely moves and
the ORIGINAL still everywhere else. It exists to kill the small wiggle in pixels that should be
static — present to some degree in every raw render.

The viewer's current `auto` button is purely distributional: `THR = p75` of the clip's own temporal
std, i.e. "keep the moving quarter". That is per-clip, but it knows nothing about SHAPE, and shape
is what Lucas actually optimises by hand:

    "if there were objects that were clearly supposed to be animated, but substantial portions of
     those objects were masked, that would lead to weird visual artifacts, because you'd get this
     object that was patterned with moving and non-moving regions, and it looked strange... changing
     the threshold so that the major moving objects were more or less complete, that was a good way
     to get the cinemagraphs looking good."

So the criterion is not "what fraction of pixels" but "are the moving objects SOLID".

Two mechanisms, and the second is what breaks the trade-off:

  1. score candidate thresholds by SOLIDITY — for the largest connected components of the mask,
     what fraction of each component's filled area is actually on. A speckled object scores low.
  2. FILL HOLES inside each component before feathering. Lowering the threshold to solidify an
     object also drags in static background; filling its interior holes solidifies it WITHOUT
     lowering the threshold, so a high threshold and complete objects stop being in conflict.

Returns a float mask (1 = show the video) ready for bake_flat.py --mask.
"""
import numpy as np
from scipy import ndimage


def _solidity(binary, min_px):
    """Mean fill-fraction of the substantial connected components: 1.0 = perfectly solid."""
    lab, n = ndimage.label(binary)
    if n == 0:
        return 0.0, 0
    sizes = ndimage.sum(binary, lab, range(1, n + 1))
    big = [i + 1 for i, s in enumerate(sizes) if s >= min_px]
    if not big:
        return 0.0, 0
    scores = []
    for i in big:
        comp = lab == i
        filled = ndimage.binary_fill_holes(comp)
        scores.append(comp.sum() / max(filled.sum(), 1))
    return float(np.mean(scores)), len(big)


def auto_mask(tstd, coverage_cap=0.55, close_radius=4, feather=6, min_frac=2e-4):
    """tstd: per-pixel temporal std (H,W). Returns (mask float 0..1, chosen threshold, report)."""
    H, W = tstd.shape
    min_px = max(64, int(min_frac * H * W))
    # candidates spanning the clip's own distribution — absolute values differ per scene, so
    # percentiles are the only portable ladder
    cands = [float(np.percentile(tstd, p)) for p in range(50, 96, 5)]
    best = None
    report = []
    for thr in cands:
        b = tstd > thr
        cov = b.mean()
        if cov > coverage_cap:            # too much of the frame: static regions are getting in
            report.append((thr, cov, None)); continue
        b = ndimage.binary_closing(b, structure=np.ones((close_radius, close_radius)))
        sol, ncomp = _solidity(b, min_px)
        report.append((thr, cov, sol))
        # prefer solid objects; among similar solidity prefer MORE coverage, since a mask that is
        # solid only because it kept one blob is not what we want
        score = sol + 0.15 * min(cov / coverage_cap, 1.0)
        if ncomp and (best is None or score > best[0]):
            best = (score, thr, sol, cov, ncomp)
    if best is None:                      # degenerate scene (e.g. an interior that barely moves)
        thr = float(np.percentile(tstd, 85))
        best = (0.0, thr, 0.0, float((tstd > thr).mean()), 0)

    _, thr, sol, cov, ncomp = best
    b = tstd > thr
    b = ndimage.binary_closing(b, structure=np.ones((close_radius, close_radius)))
    # fill interior holes so a moving object is not patterned with static speckles
    b = ndimage.binary_fill_holes(b)
    m = ndimage.gaussian_filter(b.astype(np.float32), feather)
    return np.clip(m, 0, 1), thr, dict(threshold=thr, coverage=cov, solidity=sol,
                                       components=ncomp, table=report)
