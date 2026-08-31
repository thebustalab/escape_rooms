#!/usr/bin/env python3
"""Tests for validate_assets.door_reciprocity — the scriptable bidirectional-passage check.

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
        _fails, misses, _ready = va.check_scenario(path)
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
