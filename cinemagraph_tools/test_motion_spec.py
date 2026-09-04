#!/usr/bin/env python3
"""Tests for motion_spec.py — the structured motion prompt and the per-subject liveness gate.

THE FAILURE THIS GUARDS. A whole-frame liveness number cannot say WHICH part of a room failed to
animate. canopic_night scored the lowest frame-level liveness of the whole night set (2.4%) while
being, in Lucas's words, "didn't animate the water but it did animate the little flames/candles
everywhere" — half the room perfect, half frozen, one number for both. `test_canopic_night_regression`
pins the real measured values so a change to the statistic or the thresholds that would stop flagging
the fountain fails loudly.
"""
import unittest

from motion_spec import (DEAD_P95, WEAK_P95, render_prompt, render_negative, validate,
                         repair_list, still_violations, NEG_PAPER)


def _sub(name, box, phrase="it moves", **kw):
    d = {"name": name, "box": box, "phrase": phrase}
    d.update(kw)
    return d


def _measured(name, p95, still=False):
    return {"name": name, "box": [0, 0, 1, 1], "p95": p95, "mean": p95 / 2,
            "luma": 40.0, "verdict": "dead" if p95 < DEAD_P95 else ("weak" if p95 < WEAK_P95 else "alive"),
            "expect_still": still}


class MotionSpecTest(unittest.TestCase):

    # ---- the prompt is generated FROM the subjects, so the two cannot drift ----

    def test_every_subject_phrase_reaches_the_prompt(self):
        spec = {"subjects": [_sub("a", [0, 0, .1, .1], "the water rippling"),
                             _sub("b", [.2, .2, .3, .3], "the flame flickering")]}
        p = render_prompt(spec)
        self.assertIn("the water rippling", p)
        self.assertIn("the flame flickering", p)

    def test_prompt_carries_the_no_travel_rule(self):
        """The one prompt rule that IS demonstrated: a two-ended loop forbids net travel."""
        p = render_prompt({"subjects": [_sub("a", [0, 0, .1, .1])]})
        self.assertIn("NOTHING TRAVELS ACROSS THE FRAME", p)

    def test_rigid_list_is_overridable_per_room(self):
        """The stabiliser's default names architecture only, so boards, signs and lamp bodies are not
        covered and the model may deform them — market_price's price-board bowed for exactly this
        reason. A room must be able to name its own rigid objects."""
        p = render_prompt({"subjects": [_sub("a", [0, 0, .1, .1])],
                           "rigid": "The slate price-board and the lantern body"})
        self.assertIn("The slate price-board and the lantern body are rigid", p)

    def test_a_shared_phrase_is_named_ONCE_however_many_boxes_carry_it(self):
        """THE OVER-DRIVE BUG. Lantern subjects are per-LOCATION because each needs its own measurement
        box (lights_1/2/3), but they share one phrase — and joining them naively wrote that phrase into
        the prompt three times, tripling the weight of the most energetic sentence in the scheme. Every
        canyon prompt said "a live, restless flame that gutters and flares ... pulsing" three times in a
        row, in a set Lucas rejected twice for moving too fast (2026-08-31, 2026-09-01).

        Name once, measure three times — the boxes are unaffected, which is the point."""
        spec = {"subjects": [_sub("water", [0, 0, .1, .1], "the water rippling"),
                             _sub("lights_1", [.2, .2, .3, .3], "a lantern flame"),
                             _sub("lights_2", [.4, .4, .5, .5], "a lantern flame"),
                             _sub("lights_3", [.6, .6, .7, .7], "a lantern flame")]}
        p = render_prompt(spec)
        self.assertEqual(p.count("a lantern flame"), 1)
        self.assertEqual(p.count("the water rippling"), 1)
        self.assertEqual(len(spec["subjects"]), 4)          # de-dup is prose-only; nothing is measured less

    def test_dedup_keeps_the_first_occurrence_and_the_order(self):
        """Order carries no meaning (stage AO: first/last/absent scored 4.14/4.14/4.13) but a reordering
        would still be a silent change to every prompt, so it is pinned rather than left to chance."""
        spec = {"subjects": [_sub("a", [0, 0, .1, .1], "alpha"), _sub("b", [.1, .1, .2, .2], "beta"),
                             _sub("c", [.2, .2, .3, .3], "alpha"), _sub("d", [.3, .3, .4, .4], "gamma")]}
        p = render_prompt(spec)
        self.assertIn("alpha, beta, gamma", p)

    def test_pinned_lines_do_not_produce_a_double_full_stop(self):
        """A pinned line already ends in a full stop and the stabiliser tail opens with one, which was
        writing ".." into every prompt that used pins — i.e. most of the canyon."""
        p = render_prompt({"subjects": [_sub("a", [0, 0, .1, .1])],
                           "pinned": ["The map is still."]})
        self.assertNotIn("..", p)

    def test_pinned_phrases_are_appended(self):
        p = render_prompt({"subjects": [_sub("a", [0, 0, .1, .1])],
                           "pinned": ["The parchment lies completely flat and still."]})
        self.assertIn("lies completely flat and still", p)

    def test_document_flag_adds_the_paper_negative(self):
        self.assertIn(NEG_PAPER.strip(", "), render_negative({"has_document": True}))
        self.assertNotIn("paper curling", render_negative({}))

    # ---- validation: a subject that cannot be measured must not pass silently ----

    def test_subject_without_a_box_is_rejected(self):
        errs = validate({"subjects": [{"name": "x", "phrase": "moves"}]})
        self.assertTrue(any("cannot be measured" in e for e in errs), errs)

    def test_subject_without_a_phrase_is_rejected(self):
        """A boxed subject with no phrase would be measured but never named in the prompt — so it
        would be flagged dead for the good reason that nobody asked it to move."""
        errs = validate({"subjects": [{"name": "x", "box": [0, 0, .1, .1]}]})
        self.assertTrue(any("never named in the prompt" in e for e in errs), errs)

    def test_empty_spec_is_rejected(self):
        self.assertTrue(validate({"subjects": []}))

    def test_inverted_and_out_of_range_boxes_are_rejected(self):
        self.assertTrue(validate({"subjects": [_sub("a", [.5, .5, .2, .9])]}))
        self.assertTrue(validate({"subjects": [_sub("a", [0, 0, 1.4, .5])]}))

    # ---- the gate ----

    def test_canopic_night_regression(self):
        """The real measured p95s. Water dead, candles alive — the split a frame-level number hid."""
        measured = [_measured("lion_spout", 3.26), _measured("fountain_basin", 3.80),
                    _measured("rim_spill", 2.86), _measured("shrine_lamps", 13.60),
                    _measured("colonnade_lamps", 5.15), _measured("temple_lamps", 6.12)]
        names = [r["name"] for r in repair_list(measured)]
        self.assertEqual(names, ["lion_spout", "fountain_basin", "rim_spill"])
        self.assertEqual([m["verdict"] for m in measured][3], "alive")

    def test_known_dead_and_known_alive_regions_land_on_the_right_side(self):
        """Every labelled region we have. The daytime library shaft (3.13) genuinely needed a repair
        tile; the fuel-smoke (10.63) and crown-fire (6.25) are plainly animating on inspection."""
        self.assertEqual(_measured("library_shaft", 3.13)["verdict"], "dead")
        self.assertEqual(_measured("crown_fire", 6.25)["verdict"], "weak")
        self.assertEqual(_measured("fuel_smoke", 10.63)["verdict"], "alive")
        self.assertEqual(_measured("quay_water", 26.88)["verdict"], "alive")

    def test_weak_is_not_auto_repaired(self):
        """WEAK exists so a modest but real motion is surfaced rather than silently re-rendered."""
        self.assertEqual(repair_list([_measured("crown_fire", 6.25)]), [])

    def test_a_still_subject_is_never_queued_for_repair(self):
        """`still` marks a check that something did NOT move — a gear ring, a mast. Repairing it would
        animate the very thing that must stay put."""
        self.assertEqual(repair_list([_measured("gear_ring", 1.0, still=True)]), [])

    def test_still_violation_is_reported_separately(self):
        v = still_violations([_measured("mast", 39.0, still=True)])
        self.assertEqual([x["name"] for x in v], ["mast"])

    # ---- `still` as an ENFORCEABLE pin (egypt/library, 2026-09-02) --------------------------------
    # The flag used to be measured and reported and nothing else, and two halves of it were unusable:
    # `validate` demanded a motion phrase for a subject you were trying to FREEZE, and `render_prompt`
    # then joined that phrase into the positive mover list — so declaring something still was a way of
    # asking for it to move. Both are fixed; these pin the fix.

    def test_a_still_subject_needs_no_phrase(self):
        """Demanding one is what made the flag unusable — see the note above."""
        spec = {"subjects": [_sub("dust", [0, 0, .5, .5]),
                             {"name": "codex", "box": [.6, .6, .7, .7], "still": True}]}
        self.assertEqual(validate(spec), [])

    def test_a_still_subjects_phrase_is_a_PIN_not_a_mover(self):
        """The whole point. A pinned object's sentence must land after the movers, never inside the
        comma-joined motion list where it reads as another thing to animate."""
        spec = {"subjects": [_sub("dust", [0, 0, .5, .5], phrase="dust drifting"),
                             {"name": "codex", "box": [.6, .6, .7, .7], "still": True,
                              "phrase": "The codex lies dead still."}]}
        p = render_prompt(spec)
        self.assertIn("dust drifting", p)
        self.assertIn("The codex lies dead still.", p)
        # not in the mover list: the movers are what sits before the first pin/tail sentence
        movers = p.split("dust drifting")[1].split(".")[0]
        self.assertNotIn("codex", movers)

    def test_a_still_subject_alone_still_counts_as_having_subjects(self):
        """A spec of nothing but pins is degenerate but must not crash the validator."""
        spec = {"subjects": [{"name": "codex", "box": [.6, .6, .7, .7], "still": True}]}
        self.assertEqual(validate(spec), [])

    def test_a_moving_subject_still_requires_a_phrase(self):
        """The relaxation is for `still` ONLY — an unphrased mover is still the old silent bug."""
        spec = {"subjects": [{"name": "dust", "box": [0, 0, .5, .5]}]}
        self.assertTrue(any("no `phrase`" in e for e in validate(spec)))


if __name__ == "__main__":
    unittest.main()
