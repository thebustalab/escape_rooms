#!/usr/bin/env python3
"""
Regression test for generate_scene._post error surfacing (2026-07-24).

Failure mode guarded: `_post` used to let urllib raise a bare `HTTPError: 400 Bad Request`,
swallowing the API's response body — so the harness showed no reason (the real cause of a
mystifying 400 turned out to be `billing_hard_limit_reached`, invisible until the body was read).
`_post` now catches HTTPError and re-raises a RuntimeError that INCLUDES the body. This test asserts
the body text reaches the raised message.

Run: python3 authoring/test_generate_scene.py
"""
import io
import os
import sys
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_scene  # noqa: E402


class ErrorSurfacingTest(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("OPENAI_API_KEY", "test-key")
        self._orig = urllib.request.urlopen

    def tearDown(self):
        urllib.request.urlopen = self._orig

    def test_http_error_body_is_surfaced(self):
        body = (b'{"error":{"message":"Billing hard limit has been reached.",'
                b'"code":"billing_hard_limit_reached"}}')

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                url="https://api.openai.com/v1/images/generations",
                code=400, msg="Bad Request", hdrs=None, fp=io.BytesIO(body))

        urllib.request.urlopen = fake_urlopen
        with self.assertRaises(RuntimeError) as cm:
            generate_scene._post("/images/generations", {"model": "gpt-image-2"})
        msg = str(cm.exception)
        # The raised message must carry the code and the human-readable reason from the body,
        # not just a bare "400 Bad Request".
        self.assertIn("billing_hard_limit_reached", msg)
        self.assertIn("Billing hard limit has been reached", msg)
        self.assertIn("400", msg)


class RollHTest(unittest.TestCase):
    """seamfix relies on _roll_h being an exact, invertible horizontal wrap (no pixel loss), so a
    round-trip roll leaves the panorama identical. Pure PIL, no network."""

    def test_roll_is_invertible(self):
        from PIL import Image
        im = Image.new("RGB", (64, 16))
        for x in range(64):                      # a horizontal gradient so every column is distinct
            for y in range(16):
                im.putpixel((x, y), (x * 4 % 256, y * 16 % 256, (x + y) % 256))
        dx = 32
        rolled = generate_scene._roll_h(im, dx)
        back = generate_scene._roll_h(rolled, im.width - dx)   # undo
        self.assertEqual(list(im.getdata()), list(back.getdata()))
        # a roll actually moves pixels (not a no-op) and the far edge wraps to the front
        self.assertEqual(rolled.getpixel((0, 0)), im.getpixel((im.width - dx, 0)))
        self.assertEqual(generate_scene._roll_h(im, 0).getpixel((5, 5)), im.getpixel((5, 5)))




class SeamfixGeometryTest(unittest.TestCase):
    """Where a seam-fix actually lands. The wrap tester draws a band over [pos-left, pos+right] (fractions
    of image width) and `cmd_seamfix` rolls that span to the centre, edits it, and rolls back. If the roll
    or the strip bounds drift, the repair silently lands on the WRONG COLUMNS — the art looks 'fixed' in the
    wrong place, which is exactly the failure that is impossible to spot in review. Stubs the image API with
    a flat red frame, so every output pixel taken from the model marks the edited region in ORIGINAL
    coordinates. Pins stage 1 (the wrap edge, which straddles the wrap) and stage 2 (an arbitrary mid-image
    seam). Regression for the 2026-08-07 seam investigation."""

    W, H = 1536, 512

    def _edited_columns(self, pos, left, right, full=False, feather=0.0, crop=0.0, occluder=""):
        import base64, io, tempfile, types
        import requests
        from PIL import Image
        d = tempfile.mkdtemp()
        src, out = os.path.join(d, "in.png"), os.path.join(d, "out.png")
        Image.new("RGB", (self.W, self.H), (10, 20, 30)).save(src)

        class _Resp:
            status_code = 200
            def json(self):
                red = Image.new("RGB", (SeamfixGeometryTest.W, SeamfixGeometryTest.H), (255, 0, 0))
                b = io.BytesIO(); red.save(b, "PNG")
                return {"data": [{"b64_json": base64.b64encode(b.getvalue()).decode()}]}

        saved_post, saved_key = requests.post, generate_scene._key
        requests.post = lambda *a, **k: _Resp()
        generate_scene._key = lambda: "test-key"
        try:
            generate_scene.cmd_seamfix(types.SimpleNamespace(
                input=src, out=out, left=left, right=right, feather=feather, full=full, pos=pos,
                width=0.12, model="m", quality="high", prompt=None, crop=crop, occluder=occluder))
        finally:
            requests.post, generate_scene._key = saved_post, saved_key
        px = Image.open(out).convert("RGB").load()
        # the stub paints pure red; the source is (10,20,30). A column counts as EDITED when the model's
        # red has fully replaced the source (r == 255). `influenced` is the looser test used for feather:
        # any red bleed at all, which a blurred alpha spreads past the hard band edges.
        self._influenced = {x for x in range(self.W) if px[x, self.H // 2][0] > 40}
        return {x for x in range(self.W) if px[x, self.H // 2] == (255, 0, 0)}

    def test_stage2_edits_exactly_the_band_the_user_dragged(self):
        for pos in (0.5, 0.35, 0.75):
            got = self._edited_columns(pos, 0.06, 0.06)
            want = set(range(round((pos - 0.06) * self.W), round((pos + 0.06) * self.W)))
            # allow a 2px rounding slack at each end
            self.assertLessEqual(len(want - got), 4, f"pos={pos}: band columns not edited")
            self.assertLessEqual(len(got - want), 4, f"pos={pos}: edited outside the band")

    def test_stage1_edits_the_wrap_band_across_the_seam(self):
        got = self._edited_columns(1.0, 0.06, 0.06)
        want = set(range(0, round(0.06 * self.W))) | set(range(round(0.94 * self.W), self.W))
        self.assertLessEqual(len(want - got), 4, "wrap band columns not edited")
        self.assertLessEqual(len(got - want), 4, "edited outside the wrap band")

    def test_asymmetric_band_is_honoured(self):
        got = self._edited_columns(0.5, 0.02, 0.09)
        self.assertLessEqual(abs(min(got) - round(0.48 * self.W)), 3, "left extent wrong")
        self.assertLessEqual(abs(max(got) - round(0.59 * self.W)), 3, "right extent wrong")

    def test_feather_is_a_noop_in_full_mode_but_blends_in_composite(self):
        """The seam panel shares ONE feather slider across both stages, but stage 1 defaults to `--full`
        (whole model output, NO composite) where feather is never read, while stage 2 defaults to composite
        where it is the only thing softening the pasted strip's edges. Pinning this so the asymmetry can't
        be forgotten again: full mode ignores feather entirely; composite mode with feather widens the
        affected region beyond the hard band."""
        self._edited_columns(0.5, 0.06, 0.06, full=False, feather=0.0)
        hard = self._influenced
        self._edited_columns(0.5, 0.06, 0.06, full=False, feather=0.03)
        soft = self._influenced
        self.assertGreater(len(soft), len(hard), "feather should blend beyond the hard band edges")
        full_a = self._edited_columns(0.5, 0.06, 0.06, full=True, feather=0.0)
        full_b = self._edited_columns(0.5, 0.06, 0.06, full=True, feather=0.03)
        self.assertEqual(full_a, full_b, "feather must be a no-op in full mode")


    def test_crop_inpaint_leaves_everything_outside_the_crop_untouched(self):
        """The whole-image path makes the model re-render the entire pano, so a composite keeps a strip cut
        from a DIFFERENT render (Lucas, 2026-08-07: "an AI image of an AI image"). Crop-inpaint sends only a
        band around the seam, so every column outside that crop must be pixel-identical to the source."""
        import tempfile, os as _os
        from PIL import Image
        import numpy as np
        d = tempfile.mkdtemp()
        src, out = _os.path.join(d, "in.png"), _os.path.join(d, "out.png")
        rng = np.random.default_rng(0)
        a = rng.integers(0, 255, (self.H, self.W, 3), dtype=np.uint8)
        Image.fromarray(a, "RGB").save(src)

        import base64, io, types, requests
        class _Resp:
            status_code = 200
            def __init__(self, size): self.size = size
            def json(self):
                red = Image.new("RGB", self.size, (255, 0, 0))
                b = io.BytesIO(); red.save(b, "PNG")
                return {"data": [{"b64_json": base64.b64encode(b.getvalue()).decode()}]}
        def fake_post(*args, **kw):
            wh = kw["data"]["size"].split("x")
            return _Resp((int(wh[0]), int(wh[1])))
        saved_post, saved_key = requests.post, generate_scene._key
        requests.post = fake_post
        generate_scene._key = lambda: "k"
        try:
            generate_scene.cmd_seamfix(types.SimpleNamespace(
                input=src, out=out, left=0.04, right=0.04, feather=0.0, full=False, pos=0.5,
                width=0.12, model="m", quality="high", prompt=None, crop=0.34, occluder=""))
        finally:
            requests.post, generate_scene._key = saved_post, saved_key
        got = np.asarray(Image.open(out).convert("RGB"))
        # the model only ever saw a 34% crop; outside the EDITED band the pixels must be the original
        edited = {x for x in range(self.W) if tuple(got[self.H // 2, x]) == (255, 0, 0)}
        self.assertTrue(edited, "the band should have been edited")
        far = [x for x in range(self.W) if x < min(edited) - 40 or x > max(edited) + 40]
        self.assertTrue(np.array_equal(got[:, far, :], a[:, far, :]),
                        "columns away from the seam must be untouched original art")

    def test_occluder_prompt_names_the_object_and_implies_a_crop(self):
        """Occluder mode stands an object ON the seam so the two sides never have to agree."""
        import tempfile, os as _os, base64, io, types, requests
        from PIL import Image
        d = tempfile.mkdtemp()
        src, out = _os.path.join(d, "in.png"), _os.path.join(d, "out.png")
        Image.new("RGB", (self.W, self.H), (20, 30, 40)).save(src)
        seen = {}
        class _Resp:
            status_code = 200
            def __init__(self, size): self.size = size
            def json(self):
                b = io.BytesIO(); Image.new("RGB", self.size, (9, 9, 9)).save(b, "PNG")
                return {"data": [{"b64_json": base64.b64encode(b.getvalue()).decode()}]}
        def fake_post(*args, **kw):
            seen.update(kw["data"])
            wh = kw["data"]["size"].split("x")
            return _Resp((int(wh[0]), int(wh[1])))
        saved_post, saved_key = requests.post, generate_scene._key
        requests.post = fake_post
        generate_scene._key = lambda: "k"
        try:
            generate_scene.cmd_seamfix(types.SimpleNamespace(
                input=src, out=out, left=0.04, right=0.04, feather=0.0, full=False, pos=1.0,
                width=0.12, model="m", quality="high", prompt=None, crop=0.0,
                occluder="a plain stone pillar, floor to ceiling"))
        finally:
            requests.post, generate_scene._key = saved_post, saved_key
        self.assertIn("a plain stone pillar, floor to ceiling", seen["prompt"])
        self.assertIn("do not need to", seen["prompt"])          # the two sides needn't match
        self.assertNotEqual(seen["size"], f"{self.W}x{self.H}", "occluder should imply a CROP, not the whole pano")


if __name__ == "__main__":
    unittest.main()
