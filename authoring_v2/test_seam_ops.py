#!/usr/bin/env python3
"""Tests for seam_ops.py — the non-AI panorama seam repairs. Run: python3 test_seam_ops.py"""
import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seam_ops as so  # noqa: E402

W, H = 512, 128


def _pano(step=30.0, seed=0):
    """A textured panorama whose two ends differ by a constant tonal STEP — the real-world failure mode
    (measured on the committed trees/egypt panos: the seams are tonal, not structural)."""
    rng = np.random.default_rng(seed)
    base = rng.normal(128, 6, (H, W, 3)).astype(np.float32)
    base += np.linspace(0, 12, W, dtype=np.float32)[None, :, None]      # gentle scene gradient
    base[:, W // 2:, :] += step                                          # a tonal break; wraps as a seam
    return np.clip(base, 0, 255)


def _write(a):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "in.png")
    Image.fromarray(a.astype(np.uint8), "RGB").save(p)
    return p, os.path.join(d, "out.png")


class SeamOpsTest(unittest.TestCase):
    def test_gradient_collapses_the_seam_below_natural_detail(self):
        src, out = _write(_pano(step=30.0))
        before = so.measure(src)
        self.assertTrue(before["visible"], "fixture should start with a visible seam")
        r = so.gradient(src, out, span=48)
        after = so.measure(out)
        self.assertLess(after["seam"], before["seam"])
        self.assertLess(after["seam"], after["natural"], "seam must drop under the scene's own detail")
        self.assertEqual(r["op"], "gradient")

    def test_gradient_only_touches_the_span_around_the_seam(self):
        a = _pano(step=30.0)
        src, out = _write(a)
        so.gradient(src, out, span=32)
        got = np.asarray(Image.open(out).convert("RGB"), dtype=np.float32)
        middle = slice(60, W - 60)                       # well outside the 32-column span at each end
        self.assertLess(float(np.abs(got[:, middle, :] - a[:, middle, :]).max()), 1.5,
                        "pixels away from the seam must be untouched")

    def test_gradient_handles_a_MID_IMAGE_seam_via_pos(self):
        a = _pano(step=0.0)
        a[:, W // 3:, :] += 28.0                          # break at 1/3, not at the wrap
        src, out = _write(a)
        r = so.gradient(src, out, pos=1.0 / 3.0, span=40)
        self.assertEqual(r["seamColumn"], W // 3, "should snap to the real step, not the nominal pos")
        got = np.asarray(Image.open(out).convert("RGB"), dtype=np.float32)
        i = W // 3
        jump_before = float(np.abs(a[:, i, :] - a[:, i - 1, :]).mean())
        jump_after = float(np.abs(got[:, i, :] - got[:, i - 1, :]).mean())
        self.assertGreater(jump_before, 20)
        self.assertLess(jump_after, 2.0, "the mid-image step should be absorbed too")

    def test_crop_removes_the_edges_and_restores_full_width(self):
        src, out = _write(_pano(step=30.0))
        r = so.crop(src, out, frac=0.04)
        im = Image.open(out)
        self.assertEqual(im.size, (W, H), "must come back at full width")
        self.assertEqual(r["droppedEachEnd"], round(W * 0.04 / 2))

    def test_roll_moves_the_wrap_and_is_a_pure_rotation(self):
        a = _pano(step=0.0)
        a[:, 200:260, :] += np.linspace(0, 60, 60, dtype=np.float32)[None, :, None]   # a busy region
        src, out = _write(a)
        r = so.roll(src, out)
        got = np.asarray(Image.open(out).convert("RGB"), dtype=np.float32)
        self.assertEqual(got.shape, a.shape)
        src_px = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32)
        self.assertAlmostEqual(float(got.mean()), float(src_px.mean()), places=3)   # lossless rotation
        self.assertNotIn(r["column"], range(205, 255), "shouldn't pick the busiest region")

    def test_measure_reports_ratio_and_visibility(self):
        src, _ = _write(_pano(step=40.0))
        m = so.measure(src)
        self.assertGreater(m["ratio"], 1.0)
        self.assertTrue(m["visible"])

    def test_unknown_op_raises(self):
        src, out = _write(_pano())
        with self.assertRaises(ValueError):
            so.run("magic", src, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
