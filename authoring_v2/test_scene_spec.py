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


def test_style_and_edge_discipline_sit_before_the_tail_seam_anchor():
    """FAILURE MODE: a prompt clause appended AFTER the tail seam anchor.

    Rule 5 puts the seam anchor last on purpose — it is the biggest single lever on wrap quality,
    and the 2026-09-09 model switch added two more clauses (STYLE, EDGE_DISCIPLINE) that could
    easily have been tacked on the end. Anything after the anchor demotes it to mid-prompt, which
    would silently trade seam quality for style and look like a model regression rather than a
    prompt-ordering bug.
    """
    p = scene_spec.render_prompt({"setting": "a yard", "seam": "a plain wall",
                                  "elements": [{"at": "ahead", "desc": "a bench"}]})
    assert p.rstrip().endswith("no visible seam, join, or repetition."), \
        "the tail seam anchor must be the LAST thing in the prompt"
    assert p.index(scene_spec.STYLE) < p.rindex("Again: the extreme left and right edges")
    assert p.index(scene_spec.EDGE_DISCIPLINE) < p.rindex("Again: the extreme left and right edges")


def test_edge_discipline_keeps_BOTH_of_its_clauses():
    """FAILURE MODE: someone keeps half of EDGE_DISCIPLINE because it reads redundant.

    Measured 2026-09-09 over 5 draws each, ground-band join delta (median): no clause 42.1,
    margins-only 20.6, ground-only **79.3 — worse than adding nothing**, both together 3.4. The
    two are non-additive and only work as a pair, which no amount of reading the sentences would
    tell you. This test exists so the pair cannot be split without a deliberate decision.

    If either clause is reworded, re-measure the COMBINATION over >=5 draws
    (`model_probe/probe_models.py --stages 10`). Seam scores swing two orders of magnitude between
    draws of an identical prompt: one lucky draw once had 2.5 looking like the seam winner at 0.73
    when its true median was 42.
    """
    ed = scene_spec.EDGE_DISCIPLINE
    assert "EDGE DISCIPLINE:" in ed, "the margins clause is missing"
    assert "THE GROUND IS ONE SURFACE:" in ed, "the ground clause is missing"
    p = scene_spec.render_prompt({"setting": "x", "seam": "y", "elements": []})
    assert "EDGE DISCIPLINE:" in p and "THE GROUND IS ONE SURFACE:" in p
