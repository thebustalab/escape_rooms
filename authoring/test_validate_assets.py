#!/usr/bin/env python3
"""Regression tests for validate_assets.check_scenario's blank-clue detection.

FAILURE-MODE NARRATIVE (hospital, 2026-08-05). Hospital's escape had two editorial-note clues by
design (Note A pinned the facet rows, Note B the columns). At wiring, all the guidance was folded into
Note A and Note B was left with `body: ""` and `pickup: true` (a boolean, not a caption string). In the
engine, an empty-body clue appends no text to its modal, so Note B opened a BLANK modal and its
"Add to notebook" button logged a contentless entry — a dead pickup shipped in a scenario the central
validator PASSed.

Why it slipped through: the old blank-clue check treated ANY truthy `pickup` as display content
(`not h.get("pickup")`), so a boolean `pickup:true` masked the empty body + missing image. The fix:
only a NON-EMPTY STRING pickup is a caption (real content); a boolean `pickup:true` with no body and no
image still renders blank and must be flagged. These tests pin that distinction so the class can't
regress. Run: `python3 authoring/test_validate_assets.py`.
"""
import json
import os
import tempfile

from validate_assets import check_scenario


def _scen_with_clue(clue):
    """Minimal one-room built scenario carrying a single clue hotspot to exercise the blank check."""
    return {
        "status": "in_development",
        "rooms": [{
            "key": "room1",
            "built": True,
            "panorama": "room1/scene.png",
            "sfx": {"src": "audio/x.mp3"},
            "hotspots": [dict(clue, type="clue", id="c1")],
        }],
    }


def _blank_misses(scen):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "scenario.json")
        json.dump(scen, open(p, "w"))
        _, misses, _ = check_scenario(p)
    return [m for m in misses if "renders blank" in m]


CASES = [
    # (label, clue hotspot, should_flag_blank)
    ("empty body + pickup:true (the hospital Note B bug)", {"body": "", "pickup": True}, True),
    ("empty body + no pickup at all",                      {"body": ""},                 True),
    ("missing body + pickup:true",                         {"pickup": True},             True),
    ("pickup:true WITH a real body (Note A — valid)",      {"body": "Read me.", "pickup": True}, False),
    ("string pickup caption, empty body (valid)",          {"body": "", "pickup": "Postcard #4"}, False),
    ("image only, empty body (valid)",                     {"body": "", "image": "postcards/p.png"}, False),
]


def main():
    failures = 0
    for label, clue, should_flag in CASES:
        flagged = bool(_blank_misses(_scen_with_clue(clue)))
        ok = flagged == should_flag
        print(f"  {'ok ' if ok else 'FAIL'}  {label} -> flagged={flagged} (want {should_flag})")
        failures += not ok
    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
