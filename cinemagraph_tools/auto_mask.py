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


def drop_small(binary, min_px):
    """Delete connected components smaller than `min_px`, keeping the large coherent ones.

    THE REGION FILTER, and it answers a different question from the threshold. The percentile asks
    "how hard is this pixel moving"; it has no idea whether the pixel has any company. So a lone bright
    speckle on a wall survives p95 while a large, gently-moving banner falls out — which is the exact
    inversion of what the composite wants, because an isolated freed pixel reads as noise and a big
    moving object is the thing worth generating at all.

    Applied AFTER closing (so a dashed line of nearly-touching pixels counts as one region) and BEFORE
    hole-filling (so an object's own interior holes are not first filled and then measured as solid).

    Returns (binary, kept, dropped). `min_px <= 0` is a no-op, which is the default everywhere: this
    only bites when a clip's sidecar authored a region cut."""
    if min_px <= 0:
        return binary, None, 0
    lab, n = ndimage.label(binary)
    if n == 0:
        return binary, 0, 0
    sizes = ndimage.sum(binary, lab, range(1, n + 1))
    keep = np.zeros(n + 1, dtype=bool)
    keep[1:] = sizes >= min_px
    return keep[lab], int(keep[1:].sum()), int(n - keep[1:].sum())


def finish(binary, close_radius=4, feather=6, min_px=0):
    """Close, DROP SMALL REGIONS, FILL HOLES, feather — the shaping every mask gets, whichever way its
    threshold was picked. Returns (mask, {"kept", "dropped"}).

    ONE chain, used by BOTH the auto threshold and a hand-chosen one, so they cannot drift apart: a
    slider that skipped the hole-filling would preview a speckled object and a bake would ship a solid
    one, or the reverse. The fill is the important step — it solidifies a moving object WITHOUT lowering
    the threshold, which is what stops "complete objects" and "a tight threshold" being in conflict.

    Order is load-bearing: close BEFORE the region cut (so a dashed line of nearly-touching pixels counts
    as one region), and cut BEFORE the fill (so an object's own interior holes are not first filled and
    then measured as if they were solid area)."""
    b = ndimage.binary_closing(binary, structure=np.ones((close_radius, close_radius)))
    b, kept, dropped = drop_small(b, min_px)
    b = ndimage.binary_fill_holes(b)
    m = np.clip(ndimage.gaussian_filter(b.astype(np.float32), feather), 0, 1)
    return m, {"kept": kept, "dropped": dropped}


def mask_at_percentile(tstd, pct, close_radius=4, feather=6, min_px=0):
    """A mask at a HAND-CHOSEN percentile of the clip's own motion, shaped exactly like the auto one.

    Percentiles, not absolute temporal-std values: the absolute numbers differ per scene, so a fixed
    threshold that suits a canyon of white water is meaningless in a quiet interior. This is the same
    ladder `auto_mask` searches — the slider just picks a rung on it by eye instead of by solidity.

    `min_px` is the region cut (see `drop_small`) — the second, independent axis: the percentile says how
    hard a pixel must move, the region cut says how much company it must keep."""
    thr = float(np.percentile(tstd, pct))
    m, reg = finish(tstd > thr, close_radius, feather, min_px)
    return m, thr, float(m.mean()), reg


# ⚠️ THE CAP IS A BACKSTOP AND IT WAS NOT ENOUGH (2026-09-07). `coverage_cap=0.55` permits over half
# the frame to be generated video, and the ladder below scores candidates by object SOLIDITY — which a
# uniform frame-wide shimmer satisfies perfectly, because a boiling frame IS one big solid "object".
# So on the beacons corpus this settled at 60-90% coverage on clips with no local motion in them at
# all, and the shimmer it admitted is what `cine_judge.rigid_flicker` now convicts on.
#
# Simulated on three of those clips, the coverage that actually freezes the rigid frame is 4-7%, an
# order of magnitude tighter than what was shipped: ladder/base needs p93 (7% coverage) to take its
# rigid region to 0.00 while its waterfall keeps all 29.58 of its motion, and rams_head/base needs p96
# (4%). fenwatch/base has NO working rung — its mist dies at p90 and the stone only freezes at p96 —
# which is the signature of a clip with no local motion to protect, and no threshold can rescue one.
#
# The cap is NOT lowered here, deliberately. With STABILISER_TAIL no longer requesting whole-frame
# ambient motion, the tstd map should regain real structure and the solidity score should mean what it
# was designed to mean; lowering the cap now would be tuning against art that is about to be replaced,
# and a 0.55 cap is harmless on a clip whose motion is genuinely local. Re-measure coverage on the
# first re-rendered scenario, and if it is still running high, THAT is when to move this number.
def auto_mask(tstd, coverage_cap=0.55, close_radius=4, feather=6, min_frac=2e-4, min_px=0):
    """tstd: per-pixel temporal std (H,W). Returns (mask float 0..1, chosen threshold, report).

    TWO SIZE NUMBERS LIVE HERE AND THEY ARE NOT THE SAME THING — conflating them silently changes the
    confirmed auto behaviour, so they have different names:
      * `min_frac` -> `sol_px`, the floor for which components are "substantial" enough to be AVERAGED
        INTO the solidity score. Scoring only. Nothing is removed from the mask by it.
      * `min_px`, the caller's REGION CUT, which does remove components (`drop_small`). Default 0 =
        off, so auto keeps behaving exactly as Lucas confirmed unless a sidecar authored a cut."""
    H, W = tstd.shape
    sol_px = max(64, int(min_frac * H * W))
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
        sol, ncomp = _solidity(b, sol_px)
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
    m, reg = finish(tstd > thr, close_radius, feather, min_px)
    return m, thr, dict(threshold=thr, coverage=cov, solidity=sol,
                        components=ncomp, table=report,
                        kept=reg["kept"], dropped=reg["dropped"])
