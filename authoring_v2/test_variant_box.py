#!/usr/bin/env python3
"""Tests for variant_box.py — deriving a state variant's composite region by diffing it against the base.

The point of the module is that an author never has to DRAW a variant's box: the two images say where
they differ. These pin the two shapes of change that behave differently, because a single filter cannot
serve both — measured on the real pharos art, growing a crisp change costs accuracy (0.89 -> 0.76) while
growing a diffuse one gains it (0.55 -> 0.80).
"""
import os
import tempfile
import unittest

import numpy as np
from PIL import Image

from variant_box import variant_box, iou, SPARSE_FILL


def _write(arr, path):
    Image.fromarray(arr.astype(np.uint8), "RGB").save(path)
    return path


def _scene(h=240, w=720, val=60):
    return np.full((h, w, 3), val, dtype=np.uint8)


class VariantBoxTest(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="vbox_")

    def test_crisp_rectangle_is_found_tightly(self):
        """A hard-edged change (a door) should yield a tight, honest box: high fill, not sparse."""
        base = _scene()
        var = base.copy()
        var[60:180, 300:360] = 230                      # a bright vertical slab
        b = _write(base, os.path.join(self.d, "b.png"))
        v = _write(var, os.path.join(self.d, "v.png"))
        r = variant_box(b, v)
        self.assertFalse(r["sparse"])
        self.assertGreater(r["fill"], 0.85)
        # the true box in fractions, with the module's small pad allowed for
        self.assertGreater(iou(r["box"], [300 / 720, 60 / 240, 360 / 720, 180 / 240]), 0.75)

    def test_diffuse_change_is_flagged_sparse(self):
        """A soft, scattered change (a light beam) fills little of its rectangle. The caller must be
        told, because compositing the whole rectangle would replace pixels that never changed —
        the mistake paste_tile.py documents."""
        base = _scene()
        var = base.copy()
        rng = np.random.default_rng(0)
        ys = rng.integers(80, 160, 400)
        xs = rng.integers(200, 600, 400)
        for y, x in zip(ys, xs):
            var[y:y + 2, x:x + 2] = 200
        b = _write(base, os.path.join(self.d, "b2.png"))
        v = _write(var, os.path.join(self.d, "v2.png"))
        r = variant_box(b, v)
        self.assertTrue(r["sparse"])
        self.assertLess(r["fill"], SPARSE_FILL)

    def test_identical_images_report_no_change(self):
        base = _scene()
        b = _write(base, os.path.join(self.d, "b3.png"))
        v = _write(base.copy(), os.path.join(self.d, "v3.png"))
        r = variant_box(b, v)
        self.assertIsNone(r["box"])
        self.assertEqual(r["changed"], 0.0)

    def test_encode_noise_does_not_register_as_a_change(self):
        """Two renders of the same scene differ by a level or two in flat areas. That must not be
        mistaken for a state change, or every variant would derive a full-frame box."""
        base = _scene()
        var = base.astype(np.int16) + np.random.default_rng(1).integers(-2, 3, base.shape)
        b = _write(base, os.path.join(self.d, "b4.png"))
        v = _write(np.clip(var, 0, 255), os.path.join(self.d, "v4.png"))
        r = variant_box(b, v)
        self.assertIsNone(r["box"], "encode noise was treated as a change")

    def test_full_frame_change_touches_the_border(self):
        """A night restyle changes everything. `touches_border` is how the caller tells that apart
        from a box variant — it is a full-scene state, not something to composite into a rectangle."""
        base = _scene(val=60)
        var = _scene(val=200)
        b = _write(base, os.path.join(self.d, "b5.png"))
        v = _write(var, os.path.join(self.d, "v5.png"))
        r = variant_box(b, v)
        self.assertTrue(r["touches_border"])
        self.assertGreater(r["changed"], 0.9)

    def test_size_mismatch_is_handled_not_raised(self):
        """An image-edit round trip does not always return the source size (the night route comes back
        1536x1024 and is restretched). Comparing mismatched arrays must degrade, not raise."""
        base = _scene(240, 720)
        var = np.array(Image.fromarray(_scene(240, 720)).resize((360, 120)))
        var[30:90, 150:180] = 230
        b = _write(base, os.path.join(self.d, "b6.png"))
        v = _write(var, os.path.join(self.d, "v6.png"))
        r = variant_box(b, v)          # must not raise
        self.assertIsNotNone(r["box"])

    def test_iou_of_disjoint_boxes_is_zero(self):
        self.assertEqual(iou([0, 0, 0.1, 0.1], [0.5, 0.5, 0.6, 0.6]), 0.0)


if __name__ == "__main__":
    unittest.main()
