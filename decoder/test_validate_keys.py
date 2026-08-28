#!/usr/bin/env python3
"""
test_validate_keys.py — regression coverage for scenario_expected() in validate_keys.py.

NOTE (2026-08-28): scenario_expected() grew a THIRD return value (`n_mcq`, the count of MCQ slots,
used for the same-slot positional-tell warning) when the dynamic puzzle queue landed, and this suite
was not updated — so all six tests errored on unpacking and the guard that protects every grading key
had no working regression cover. Unpacked with `*_rest` now, so the suite survives the NEXT field too (it grew a fourth, `ungraded`, on 2026-08-28).

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
        vec, notes, *_rest = scenario_expected({"rooms": [room("r1", puzzle=mcq(3))]})
        self.assertEqual(vec, [3])
        self.assertEqual(notes, [])

    def test_check_encodes_one(self):
        vec, notes, *_rest = scenario_expected({"rooms": [room("r1", puzzle=check())]})
        self.assertEqual(vec, [1])
        self.assertEqual(notes, [])

    def test_pick_encodes_one(self):
        vec, notes, *_rest = scenario_expected({"rooms": [room("r1", puzzle=pick())]})
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
        vec, notes, *_rest = scenario_expected(doc)
        self.assertEqual(vec, [3, 2, 1, 1])
        self.assertEqual(notes, [])

    def test_escape_and_stub_rooms_excluded(self):
        doc = {"rooms": [
            room("room1", puzzle=mcq(3)),
            room("stub", built=False, puzzle=mcq(0)),
            room("escape1", phase="escape", puzzle=pick()),
        ]}
        vec, _, *_rest = scenario_expected(doc)
        self.assertEqual(vec, [3])

    def test_puzzle_without_gradeable_content_flagged(self):
        vec, notes, *_rest = scenario_expected({"rooms": [room("r1", puzzle={"type": "puzzle"})]})
        self.assertIn(None, vec)
        self.assertTrue(any("neither question, check, nor pick" in n for n in notes))


# FAILURE MODE UNDER TEST — a built room with no puzzle used to append None to the expected vector, and
# main() then hit `if None in exp: continue`, SKIPPING THE DECODER-KEY COMPARISON FOR THE WHOLE SCENARIO.
# So the guard silently stopped guarding exactly the scenarios that had a connective room: temple's key
# was 1-BASED against a 0-based codec — every answer would have graded wrong — and validate_keys had been
# reporting it as a mere structural complaint for weeks (found + fixed 2026-08-28). An ungraded room takes
# no codec slot (mintCode keys off roomResults), so it must take no vector slot either, and must never
# suppress the comparison.

class TestUngradedRoomsDoNotSuppressTheKeyCheck(unittest.TestCase):
    def _doc(self, extra_hotspots):
        return {"rooms": [
            room("graded", puzzle=mcq(2)),
            {"key": "passage", "built": True, "hotspots": extra_hotspots},
        ]}

    def test_a_clue_room_takes_no_slot_and_leaves_the_vector_comparable(self):
        vec, notes, *_rest = scenario_expected(self._doc([{"id": "c", "type": "clue"}]))
        self.assertEqual(vec, [2], "a clue room must not occupy a codec slot")
        self.assertNotIn(None, vec, "a None here silently disables the whole key comparison")
        self.assertEqual(notes, [], "a clue room is deliberate, not a structural failure")

    def test_a_bare_passage_warns_but_still_leaves_the_vector_comparable(self):
        doc = self._doc([{"id": "d", "type": "door"}])
        vec, notes, _n, ungraded = scenario_expected(doc)
        self.assertEqual(vec, [2])
        self.assertNotIn(None, vec)
        self.assertEqual(notes, [], "a bare passage cannot mis-grade, so it must not FAIL")
        self.assertTrue(ungraded, "...but it should still be surfaced as a warning")


if __name__ == "__main__":
    unittest.main()
