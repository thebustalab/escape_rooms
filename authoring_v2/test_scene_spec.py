#!/usr/bin/env python3
"""
test_scene_spec.py — render_prompt seam-anchoring.

FAILURE MODE UNDER TEST. Under the fully-described 360 spec the image model was told the L/R edges "meet
seamlessly" but the sweep described the far-left and far-right as two DIFFERENT objects, so they clashed at
the seam. The fix anchors the wrap to ONE named surface (spec `seam`, or a default from `interior`) stated at
BOTH the head and tail of the prompt. These tests pin that the anchor is present twice, brackets the sweep,
and defaults correctly. Regression for the seam-anchor spec field (2026-08-05).

Run:  python3 test_scene_spec.py   ->  prints "all tests passed" or asserts.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene_spec  # noqa: E402  (path insert must precede import)


def test_seam_field_anchors_head_and_tail():
    spec = {"setting": "a vault", "interior": True,
            "seam": "a plain steel bulkhead, uniform and unbroken.",   # trailing period stripped for embedding
            "elements": [{"id": "a", "at": "on the far left", "desc": "a brass lever"}]}
    p = scene_spec.render_prompt(spec)
    anchor = "a plain steel bulkhead, uniform and unbroken"
    assert p.count(anchor) == 2, p                                     # named at head AND tail
    assert p.index(anchor) < p.index("a brass lever") < p.rindex(anchor)   # the sweep sits between the two anchors
    assert "extreme left and extreme right" in p
    assert "no visible seam" in p


def test_seam_defaults_from_interior():
    inside = scene_spec.render_prompt({"setting": "x", "interior": True, "elements": []})
    outside = scene_spec.render_prompt({"setting": "x", "interior": False, "elements": []})
    assert "stretch of wall" in inside and inside.count("stretch of wall") == 2      # default anchor, head+tail
    assert "sky and distant horizon" in outside and outside.count("sky and distant horizon") == 2


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"all tests passed ({len(tests)})")
