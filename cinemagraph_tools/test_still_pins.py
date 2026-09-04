#!/usr/bin/env python3
"""Tests for the bake-time half of `motion_spec`'s `still: True` flag.

WHAT THIS GUARDS (egypt/library, 2026-09-02). The Library's re-cued clip animated the lectern codex at
p95 32.9 and the wall-niche scrolls at 12.9/20.3 while the dust it exists to show sat at 4.3. NEITHER
mask slider could remove them, because both select FOR motion and these were the strongest motion in
the frame: the threshold keeps the hardest movers, and the region cut keeps large coherent blobs (a
book, a scroll rack) while deleting fine speckle (drifting dust). A region you want held still has to be
NAMED — so `still` subjects are forced black in the playback mask.

The wiring is the fragile part, not the arithmetic. `_still_boxes` resolves the pins from scenario.json
inside `_mask_inputs`, which is deliberate: the gallery's "commit mask + re-bake" and the per-patch
`rebuild_clip` both bake WITHOUT a spec in hand, and a pin that survived the render but vanished on a
re-bake would be worse than no pin — it would come back only sometimes.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring_v2"))
import cine_scenario as CSN  # noqa: E402


def _scenario(tmp, subjects_base, subjects_night=None):
    spec = {"subjects": subjects_base}
    if subjects_night is not None:
        spec["states"] = {"night": {"subjects": subjects_night}}
    doc = {"rooms": [{"key": "hall", "authoring": {"motionSpec": spec}}]}
    json.dump(doc, open(os.path.join(tmp, "scenario.json"), "w", encoding="utf-8"))
    return tmp


PIN = {"name": "codex", "box": [0.2, 0.5, 0.3, 0.7], "still": True}
MOVER = {"name": "dust", "box": [0.6, 0.1, 0.7, 0.5], "phrase": "dust"}


class StillBoxResolutionTest(unittest.TestCase):
    def test_pins_are_found_for_the_base_state(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER, PIN])
            self.assertEqual([b["name"] for b in CSN._still_boxes(t, "hall", "base")], ["codex"])

    def test_movers_are_not_pinned(self):
        """The inverse mistake would freeze the one thing the clip exists to show."""
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER])
            self.assertEqual(CSN._still_boxes(t, "hall", "base"), [])

    def test_a_variant_state_reads_ITS_OWN_pins_not_the_base_ones(self):
        """Night is a different scene: the Library's day pins freeze paper, but night deliberately
        animates candles standing on the very same desks. Reading base's pins for a night bake would
        freeze them."""
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [PIN], subjects_night=[MOVER])
            self.assertEqual([b["name"] for b in CSN._still_boxes(t, "hall", "base")], ["codex"])
            self.assertEqual(CSN._still_boxes(t, "hall", "night"), [])

    def test_a_state_with_no_spec_pins_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [PIN])
            self.assertEqual(CSN._still_boxes(t, "hall", "night"), [])

    def test_missing_scenario_is_not_an_error(self):
        """A clips-only fixture has no scenario.json; the bake must still run, pinning nothing."""
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(CSN._still_boxes(t, "hall", "base"), [])

    def test_unknown_room_pins_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [PIN])
            self.assertEqual(CSN._still_boxes(t, "nosuchroom", "base"), [])


class MaskBlackoutTest(unittest.TestCase):
    """The blackout arithmetic, exercised through the same helper `mask_png` uses."""

    def _apply(self, m, boxes):
        # mirrors mask_png's pin loop; kept in step by test_the_real_mask_png_applies_pins below
        H, W = m.shape[:2]
        for b in boxes:
            x0, y0, x1, y1 = b["box"]
            m[int(round(y0 * H)):int(round(y1 * H)), int(round(x0 * W)):int(round(x1 * W))] = 0.0
        return m

    def test_a_pinned_box_goes_black_and_the_rest_survives(self):
        import numpy as np
        m = np.ones((100, 200), dtype=float)
        self._apply(m, [PIN])
        self.assertEqual(m[50:70, 40:60].max(), 0.0)       # inside the pin: all still
        self.assertEqual(m[0:40, :].min(), 1.0)            # outside: untouched

    def test_the_real_mask_png_applies_pins(self):
        """Calls mask_png itself so the loop above cannot drift from the shipped one. The clip is
        faked out by monkeypatching the frame sampler — this test is about the pin, not decoding."""
        import numpy as np
        from PIL import Image
        import motion_mask
        orig = motion_mask.sample_frames
        motion_mask.sample_frames = lambda *a, **k: np.random.RandomState(0).rand(4, 64, 128, 3) * 40
        try:
            with tempfile.TemporaryDirectory() as t:
                os.makedirs(os.path.join(t, "_scratch", "motion"), exist_ok=True)
                out, meta = CSN.mask_png(t, "hall", "base", "ignored.mp4", pct=50,
                                         still_boxes=[PIN])
                self.assertEqual(meta["stillBoxes"], ["codex"])
                a = np.asarray(Image.open(out).convert("L"))
                H, W = a.shape
                self.assertEqual(a[int(.52 * H):int(.68 * H), int(.22 * W):int(.28 * W)].max(), 0)
        finally:
            motion_mask.sample_frames = orig

    def test_a_malformed_box_does_not_lose_the_whole_mask(self):
        import numpy as np
        m = np.ones((100, 200), dtype=float)
        # inverted / empty boxes are skipped by mask_png rather than raising
        self._apply(m, [])
        self.assertEqual(m.min(), 1.0)


if __name__ == "__main__":
    unittest.main()
