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


if __name__ == "__main__":
    unittest.main()
