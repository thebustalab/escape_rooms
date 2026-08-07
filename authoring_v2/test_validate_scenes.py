#!/usr/bin/env python3
"""Tests for validate_scenes.py — the mechanical pre-art scene checks (stdlib only).

Each case pins a failure that is SILENT in the pipeline: the art generates, the boxes place, the harness
reports success, and the break only surfaces when a student clicks the thing. Run: python3 test_validate_scenes.py
"""
import json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate_scenes as vs


def _scen(rooms, **top):
    doc = {"chapter": "c", "scenario": "s", "coverPrompt": "a cover", "rooms": rooms}
    doc.update(top)
    return doc


def _room(key, elements, planned=None, seam="a plain wall"):
    r = {"key": key, "authoring": {"sceneSpec": {
        "room": key, "setting": "somewhere", "seam": seam, "elements": elements}}}
    if planned is not None:
        r["plannedHotspots"] = planned
    return r


def _run(doc):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "scenario.json")
        json.dump(doc, open(p, "w", encoding="utf-8"))
        fails, warns, ready, skipped = vs.check_scenario(p)
    return fails, warns, skipped


class T(unittest.TestCase):
    def test_switch_role_is_inert_in_the_engine(self):
        f, _, _ = _run(_scen([_room("r1", [
            {"id": "lever", "at": "to the left", "label": "A lever", "desc": "a lever", "switch": True}])]))
        self.assertTrue(any("NO handler" in x for x in f), f)

    def test_dial_role_is_accepted(self):
        f, _, _ = _run(_scen([_room("r1", [
            {"id": "lever", "at": "to the left", "label": "A lever", "desc": "a lever", "dial": True}])]))
        self.assertEqual(f, [])

    def test_lock_carrying_grid_shaped_content_is_flagged(self):
        f, _, _ = _run(_scen([_room("r1",
            [{"id": "d", "at": "dead ahead in the centre", "label": "The door", "desc": "a door", "lock": True}],
            planned=[{"type": "lock", "label": "The door", "items": [], "buckets": [], "answer": {}}])]))
        self.assertTrue(any("GRID-shaped" in x for x in f), f)

    def test_missing_label_warns_and_colliding_slugs_fail(self):
        long = "a bright summer trip postcard taped up beside the wall phone in the corridor"
        f, w, _ = _run(_scen([_room("r1", [
            {"id": "a", "at": "to the left", "desc": long, "clue": True},
            {"id": "b", "at": "to the right", "desc": long, "clue": True}])]))
        self.assertTrue(any("no explicit `label`" in x for x in w), w)
        self.assertTrue(any("collides with" in x for x in f), f)   # same desc[:60] -> same slug

    def test_forward_door_in_a_gateless_room_can_never_open(self):
        f, _, _ = _run(_scen([
            _room("r1", [{"id": "d", "at": "to the right", "label": "On", "desc": "a door",
                          "door": {"direction": "forward", "to": "r2"}}]),
            _room("r2", [{"id": "b", "at": "to the left", "label": "Back", "desc": "back",
                          "door": {"direction": "back", "to": "r1"}}])]))
        self.assertTrue(any("can never open" in x for x in f), f)

    def test_a_lock_counts_as_a_gate_so_its_forward_door_is_fine(self):
        # regression: an escape room gated by a keypad DOES have a primary gate (pano-player primaryGate)
        f, _, _ = _run(_scen([
            _room("r1", [{"id": "k", "at": "dead ahead in the centre", "label": "Pad", "desc": "a keypad",
                          "lock": True},
                         {"id": "d", "at": "to the right", "label": "Out", "desc": "a door",
                          "door": {"direction": "forward", "to": "r2"}}]),
            _room("r2", [{"id": "b", "at": "to the left", "label": "Back", "desc": "back",
                          "door": {"direction": "back", "to": "r1"}}])]))
        self.assertEqual(f, [])

    def test_door_to_a_missing_room_and_unreachable_room(self):
        f, _, _ = _run(_scen([
            _room("r1", [{"id": "d", "at": "to the right", "label": "On", "desc": "a door",
                          "door": {"direction": "open", "to": "nowhere"}}]),
            _room("r2", [{"id": "x", "at": "to the left", "label": "Thing", "desc": "a thing", "clue": True}])]))
        self.assertTrue(any("is not a room" in x for x in f), f)
        self.assertTrue(any("not reachable" in x for x in f), f)

    def test_variant_needs_a_carrier_hotspot_and_a_matching_dial(self):
        f, w, _ = _run(_scen([_room("r1", [
            # no role -> no hotspot -> nothing to hang the variant on
            {"id": "view", "at": "to the right", "desc": "a view",
             "variants": [{"state": "lit", "reveal": "now lit", "when": {"eq": ["beam", "ship"]}}]},
            {"id": "dial", "at": "to the left", "label": "Dial", "desc": "a dial", "dial": True}],
            planned=[{"type": "dial", "label": "Dial", "key": "other_key"}])]))
        self.assertTrue(any("NO role" in x for x in f), f)
        self.assertTrue(any("which no dial in this room sets" in x for x in w), w)

    def test_animated_object_on_the_wrap_seam_warns(self):
        _, w, _ = _run(_scen([_room("r1", [
            {"id": "fire", "at": "on the far right", "label": "Fire", "desc": "a fire",
             "animate": {"motion": "flames", "loop": "boomerang"}}])]))
        self.assertTrue(any("wrap edge" in x for x in w), w)

    def test_bad_loop_mode_and_empty_motion_fail(self):
        f, _, _ = _run(_scen([_room("r1", [
            {"id": "a", "at": "to the left", "label": "A", "desc": "a", "animate": {"motion": "x", "loop": "spin"}},
            {"id": "b", "at": "to the right", "label": "B", "desc": "b", "animate": {"motion": "", "loop": "boomerang"}}])]))
        self.assertTrue(any("not in" in x for x in f), f)
        self.assertTrue(any("no motion" in x for x in f), f)

    def test_missing_seam_and_cover_warn(self):
        _, w, _ = _run(_scen([_room("r1", [
            {"id": "a", "at": "to the left", "label": "A", "desc": "a", "clue": True}], seam="")],
            coverPrompt=""))
        self.assertTrue(any("no `seam` set" in x for x in w), w)
        self.assertTrue(any("no coverPrompt" in x for x in w), w)

    def test_spec_role_drifting_from_the_committed_hotspot_fails(self):
        """Once a room is BUILT the committed hotspot is the truth. trees shipped with its levers spec'd as
        `switch` (committed `dial`) and its vault gate as `lock` (committed `grid`) — a re-gen would have
        recreated the wrong mechanic. Regression for the 2026-08-07 trees spec realignment."""
        doc = _scen([_room("r1", [
            {"id": "lever", "at": "to the left", "label": "Lever", "desc": "a lever", "switch": True},
            {"id": "gate", "at": "dead ahead in the centre", "label": "Gate", "desc": "a gate", "lock": True}])])
        doc["rooms"][0]["hotspots"] = [{"id": "lever", "type": "dial", "label": "Lever"},
                                       {"id": "gate", "type": "grid", "label": "Gate"}]
        f, _, _ = _run(doc)
        self.assertTrue(any("COMMITTED hotspot is 'grid'" in x for x in f), f)

    def test_a_switch_door_counts_as_the_way_back(self):
        """A monorail car's ONE door leads back or onward depending on the lever, so the car legitimately
        has no separate `back` door — don't warn about it."""
        doc = _scen([
            _room("r1", [{"id": "d", "at": "to the right", "label": "On", "desc": "a door",
                          "door": {"direction": "open", "to": "car"}}]),
            _room("car", [{"id": "cd", "at": "dead ahead in the centre", "label": "The car door",
                           "desc": "the car door", "door": {"direction": "open", "to": "r1",
                           "opensOnto": [{"state": "back", "reveal": "onto r1"},
                                         {"state": "on", "reveal": "onto r2"}]}}])])
        _, w, _ = _run(doc)
        self.assertFalse(any("no `back` door" in x for x in w), w)

    def test_scenario_with_no_specs_is_skipped_not_failed(self):
        f, w, skipped = _run(_scen([{"key": "r1"}]))
        self.assertTrue(skipped)
        self.assertEqual((f, w), ([], []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
