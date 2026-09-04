#!/usr/bin/env python3
"""Regression tests for the playback motion mask's TWO axes.

The failure these pin: the `thresh` slider is a percentile of temporal std, and a percentile has no
idea whether a moving pixel has any neighbours. So a lone bright speckle on a wall outlives p95 while
a large, gently-moving object falls out — backwards, because an isolated freed pixel reads as noise
and the big mover is the reason to generate anything at all. `drop_small` is the second axis, and
these tests hold it to: it removes the speckle, it keeps the large region, it is OFF by default, and
it does not silently change the confirmed `auto` behaviour.
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auto_mask import auto_mask, drop_small, finish, mask_at_percentile  # noqa: E402


def _scene(seed=0):
    """A quiet frame with ONE large coherent mover and a scatter of one-off hot pixels."""
    rng = np.random.default_rng(seed)
    t = (rng.random((200, 400)) * 2).astype(np.float32)
    t[60:110, 120:260] += 18                 # 7000 px of genuine, connected motion
    for _ in range(60):                      # isolated speckle, individually BRIGHTER than the mover
        y, x = int(rng.integers(3, 197)), int(rng.integers(3, 397))
        t[y:y + 2, x:x + 2] += 22
    return t


class RegionCut(unittest.TestCase):
    def test_off_by_default(self):
        """min_px=0 is a no-op — the confirmed percentile behaviour must be untouched unless authored."""
        b = np.zeros((20, 20), bool); b[0, 0] = True
        out, kept, dropped = drop_small(b, 0)
        self.assertTrue(out[0, 0])
        self.assertEqual((kept, dropped), (None, 0))

    def test_drops_speckle_keeps_the_big_mover(self):
        t = _scene()
        _, _, cov0, r0 = mask_at_percentile(t, 90, min_px=0)
        _, _, cov1, r1 = mask_at_percentile(t, 90, min_px=200)
        self.assertEqual(r0["dropped"], 0)             # no cut -> nothing removed
        self.assertGreater(r1["dropped"], 100)         # the scatter goes
        self.assertEqual(r1["kept"], 1)                # the mover stays
        self.assertLess(cov1, cov0)                    # and coverage falls, not rises

    def test_the_survivor_is_the_LARGE_region_not_the_brightest(self):
        """The point of the axis. The speckle is brighter than the mover; size must decide, not heat."""
        t = _scene()
        m, _, _, _ = mask_at_percentile(t, 90, min_px=200)
        self.assertGreater(m[60:110, 120:260].mean(), 0.8)   # mover is on
        corner = m[0:40, 300:400]                             # a region with only speckle
        self.assertLess(corner.mean(), 0.2)

    def test_monotone_in_the_cut(self):
        t = _scene()
        covs = [mask_at_percentile(t, 90, min_px=p)[2] for p in (0, 100, 1000, 20000)]
        self.assertEqual(covs, sorted(covs, reverse=True))

    def test_auto_is_unchanged_when_no_cut_is_authored(self):
        """`min_frac` (the solidity SCORING floor) and `min_px` (the region CUT) are different numbers.
        Conflating them silently turned auto into a 629 px cut on every clip."""
        t = _scene()
        m_a, thr_a, rep_a = auto_mask(t)
        m_b, thr_b, rep_b = auto_mask(t, min_px=0)
        self.assertEqual(thr_a, thr_b)
        np.testing.assert_allclose(m_a, m_b)
        self.assertIsNone(rep_a["kept"])               # nothing was cut
        self.assertEqual(rep_a["dropped"], 0)

    def test_finish_reports_and_is_the_one_chain(self):
        """`finish` is shared by auto and hand-picked so a preview and a bake cannot drift apart."""
        t = _scene()
        thr = float(np.percentile(t, 90))
        m1, reg1 = finish(t > thr, min_px=200)
        m2, _, _, reg2 = mask_at_percentile(t, 90, min_px=200)
        np.testing.assert_allclose(m1, m2)
        self.assertEqual(reg1, reg2)


if __name__ == "__main__":
    unittest.main()
