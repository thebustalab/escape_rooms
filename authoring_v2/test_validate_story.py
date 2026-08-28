#!/usr/bin/env python3
"""Tests for validate_story.py — the Story stage's closing gate.

FAILURE MODES UNDER TEST:
  - the walker misses a NESTED player-facing string. This is the whole reason the file exists: a hand
    sweep of temple's text came back clean while an orphaned reference sat in
    `hotspots[].question.prompt`. If the walker ever stops reaching a field, that field becomes
    invisible to the check and the gate silently stops gating.
  - a term dropped from the vetted opening but still used downstream is NOT flagged (the real break).
  - a term that was never in the opening and never removed IS flagged (noise that would train Lucas to
    ignore the gate).
  - a scenario with a string where a dict was expected kills the whole sweep (clouds did exactly this).

Run: python3 test_validate_story.py
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_story as vs


def scenario(story, **over):
    d = {"story": story, "enterLabel": "Go →",
         "done": {"title": "d", "body": "done body"},
         "escapeDone": {"title": "e", "body": "escape body"},
         "rooms": [{"key": "r1", "title": "Room one",
                    "entry": {"title": "E", "text": "entry text", "button": "On →"},
                    "hotspots": [{"id": "h1", "type": "clue", "label": "A clue", "body": "clue body"},
                                 {"id": "p1", "type": "puzzle", "label": "A table",
                                  "question": {"prompt": "nested prompt",
                                               "options": ["opt one", "opt two"],
                                               "feedback": {"correct": "nested correct",
                                                            "wrong": ["hint one", "hint two"]}}}]}]}
    d.update(over)
    return d


class WalkerCoverage(unittest.TestCase):
    def paths(self, doc):
        return {p for p, _ in vs.walk_text(doc)}

    def test_reaches_the_nested_question_block(self):
        """The exact blind spot that let temple's orphan through."""
        p = self.paths(scenario("opening"))
        for must in ("r1/p1.question.prompt",
                     "r1/p1.question.feedback.correct",
                     "r1/p1.question.feedback.wrong[0]",
                     "r1/p1.question.feedback.wrong[1]",
                     "r1/p1.question.options[0]"):
            self.assertIn(must, p, "walker cannot see %s — it is invisible to the gate" % must)

    def test_reaches_the_flat_fields_too(self):
        p = self.paths(scenario("opening"))
        for must in ("scenario.enterLabel", "scenario.done.body", "scenario.escapeDone.body",
                     "r1.entry.text", "r1.entry.button", "r1/h1.body", "r1/h1.label"):
            self.assertIn(must, p)

    def test_done_and_escapeDone_may_be_bare_strings(self):
        """clouds ships them as strings; assuming the {title,body} dict killed the corpus sweep."""
        d = scenario("opening", done="a bare string finish", escapeDone="a bare string escape")
        p = self.paths(d)
        self.assertIn("scenario.done", p)
        self.assertIn("scenario.escapeDone", p)

    def test_survives_a_string_where_a_dict_was_expected(self):
        """dimensionality_reduction/clouds crashed the whole sweep this way."""
        d = scenario("opening")
        d["rooms"][0]["hotspots"].append("not a dict")
        d["rooms"][0]["hotspots"].append({"id": "l1", "rows": ["bare string row"],
                                          "options": ["bare option"]})
        self.assertTrue(self.paths(d))          # no exception


class DroppedTerms(unittest.TestCase):
    def run_check(self, story, downstream_prompt, vetted):
        with tempfile.TemporaryDirectory() as td:
            d = scenario(story)
            d["rooms"][0]["hotspots"][1]["question"]["prompt"] = downstream_prompt
            sp = os.path.join(td, "scenario.json")
            json.dump(d, open(sp, "w", encoding="utf-8"))
            open(os.path.join(td, ".vetted_story.txt"), "w", encoding="utf-8").write(vetted)
            return vs.check_scenario(sp)

    def test_flags_a_term_the_rewrite_dropped(self):
        fails, _w, _n = self.run_check(
            story="You have until midday to rebuild the registers.",
            downstream_prompt="The Closing must account for every fire.",
            vetted="The sanctuary is banked at the Closing.")
        self.assertTrue(any("closing" in f.lower() for f in fails),
                        "the real break must FAIL: %r" % fails)

    def test_does_not_flag_a_term_that_never_left(self):
        fails, _w, _n = self.run_check(
            story="The Closing comes at midday.",
            downstream_prompt="The Closing must account for every fire.",
            vetted="The Closing comes at midday.")
        self.assertEqual(fails, [], "a term still in the opening must not be flagged")

    def test_does_not_flag_a_local_proper_noun(self):
        """A room may introduce its own names — that is not an orphan."""
        fails, _w, _n = self.run_check(
            story="You have until midday to rebuild the registers.",
            downstream_prompt="Ninestep sits beside Longshadow in the East wing.",
            vetted="You have until midday to rebuild the registers.")
        self.assertEqual(fails, [])

    def test_missing_snapshot_warns_but_does_not_fail(self):
        with tempfile.TemporaryDirectory() as td:
            sp = os.path.join(td, "scenario.json")
            json.dump(scenario("an opening"), open(sp, "w", encoding="utf-8"))
            fails, warns, _n = vs.check_scenario(sp)
            self.assertEqual(fails, [])
            self.assertTrue(any("vetted_story" in w for w in warns))

    def test_no_landing_story_is_a_failure(self):
        with tempfile.TemporaryDirectory() as td:
            sp = os.path.join(td, "scenario.json")
            json.dump(scenario(""), open(sp, "w", encoding="utf-8"))
            fails, _w, _n = vs.check_scenario(sp)
            self.assertTrue(fails)


if __name__ == "__main__":
    unittest.main(verbosity=2)
