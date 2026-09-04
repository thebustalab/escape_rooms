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


# --- malformed art-job fields are NAMED, not fatal -------------------------------------------------
# 2026-08-07: `door.opensOnto` was authored as a bare reveal string instead of a list of {state,reveal}.
# validate_scenes PASSED it, and the harness then died loading the scenario with a bare
# "'str' object has no attribute 'get'" from dooropen_jobs — no room, no field, no clue. Two halves to
# the fix: the job builders skip a malformed entry instead of raising (test_scene_spec covers that), and
# the validator FAILS with the element named so the art isn't silently dropped instead.
class TestSweepOrder(unittest.TestCase):
    """Regression: elements must run in left→right sweep order.

    canyon/undercroft (2026-08-28) carried [far left, left, dead ahead, left of centre, right,
    just right of centre, far right] — the control panel described before the map table that sits to
    its left, and the trunk arch before the ladder inboard of it. `render_prompt` joins elements in
    FILE order, so the prompt told gpt-image to sweep the panorama and then jump backwards, twice.
    Nothing caught it: the boxes derive from the `at` phrase rather than the order, so every
    downstream check passed and the only symptom would have been worse art, discovered after the gens
    were paid for. Two elements swapped to fix; the check is what makes it not recur.
    """

    def test_out_of_order_elements_warn(self):
        f, w, _ = _run(_scen([_room("r1", [
            {"id": "a", "at": "on the far left", "desc": "a wall"},
            {"id": "panel", "at": "dead ahead in the centre", "desc": "a panel"},
            {"id": "table", "at": "to the left of centre", "desc": "a table"},
            {"id": "z", "at": "on the far right", "desc": "a wall"}])]))
        self.assertTrue(any("left→right order" in x for x in w), w)
        # names BOTH sides of the inversion, in the order they appear — "A before B" reads as the fix
        self.assertTrue(any("panel before table" in x for x in w), w)
        self.assertEqual(f, [])                            # a warning, not a gate

    def test_in_order_elements_are_clean(self):
        _, w, _ = _run(_scen([_room("r1", [
            {"id": "a", "at": "on the far left", "desc": "a wall"},
            {"id": "table", "at": "to the left of centre", "desc": "a table"},
            {"id": "panel", "at": "dead ahead in the centre", "desc": "a panel"},
            {"id": "z", "at": "on the far right", "desc": "a wall"}])]))
        self.assertFalse(any("left→right order" in x for x in w), w)

    def test_phrases_sharing_one_x_are_not_an_ordering_violation(self):
        # "just right of centre" and "to the centre-right" both resolve to x=0.64; equal rank, so
        # either order is legal (they collide on position, which is a DIFFERENT, existing warning).
        _, w, _ = _run(_scen([_room("r1", [
            {"id": "a", "at": "to the centre-right", "desc": "a stair"},
            {"id": "b", "at": "just right of centre", "desc": "a stone"}])]))
        self.assertFalse(any("left→right order" in x for x in w), w)


def _spec_with(el):
    return {"rooms": [{"key": "r1", "authoring": {"sceneSpec": {
        "room": "r1", "setting": "a room", "seam": "a plain wall",
        "elements": [{"id": "e1", "at": "dead ahead in the centre", "desc": "a thing", **el}]}}}]}


def test_malformed_opensonto_is_a_named_fail(tmp_path):
    p = tmp_path / "scenario.json"
    p.write_text(json.dumps(_spec_with({"door": {"direction": "forward", "to": "r2",
                                                 "opensOnto": "the door standing open"}})))
    fails, _warns, _ready, _ok = vs.check_scenario(str(p))
    assert any("opensOnto" in f and "r1/e1" in f for f in fails), fails


def test_malformed_animate_and_variants_are_named_fails(tmp_path):
    for field, bad in (("animate", "the fire flickering"), ("variants", {"state": "lit"})):
        p = tmp_path / f"{field}.json"
        p.write_text(json.dumps(_spec_with({field: bad})))
        fails, _w, _r, _o = vs.check_scenario(str(p))
        assert any(field in f and "r1/e1" in f for f in fails), (field, fails)


def test_well_formed_art_fields_still_pass(tmp_path):
    p = tmp_path / "ok.json"
    p.write_text(json.dumps(_spec_with({
        "animate": {"motion": "the fire surging", "loop": "boomerang"},
        "variants": [{"state": "lit", "when": {"eq": ["k", "v"]}, "reveal": "identical but lit"}]})))
    fails, _w, _r, _o = vs.check_scenario(str(p))
    assert not [f for f in fails if "animate" in f or "variants" in f], fails


# ---- x-collision warning is ROLE-AWARE (2026-09-03) --------------------------------------------
# `approx_boxes` boxes EVERY element, so warning on any shared x flagged two bits of backdrop as if
# their (never-drawn) boxes would fight. That fired on a third of all authored rooms and pushed authors
# toward an eighth spatial position, which does not exist — there are seven. Only an element that needs
# a real box can contend: a gameplay role, or an `animate` motion subject.

def _two_at(el_a, el_b, hotspots=None):
    room = {"key": "r1", "authoring": {"sceneSpec": {
        "room": "r1", "setting": "a room", "seam": "a plain wall",
        "elements": [{"id": "a", "at": "dead ahead in the centre", "desc": "a thing", **el_a},
                     {"id": "b", "at": "dead ahead in the centre", "desc": "another thing", **el_b}]}}}
    if hotspots:
        room["hotspots"] = hotspots
    return {"rooms": [room]}


def _collisions(tmp_path, doc, name):
    p = tmp_path / name
    p.write_text(json.dumps(doc))
    _f, warns, _r, _o = vs.check_scenario(str(p))
    return [w for w in warns if "same approximate position" in w]


def test_two_scenery_elements_sharing_an_x_do_not_warn(tmp_path):
    """Neither will ever carry a box, so nothing can overlap."""
    assert _collisions(tmp_path, _two_at({}, {}), "scenery.json") == []


def test_two_animate_elements_sharing_an_x_do_warn(tmp_path):
    """Both become measured motion subjects — a real conflict."""
    m = {"animate": {"motion": "it stirs", "loop": "boomerang"}}
    assert len(_collisions(tmp_path, _two_at(m, m), "animate.json")) == 1


def test_an_animate_element_colliding_with_pure_scenery_does_not_warn(tmp_path):
    """Only ONE side needs a box, so there is nothing for it to fight with."""
    m = {"animate": {"motion": "it stirs", "loop": "boomerang"}}
    assert _collisions(tmp_path, _two_at(m, {}), "mixed.json") == []


def test_two_gameplay_hotspots_sharing_an_x_do_warn(tmp_path):
    doc = _two_at({"puzzle": True}, {"clue": True},
                  hotspots=[{"id": "a", "type": "puzzle"}, {"id": "b", "type": "clue"}])
    assert len(_collisions(tmp_path, doc, "roles.json")) == 1
