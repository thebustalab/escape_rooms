#!/usr/bin/env python3
"""Tests for the scriptable scenario checks in validate_assets — currently `door_reciprocity` (the
bidirectional-passage check) and `door_labels_undecided` (the publish-time door-name-plate decision).

## door_reciprocity

Regression for the monorail SWITCH-DOOR (2026-08-05): a car's single door routes back OR forward by lever
state, so its return path lives on a state VARIANT's `to`, not the base `to` (which points onward). The
check must read variant targets, or it flags every switch-door car as a one-way passage (false positive);
but it must STILL catch a genuinely one-way passage (a room you can enter with no way back).
"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_assets as va


def _scen(car_door):
    """A station1 -> car_sq forward passage, with station2 present+built so the car's onward target resolves;
    `car_door` is the car's single door. Returns just the station1<->car_sq one-way-passage messages."""
    scen = {"rooms": [
        {"key": "station1", "built": True, "hotspots": [
            {"id": "sd", "type": "door", "direction": "forward", "to": "car_sq"}]},
        {"key": "car_sq", "built": True, "hotspots": [car_door]},
        {"key": "station2", "built": True, "hotspots": [
            {"id": "sp", "type": "door", "direction": "back", "to": "car_sq"}]},
    ]}
    return [m for m in va.door_reciprocity(scen) if "one-way passage" in m and "station1" in m]


def test_switch_door_back_variant_counts_as_return():
    # base `to` points ONWARD (station2) but the back VARIANT returns to station1 → not one-way
    car_door = {"id": "cd", "type": "door", "direction": "open", "to": "station2", "variants": [
        {"state": "to_station2", "when": {"eq": ["car_sq_dir", "forward"]}, "to": "station2", "direction": "open"},
        {"state": "to_station1", "when": {"eq": ["car_sq_dir", "back"]}, "to": "station1", "direction": "back"}]}
    assert _scen(car_door) == []                                # the variant return is seen → no one-way flag


def test_genuine_one_way_still_flagged():
    # a car whose only door goes onward, with NO return door and NO variant back to station1
    car_door = {"id": "cd", "type": "door", "direction": "open", "to": "station2"}
    assert _scen(car_door), "a genuine one-way passage must still be flagged"


def test_plain_back_door_return_still_works():
    # the ordinary (non-switch) return: an explicit back door naming the source
    car_door = {"id": "cd", "type": "door", "direction": "back", "to": "station1"}
    assert _scen(car_door) == []


if __name__ == "__main__":
    test_switch_door_back_variant_counts_as_return()
    test_genuine_one_way_still_flagged()
    test_plain_back_door_return_still_works()
    print("ALL PASS")


def _solve_misses(gate):
    """Run check_scenario over one built room holding `gate`; return its solveSfx MISS messages."""
    scen = {"rooms": [{"key": "r1", "built": True, "panorama": "r1/scene.png",
                       "sfx": [{"src": "audio/bed.mp3"}], "hotspots": [gate]}]}
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "scenario.json")
        json.dump(scen, open(path, "w", encoding="utf-8"))
        _fails, misses, _ready, _advisories = va.check_scenario(path)
    return [m for m in misses if "solveSfx" in m]


def test_every_gate_type_needs_a_solve_sound():
    """Regression: the solveSfx MISS must cover ALL FOUR gate types, not just puzzle/lock.

    temple's escape (sun_altar/register_gods) was committed as `puzzle` while its spec and content were
    a `ledger`. Correcting the type to `ledger` (2026-08-28) made the room go from flagged to CLEAN —
    not because it gained a sound, but because the narrower ("puzzle","lock") test stopped applying to
    it. A silent loss of coverage caused by fixing an unrelated bug; this is the check that catches it.
    """
    for typ in ("puzzle", "lock", "grid", "ledger"):
        misses = _solve_misses({"id": "g", "type": typ})
        assert misses, f"{typ} gate with no solveSfx was not flagged"
        assert typ in misses[0], misses


def test_a_gate_with_a_solve_sound_is_clean():
    for typ in ("puzzle", "lock", "grid", "ledger"):
        assert _solve_misses({"id": "g", "type": typ, "solveSfx": "audio/s.mp3"}) == []


def test_non_gate_hotspots_do_not_need_one():
    for typ in ("clue", "door", "ambient", "dial", "elevmap"):
        assert _solve_misses({"id": "h", "type": typ, "body": "x", "to": "r1"}) == []


# --- door_labels_undecided: the publish-time door-name-plate decision (2026-09-16) -------------------
# `doorLabels` captions each open door with its target room's title. The check's whole job is to make the
# choice EXPLICIT at promotion, so it fires on ABSENCE and never on `false` — declining is an answer,
# forgetting is not. It only asks where a player can get lost, i.e. a room with 3+ doors.

def _junction(n_doors, **scen_extra):
    """One built room carrying `n_doors` doors, plus whatever scenario-level fields the test sets."""
    scen = {"rooms": [{"key": "hub", "built": True, "hotspots": [
        {"id": f"d{i}", "type": "door", "to": f"r{i}"} for i in range(n_doors)]}]}
    scen.update(scen_extra)
    return va.door_labels_undecided(scen)


def test_unset_on_a_junction_is_flagged():
    # 3 exits and no decision recorded — the case the check exists for
    out = _junction(3)
    assert out and "doorLabels" in out[0] and "hub (3)" in out[0]


def test_false_is_a_decision_and_passes():
    # explicitly declined — must NOT nag, or the only way to silence it would be to turn it on
    assert _junction(3, doorLabels=False) == []


def test_true_is_a_decision_and_passes():
    assert _junction(3, doorLabels=True) == []


def test_two_door_corridor_is_never_asked():
    # a corridor disambiguates itself (you came from one door, you're going to the other)
    assert _junction(2) == []


def test_unbuilt_rooms_do_not_trigger_it():
    scen = {"rooms": [{"key": "hub", "built": False, "hotspots": [
        {"id": f"d{i}", "type": "door", "to": f"r{i}"} for i in range(4)]}]}
    assert va.door_labels_undecided(scen) == []


def test_non_door_hotspots_are_not_counted_as_exits():
    # a room with two doors and three puzzles is a corridor, not a junction
    scen = {"rooms": [{"key": "hub", "built": True, "hotspots": [
        {"id": "d0", "type": "door", "to": "r0"}, {"id": "d1", "type": "door", "to": "r1"},
        {"id": "p0", "type": "puzzle"}, {"id": "p1", "type": "clue"}, {"id": "p2", "type": "dial"}]}]}
    assert va.door_labels_undecided(scen) == []


# ## packages_not_attached
# Subway (2026-09-21) listed dplyr/ggplot2/igraph but had NO `setup`, so nothing was attached and `%>%`
# was "could not find function" in its first puzzle. webr-console installs `packages`; only `setup`
# runs library(). Student-facing packages must be attached; support packages need not be.

def test_unattached_student_package_is_flagged():
    scen = {"packages": ["dplyr", "ggplot2", "tidyr"], "setup": "suppressMessages({library(dplyr)})"}
    flagged = va.packages_not_attached(scen)
    assert any("'ggplot2'" in m for m in flagged) and any("'tidyr'" in m for m in flagged)
    assert not any("'dplyr'" in m for m in flagged)


def test_missing_setup_flags_everything_student_facing():
    assert len(va.packages_not_attached({"packages": ["dplyr", "ggplot2"]})) == 2


def test_support_packages_may_stay_unattached():
    scen = {"packages": ["dplyr", "readr", "igraph", "ggiraph"], "setup": "library(dplyr)"}
    assert va.packages_not_attached(scen) == []


# --- planned_placed_drift: the planned manifest is a LIVE OVERWRITE, not a record (2026-09-22) -------
# `harness_server._attach_planned_content` copies every field of a `plannedHotspots` entry onto the
# placed hotspot it matches on (type, slug(label)) — and it runs on EVERY commit path, not only the
# first. So a planned entry left describing a SUPERSEDED design silently reverts the shipped one, days
# or weeks later, the next time anyone touches that room in the harness.
#
# Found auditing networks/subway, where it had survived three earlier audits because nothing simulates
# the commit: the cab ride controls were built as `lever` (shared/ride.js engages on nothing else)
# while their planned twins still described the abandoned `dial` design; the five cab platform doors
# were planned against a `dest_<line>` game-state key that no longer existed; and the two escape clues
# were planned with their pre-trim bodies, one of which carries the filing convention the escape cannot
# be solved without. Every other validator was green and the JS suite was green.
#
# The check is a dry run of that same attach. These tests pin its two halves.

def _drift(room):
    return va.planned_placed_drift({"rooms": [room]})


def _built(planned, placed):
    return {"key": "r1", "built": True, "plannedHotspots": planned, "hotspots": placed}


def test_a_planned_field_that_would_overwrite_the_built_one_is_reported():
    out = _drift(_built(
        [{"type": "door", "label": "The platform door", "to": "old_room"}],
        [{"id": "d", "type": "door", "label": "The platform door", "to": "new_room"}]))
    assert out and "`to`" in out[0], out


def test_a_planned_entry_matching_the_built_one_is_silent():
    hs = {"type": "door", "label": "The platform door", "to": "r2"}
    assert _drift(_built([dict(hs)], [dict(hs, id="d")])) == []


def test_placement_only_fields_are_not_drift():
    # box/id/label/type/note are _PLANNED_SKIP — the harness never copies them, so neither do we.
    assert _drift(_built(
        [{"type": "clue", "label": "A thing", "box": [0, 0, 1, 1], "note": "planned note", "body": "x"}],
        [{"id": "c", "type": "clue", "label": "A thing", "box": [0.2, 0.2, 0.3, 0.3], "body": "x"}])) == []


def test_a_planned_entry_with_no_placed_twin_is_reported():
    out = _drift(_built(
        [{"type": "clue", "label": "A deleted clue", "box": [0, 0, 1, 1], "body": "x"}],
        [{"id": "d", "type": "door", "label": "A door", "to": "r2"}]))
    assert out and "RE-CREATE" in out[0], out


def test_noElement_is_the_honest_opt_out():
    assert _drift(_built(
        [{"type": "clue", "label": "No object of its own", "noElement": True, "body": "x"}],
        [{"id": "d", "type": "door", "label": "A door", "to": "r2"}])) == []


def test_an_unbuilt_room_is_not_checked():
    r = _built([{"type": "door", "label": "A door", "to": "old"}],
               [{"id": "d", "type": "door", "label": "A door", "to": "new"}])
    r["built"] = False
    assert va.planned_placed_drift({"rooms": [r]}) == []
