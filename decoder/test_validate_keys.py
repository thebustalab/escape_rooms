#!/usr/bin/env python3
"""
test_validate_keys.py — regression coverage for scenario_expected() in validate_keys.py.

Guards the encoding contract the decoder key depends on: an MCQ room encodes its chosen option
index; a console-`check` OR a Type 4 `pick`-the-point room encodes 1 (solved); an escape-phase room
is excluded; a stub (unbuilt) room is excluded; a puzzle with none of question/check/pick is flagged.

The `pick` case is the one added 2026-07-22 with the pick-the-point puzzle type — before that a pick
room fell through to the "neither question nor check" failure. Run: python3 decoder/test_validate_keys.py
"""
import unittest
from validate_keys import scenario_expected


def room(key, built=True, phase="analysis", puzzle=None):
    hotspots = [puzzle] if puzzle else []
    return {"key": key, "built": built, "phase": phase, "hotspots": hotspots}


def mcq(correct, n_opts=6):
    return {"type": "puzzle", "question": {"options": [f"o{i}" for i in range(n_opts)], "correct": correct}}


def check():
    return {"type": "puzzle", "check": {"requires": ["answer"], "expr": "answer == 1"}}


def pick(answer="Lava_Lake"):
    return {"type": "puzzle", "pick": {"plotCode": "p <- ...", "answer": answer}}


class TestScenarioExpected(unittest.TestCase):
    def test_mcq_encodes_index(self):
        vec, notes = scenario_expected({"rooms": [room("r1", puzzle=mcq(3))]})
        self.assertEqual(vec, [3])
        self.assertEqual(notes, [])

    def test_check_encodes_one(self):
        vec, notes = scenario_expected({"rooms": [room("r1", puzzle=check())]})
        self.assertEqual(vec, [1])
        self.assertEqual(notes, [])

    def test_pick_encodes_one(self):
        vec, notes = scenario_expected({"rooms": [room("r1", puzzle=pick())]})
        self.assertEqual(vec, [1])
        self.assertEqual(notes, [])

    def test_redesigned_alaska_ladder(self):
        # R1 MCQ(3), R2 MCQ(idx), R3 pick, boss pick  ->  c(3, idx, 1, 1)
        doc = {"rooms": [
            room("room1", puzzle=mcq(3)),
            room("room2", puzzle=mcq(2)),
            room("room3", puzzle=pick("North_Killeak_Lake")),
            room("boss", puzzle=pick("Lava_Lake")),
        ]}
        vec, notes = scenario_expected(doc)
        self.assertEqual(vec, [3, 2, 1, 1])
        self.assertEqual(notes, [])

    def test_escape_and_stub_rooms_excluded(self):
        doc = {"rooms": [
            room("room1", puzzle=mcq(3)),
            room("stub", built=False, puzzle=mcq(0)),
            room("escape1", phase="escape", puzzle=pick()),
        ]}
        vec, _ = scenario_expected(doc)
        self.assertEqual(vec, [3])

    def test_puzzle_without_gradeable_content_flagged(self):
        vec, notes = scenario_expected({"rooms": [room("r1", puzzle={"type": "puzzle"})]})
        self.assertIn(None, vec)
        self.assertTrue(any("neither question, check, nor pick" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
