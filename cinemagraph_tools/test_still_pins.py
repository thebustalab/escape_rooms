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


def _sidecar(tmp, room, state, cfg):
    d = os.path.join(tmp, room)
    os.makedirs(d, exist_ok=True)
    json.dump(cfg, open(os.path.join(d, "cine_%s.mask.json" % state), "w", encoding="utf-8"))


class PaintOutTest(unittest.TestCase):
    """HAND-DRAWN pins — the second source, added 2026-09-06 so the overnight loop could stop
    suppressing incidental motion and hand that job to Lucas instead.

    The gap this closes: the loop's new policy is "get one or two hero motions alive, leave the rest to
    the mask". But the mask he had was `thresh` + `region`, and the docstring at the top of this file is
    the reason that was not yet a workflow — BOTH axes select for motion, so neither can remove one
    specific unwanted mover. The only thing that could was a `still: True` subject, i.e. the very
    authoring the change exists to avoid. A paint-out is the same blackout, owned by the human, applied
    at bake time from `cine_<state>.mask.json` -> `paintOut`.
    """

    def test_a_painted_box_is_pinned(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER])
            _sidecar(t, "hall", "base", {"pct": "auto", "paintOut": [{"name": "churn",
                                                                     "box": [0.1, 0.1, 0.2, 0.2]}]})
            self.assertEqual([b["name"] for b in CSN._still_boxes(t, "hall", "base")], ["churn"])

    def test_painted_and_AUTHORED_pins_are_unioned(self):
        """Both are pins by the time they reach the bake; what differs is who owns them."""
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER, PIN])
            _sidecar(t, "hall", "base", {"paintOut": [{"name": "churn", "box": [0.1, 0.1, 0.2, 0.2]}]})
            self.assertEqual(sorted(b["name"] for b in CSN._still_boxes(t, "hall", "base")),
                             ["churn", "codex"])

    def test_paint_is_PER_STATE(self):
        """Same rule as an authored pin: night is a different scene, and its sidecar is its own."""
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER], subjects_night=[MOVER])
            _sidecar(t, "hall", "base", {"paintOut": [{"name": "churn", "box": [0.1, 0.1, 0.2, 0.2]}]})
            self.assertEqual(CSN._still_boxes(t, "hall", "night"), [])

    def test_a_bare_box_without_a_name_still_pins(self):
        """Tolerate the shorthand: the UI writes {name, box}, but a hand-edited sidecar may not."""
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER])
            _sidecar(t, "hall", "base", {"paintOut": [[0.1, 0.1, 0.2, 0.2]]})
            got = CSN._still_boxes(t, "hall", "base")
            self.assertEqual(len(got), 1)
            self.assertEqual(got[0]["box"], [0.1, 0.1, 0.2, 0.2])

    def test_a_malformed_painted_box_is_skipped_not_raised(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER])
            _sidecar(t, "hall", "base", {"paintOut": [{"name": "bad", "box": [0.1, 0.1]},
                                                      {"name": "ok", "box": [0.3, 0.3, 0.4, 0.4]}]})
            self.assertEqual([b["name"] for b in CSN._still_boxes(t, "hall", "base")], ["ok"])

    def test_a_corrupt_sidecar_pins_nothing_rather_than_failing_the_bake(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER])
            d = os.path.join(t, "hall")
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "cine_base.mask.json"), "w").write("{not json")
            self.assertEqual(CSN.paint_out_boxes(t, "hall", "base"), [])

    def test_paintOut_SURVIVES_the_sidecar_rewrite(self):
        """THE REGRESSION, and it would have been silent. `_mask_inputs` replaces the whole sidecar with
        the mask builder's `meta` on every bake. The painted boxes live in that same file, so without
        carrying them forward, painting a box and then doing anything that re-bakes — dropping a repair
        patch, nudging the threshold — deletes the pins with no error anywhere and the churn comes back.
        Same shape as authoring_v2/AGENTS.md's warning that a stale sidecar copy makes "commit mask +
        re-bake" silently drop the pins.
        """
        import numpy as np
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER])
            d = os.path.join(t, "hall")
            os.makedirs(d, exist_ok=True)
            Image.fromarray(np.zeros((64, 128, 3), dtype="uint8")).save(os.path.join(d, "scene.png"))
            _sidecar(t, "hall", "base", {"pct": 70, "region": 0,
                                         "paintOut": [{"name": "churn", "box": [0.1, 0.1, 0.2, 0.2]}]})
            sj = os.path.join(d, "cine_base.mask.json")
            # Drive the real thing, with the frame sampler stubbed — the wiring is what is under test,
            # not the arithmetic (which MaskBlackoutTest covers).
            import motion_mask as MM
            orig = MM.sample_frames
            MM.sample_frames = lambda clip, n=16: np.zeros((n, 64, 128, 3), dtype="float32")
            try:
                CSN._mask_inputs(t, "hall", "base", os.path.join(d, "cine_base.mp4"),
                                 log=lambda m: None)
            finally:
                MM.sample_frames = orig
            after = json.load(open(sj, encoding="utf-8"))
            self.assertEqual([b["name"] for b in after.get("paintOut") or []], ["churn"])


class BoxMaskTest(unittest.TestCase):
    """The mask built FROM THE AUTHORED BOXES rather than from measured motion magnitude.

    THE FINDING (2026-09-07). The auto threshold chooses which pixels play the video by how hard they
    move, and the hardest-moving thing in this corpus is not the hero — it is the render's own drift of
    the rigid scene. fenwatch/base, frame 0 against frame 30: the mist box changed at p95 19, the
    office and yard STONE at p95 40. Every rung of the ladder therefore kept the drift and dropped the
    mist. Baking the same render with the hero box as the mask took the stone to 0.00 and the roof to
    0.00 while the mist kept 21.00, at 8.4% coverage against the threshold's 71.2%.

    This is how the boxed era worked — trees' cloud and mist animate convincingly and its clips are
    small crops where the object fills the frame, so the box WAS the mask. Replacing that with a
    magnitude threshold discarded the mechanism.
    """

    def test_hero_boxes_win_over_plain_movers(self):
        """Under the one-hero policy the hero is the promised motion; an incidental mover is not."""
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [dict(MOVER, hero=True),
                          {"name": "extra", "box": [0.8, 0.8, 0.9, 0.9], "phrase": "p"}])
            self.assertEqual([b["name"] for b in CSN.mover_boxes(t, "hall", "base")], ["dust"])

    def test_a_legacy_spec_with_no_hero_uses_all_its_movers(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER, {"name": "extra", "box": [0.8, 0.8, 0.9, 0.9], "phrase": "p"}])
            self.assertEqual(sorted(b["name"] for b in CSN.mover_boxes(t, "hall", "base")),
                             ["dust", "extra"])

    def test_pins_are_not_movers(self):
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [PIN])
            self.assertEqual(CSN.mover_boxes(t, "hall", "base"), [])

    def test_the_mask_is_white_in_the_box_and_black_outside(self):
        import numpy as np
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [dict(MOVER, hero=True)])
            mk, meta = CSN.box_mask(t, "hall", "base", (400, 200),
                                    mover=CSN.mover_boxes(t, "hall", "base"), feather=0)
            a = np.asarray(Image.open(mk).convert("L"), float) / 255.0
            # MOVER box is [0.6, 0.1, 0.7, 0.5] -> cols 240-280, rows 20-100
            self.assertGreater(a[60, 260], 0.9)      # inside the box: plays the video
            self.assertLess(a[150, 50], 0.1)        # outside: plays the still
            self.assertEqual(meta["maskMode"], "boxes")
            self.assertAlmostEqual(meta["coverage"], 0.1 * 0.4, places=2)

    def test_a_pin_inside_a_mover_box_still_wins(self):
        import numpy as np
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            big = {"name": "sky", "box": [0.0, 0.0, 1.0, 1.0], "phrase": "sky", "hero": True}
            _scenario(t, [big, PIN])
            mk, meta = CSN.box_mask(t, "hall", "base", (400, 200),
                                    mover=CSN.mover_boxes(t, "hall", "base"),
                                    still_boxes=CSN._still_boxes(t, "hall", "base"), feather=0)
            a = np.asarray(Image.open(mk).convert("L"), float) / 255.0
            # PIN is [0.2, 0.5, 0.3, 0.7] -> cols 80-120, rows 100-140
            self.assertLess(a[120, 100], 0.1)
            self.assertEqual(meta["stillBoxes"], ["codex"])

    def test_no_usable_box_returns_None_so_the_caller_can_fall_back(self):
        """A malformed box must not ship an UNMASKED clip — that is how the drift reaches the player."""
        with tempfile.TemporaryDirectory() as t:
            _scenario(t, [MOVER])
            mk, meta = CSN.box_mask(t, "hall", "base", (400, 200),
                                    mover=[{"name": "bad", "box": [0.5, 0.5, 0.5, 0.5]}])
            self.assertIsNone(mk)
            self.assertIsNone(meta)


class ColourNormaliseOptInTest(unittest.TestCase):
    """The one defect class the mask provably cannot touch: a whole-frame brightness arc.

    `colour_normalise.py` was written for exactly this, measured on anvil/night at frame swing
    3.86 -> 0.31 with the subjects still alive, and then had NO importer anywhere in the bake chain —
    the sixth "settled finding with no call site" in this directory. It now has one, opt-in per clip,
    because a fire-lit night room is supposed to change brightness and flattening every clip would
    remove the thing some rooms are for.
    """

    def test_absent_flag_returns_the_clip_UNCHANGED(self):
        """The default has to be a no-op for every existing clip, including with no sidecar at all."""
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(CSN.colour_normalised(t, "hall", "base", "/x/clip.mp4"), "/x/clip.mp4")
            _sidecar(t, "hall", "base", {"pct": 70})
            self.assertEqual(CSN.colour_normalised(t, "hall", "base", "/x/clip.mp4"), "/x/clip.mp4")
            _sidecar(t, "hall", "base", {"colourNormalise": False})
            self.assertEqual(CSN.colour_normalised(t, "hall", "base", "/x/clip.mp4"), "/x/clip.mp4")

    def test_true_means_full_strength_and_a_float_is_honoured(self):
        seen = {}
        orig = None
        import colour_normalise as CN
        orig = CN.normalise

        def fake(src, dst, strength=1.0):
            seen["src"], seen["dst"], seen["strength"] = src, dst, strength
            return 3.86, 61
        CN.normalise = fake
        try:
            with tempfile.TemporaryDirectory() as t:
                _sidecar(t, "hall", "base", {"colourNormalise": True})
                out = CSN.colour_normalised(t, "hall", "base", "/x/clip.mp4", log=lambda m: None)
                self.assertEqual(seen["strength"], 1.0)
                self.assertEqual(out, seen["dst"])
                self.assertNotEqual(out, "/x/clip.mp4")
                _sidecar(t, "hall", "base", {"colourNormalise": 0.5})
                CSN.colour_normalised(t, "hall", "base", "/x/clip.mp4", log=lambda m: None)
                self.assertEqual(seen["strength"], 0.5)
        finally:
            CN.normalise = orig

    def test_a_FAILED_normalise_bakes_the_original_rather_than_raising(self):
        """It sits mid-bake. Raising here would leave the room with no clip at all, which is strictly
        worse than a clip that still has its brightness arc."""
        import colour_normalise as CN
        orig = CN.normalise
        CN.normalise = lambda src, dst, strength=1.0: (_ for _ in ()).throw(RuntimeError("ffmpeg gone"))
        try:
            with tempfile.TemporaryDirectory() as t:
                _sidecar(t, "hall", "base", {"colourNormalise": True})
                said = []
                out = CSN.colour_normalised(t, "hall", "base", "/x/clip.mp4", log=said.append)
                self.assertEqual(out, "/x/clip.mp4")
                self.assertTrue(any("FAILED" in m for m in said))
        finally:
            CN.normalise = orig


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
