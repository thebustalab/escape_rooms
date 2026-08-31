#!/usr/bin/env python3
"""Tests for scene_states.py — the (room, world-state) enumeration the art pipeline iterates.

THE FAILURE THIS GUARDS. On 2026-08-31 a cinemagraph run walked `room.panorama` to decide what to
animate. Egypt's `deck` room has a dawn base panorama AND a night variant hanging off an `ambient`
carrier hotspot (`night_wash`) as `variants[].panorama`. The run therefore rendered the DAYTIME image
and filed it as the night deck; Lucas spotted it by eye. Seven Egypt rooms carry such a variant, so a
room-shaped iteration silently animates the base states and ships a half-dead second act.

`test_variant_is_enumerated_not_just_base` is the direct regression. The rest pin the properties the
pipeline depends on: unbuilt scenarios enumerate (canyon keeps everything on `plannedHotspots`),
routing-only variants are not mistaken for art, and a variant with no prompt is reported.
"""
import unittest

from scene_states import scene_states, state_gaps


def _doc(rooms):
    return {"rooms": rooms}


class SceneStatesTest(unittest.TestCase):

    def test_variant_is_enumerated_not_just_base(self):
        """The deck regression: a room with a variant panorama yields TWO states, not one."""
        doc = _doc([{
            "key": "deck", "built": True, "panorama": "deck/scene.png",
            "authoring": {"scenePrompt": "a dawn deck"},
            "hotspots": [{"id": "night_wash", "type": "ambient", "variants": [
                {"state": "night", "panorama": "deck/scene_night.png",
                 "prompt": "same scene, now night", "when": {"solved": "library"}}]}],
        }])
        st = scene_states(doc)
        self.assertEqual(len(st), 2)
        self.assertEqual([s["state"] for s in st], ["base", "night"])
        self.assertEqual(st[0]["panorama"], "deck/scene.png")
        self.assertEqual(st[1]["panorama"], "deck/scene_night.png")
        self.assertEqual(st[1]["carrier"], "night_wash")
        # the gate travels with the state — the pipeline needs to know when it is shown
        self.assertEqual(st[1]["when"], {"solved": "library"})

    def test_planned_hotspots_are_read(self):
        """An authored-but-unbuilt scenario (canyon) keeps content on plannedHotspots only.
        Reading `hotspots` alone reports nothing and the whole scenario looks state-free."""
        doc = _doc([{
            "key": "works", "built": False, "panorama": None,
            "plannedHotspots": [{"id": "flood", "type": "ambient", "variants": [
                {"state": "flooded", "panorama": "works/scene_flood.png", "prompt": "rising water"}]}],
        }])
        st = scene_states(doc)
        self.assertEqual([s["state"] for s in st], ["base", "flooded"])
        self.assertEqual(st[1]["source"], "plannedHotspots")

    def test_routing_only_variant_is_not_a_state(self):
        """A switch-door variant carries `to`/`when` for navigation and NO art. It must not be
        enumerated, or the pipeline would try to render a panorama that was never meant to exist."""
        doc = _doc([{
            "key": "car", "built": True, "panorama": "car/scene.png",
            "hotspots": [{"id": "door", "type": "door", "variants": [
                {"state": "forward", "to": "next", "when": {"eq": ["dial", "on"]}}]}],
        }])
        st = scene_states(doc)
        self.assertEqual([s["state"] for s in st], ["base"])

    def test_missing_prompt_is_reported(self):
        """quay's real gap: night art committed, no prompt recorded, so it cannot be regenerated."""
        doc = _doc([{
            "key": "quay", "built": True, "panorama": "quay/scene.png",
            "authoring": {"scenePrompt": "a harbour"},
            "hotspots": [{"id": "night_wash", "variants": [
                {"state": "night", "panorama": "quay/scene_night.png"}]}],
        }])
        gaps = state_gaps(scene_states(doc))
        self.assertTrue(any(level == "missing-prompt" for level, _ in gaps), gaps)

    def test_base_prompt_comes_from_scene_prompt(self):
        doc = _doc([{"key": "r", "built": True, "panorama": "r/scene.png",
                     "authoring": {"scenePrompt": "the room"}}])
        self.assertEqual(scene_states(doc)[0]["prompt"], "the room")

    def test_room_with_no_variants_yields_exactly_one_state(self):
        """canyon's shape: nine rooms, no variants -> nine states. The boring case must stay boring."""
        doc = _doc([{"key": "j_c%d" % i, "built": False, "panorama": None} for i in range(9)])
        st = scene_states(doc)
        self.assertEqual(len(st), 9)
        self.assertTrue(all(s["state"] == "base" for s in st))


if __name__ == "__main__":
    unittest.main()
