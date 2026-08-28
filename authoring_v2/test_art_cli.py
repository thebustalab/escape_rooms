#!/usr/bin/env python3
"""Tests for art_cli.py — the agent-triggerable art path (stdlib + PIL).

art_cli exists so an agent can fire variant/cinemagraph generation from the MOBILE assistant, where
nobody is watching the run and a bad job is discovered hours later at the desktop. So the thing worth
pinning is the VALIDATION: every way a job can be wrong must be caught before an API call is spent, and
the carrier-hotspot write must be idempotent (a re-run after a partial failure must not duplicate it).

The generation calls themselves are not exercised — they cost money and need a GPU — so each is fenced
behind a validated plan instead. Run: python3 test_art_cli.py
"""
import json, os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art_cli                                                     # noqa: E402
import harness_server as HS                                        # noqa: E402


def _png(path, size=(60, 20)):
    from PIL import Image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.new("RGB", size, (30, 40, 50)).save(path)


def _scenario(tmp):
    """A minimal committed scenario on disk: two rooms with scene.png, one uncommitted."""
    base = os.path.join(tmp, "rooms", "ch", "sc")
    os.makedirs(base, exist_ok=True)
    doc = {"chapter": "ch", "scenario": "sc", "status": "in_development", "rooms": [
        {"key": "deck", "built": True, "panorama": "deck/scene.png", "hotspots": [
            {"id": "mainsail", "type": "ambient", "label": "The mainsail", "box": [0.1, 0.2, 0.3, 0.6]},
            {"id": "no_box", "type": "ambient", "label": "Boxless"},
        ]},
        {"key": "hold", "built": True, "panorama": "hold/scene.png", "hotspots": [
            {"id": "lamp", "type": "ambient", "label": "The lamp", "box": [0, 0, 1, 1]}]},
        {"key": "unbuilt", "built": False, "hotspots": []},
    ]}
    with open(os.path.join(base, "scenario.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    _png(os.path.join(base, "deck", "scene.png"))
    _png(os.path.join(base, "hold", "scene.png"))
    return base


class Validation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.base = _scenario(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def plan(self, *jobs):
        return art_cli._plan(self.base, {"jobs": list(jobs)})

    def bad(self, job, needle):
        with self.assertRaises(ValueError) as cm:
            self.plan(job)
        self.assertIn(needle, str(cm.exception))

    def test_a_night_job_defaults_its_state_and_carrier(self):
        j = self.plan({"type": "night", "room": "deck", "prompt": "after dark"})[0]
        self.assertEqual(j["state"], "night")
        self.assertEqual(j["carrier"], "night_wash")

    def test_an_empty_job_list_is_refused(self):
        with self.assertRaises(ValueError):
            art_cli._plan(self.base, {"jobs": []})

    def test_unknown_room_is_caught_before_any_spend(self):
        self.bad({"type": "night", "room": "atlantis", "prompt": "x"}, "no room")

    def test_uncommitted_room_is_caught(self):
        # the single most expensive mistake to discover late: generating against art that isn't there
        self.bad({"type": "night", "room": "unbuilt", "prompt": "x"}, "no committed scene.png")

    def test_missing_prompt_is_caught(self):
        self.bad({"type": "night", "room": "deck", "prompt": "   "}, "needs a prompt")

    def test_a_typo_in_a_key_fails_loudly_rather_than_being_ignored(self):
        # a silently-dropped key is how a `when` condition goes missing and the variant never fires
        self.bad({"type": "night", "room": "deck", "prompt": "x", "whn": {}}, "unknown key")

    def test_variant_needs_a_state_and_a_real_hotspot(self):
        self.bad({"type": "variant", "room": "deck", "hotspot": "mainsail", "prompt": "x"}, "needs a state")
        self.bad({"type": "variant", "room": "deck", "hotspot": "ghost", "state": "s", "prompt": "x"},
                 "no hotspot")

    def test_variant_falls_back_to_the_hotspots_own_box(self):
        j = self.plan({"type": "variant", "room": "deck", "hotspot": "mainsail",
                       "state": "furled", "prompt": "x"})[0]
        self.assertEqual(j["box"], [0.1, 0.2, 0.3, 0.6])

    def test_a_hotspot_with_no_box_anywhere_is_caught(self):
        self.bad({"type": "variant", "room": "deck", "hotspot": "no_box", "state": "s", "prompt": "x"},
                 "needs a box[4]")

    def test_bad_type_is_caught(self):
        self.bad({"type": "mural", "room": "deck", "prompt": "x"}, "type must be")

    def test_one_bad_job_rejects_the_whole_plan(self):
        # all-or-nothing: a plan is validated before ANY job runs, so a fleet fired from mobile can't
        # spend half its money and then stop on a typo in the last entry
        with self.assertRaises(ValueError) as cm:
            self.plan({"type": "night", "room": "deck", "prompt": "ok"},
                      {"type": "night", "room": "deck"})
        self.assertIn("job 1", str(cm.exception))


class Carrier(unittest.TestCase):
    """The full-scene carrier is a marker-less ambient at [0,0,1,1] — see authoring_v2/AGENTS.md."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.base = _scenario(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _hotspots(self, room):
        doc = HS._load_scenario(self.base)
        return next(r for r in doc["rooms"] if r["key"] == room)["hotspots"]

    def test_carrier_is_created_ambient_and_full_frame(self):
        art_cli._ensure_carrier(self.base, "deck", "night_wash")
        spot = next(h for h in self._hotspots("deck") if h["id"] == "night_wash")
        self.assertEqual(spot["type"], "ambient")     # ambient => no marker, intercepts no clicks
        self.assertEqual(spot["box"], [0, 0, 1, 1])   # full frame => swaps the whole panorama

    def test_creating_the_carrier_twice_does_not_duplicate_it(self):
        # a re-run after a failed generation must be safe; two carriers would stack two full-scene
        # variants on the same state and the room would flicker between them
        art_cli._ensure_carrier(self.base, "deck", "night_wash")
        art_cli._ensure_carrier(self.base, "deck", "night_wash")
        self.assertEqual(sum(1 for h in self._hotspots("deck") if h["id"] == "night_wash"), 1)

    def test_carrier_does_not_disturb_the_rooms_existing_hotspots(self):
        art_cli._ensure_carrier(self.base, "deck", "night_wash")
        self.assertIn("mainsail", [h["id"] for h in self._hotspots("deck")])


class Restretch(unittest.TestCase):
    """The edit endpoint won't return 3:1 — it hands back 1536x1024, which MUST be stretched back to the
    base panorama's width or every hotspot box in the room lands on the wrong object after dark."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_squashed_reply_is_stretched_to_the_base_size(self):
        from PIL import Image
        p = os.path.join(self.tmp, "reply.png")
        _png(p, (1536, 1024))
        self.assertTrue(art_cli._restretch(p, (3072, 1024)))
        with Image.open(p) as im:
            self.assertEqual(im.size, (3072, 1024))

    def test_a_reply_already_at_the_right_size_is_left_alone(self):
        p = os.path.join(self.tmp, "reply.png")
        _png(p, (3072, 1024))
        self.assertFalse(art_cli._restretch(p, (3072, 1024)))


class ObserverWiring(unittest.TestCase):
    """The mobile path: an `escape_art` row must reach THIS script. A broken path here fails silently
    hours later in observer_results.jsonl, which is exactly the case art_cli was built to serve."""

    def test_the_escape_art_project_is_registered_and_points_at_this_file(self):
        tools = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
        cfg = os.path.join(tools, "Utilities", "agent_observer", "observer_config.json")
        if not os.path.isfile(cfg):
            self.skipTest("observer config not present on this machine")
        d = json.load(open(cfg, encoding="utf-8"))
        proj = next((p for p in d["projects"] if p["name"] == "escape_art"), None)
        self.assertIsNotNone(proj, "escape_art project missing from observer_config.json")
        self.assertTrue(proj.get("enabled"))
        self.assertTrue(proj.get("parallel"),
                        "must be parallel — a serial art run blocks the observer's whole poll loop")
        self.assertEqual(proj["match_fields"], {"action": "escape_art"})
        script = [c for c in proj["command"] if c.endswith("art_cli.py")]
        self.assertEqual(len(script), 1)
        self.assertTrue(os.path.isfile(script[0].replace("{tools_dir}", tools)),
                        "the configured art_cli.py path does not exist")
        self.assertGreaterEqual(proj["command_timeout_sec"], 1800,
                                "an art run is minutes per job — a short timeout kills it mid-fleet")


class VariantGallery(unittest.TestCase):
    """`collect_variants` backs the console's Environmental-variants panel. It is the only thing that
    makes a generated night pass VISIBLE before a student hits it, so its shape is worth pinning."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.base = _scenario(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reports_a_variant_with_its_base_and_whether_the_file_is_really_there(self):
        HS.ensure_variant_carrier(self.base, "deck", "night_wash")
        HS._add_variant("deck", "night_wash",
                        {"state": "night", "box": [0, 0, 1, 1], "prompt": "after dark",
                         "panorama": "deck/scene_night.png", "when": {"solved": "hold"}}, self.base)
        v = [x for x in HS.collect_variants(self.base) if x["room"] == "deck"][0]
        self.assertEqual(v["base"], "deck/scene.png")      # the gallery shows them side by side
        self.assertTrue(v["fullScene"])
        self.assertEqual(v["when"], {"solved": "hold"})
        self.assertFalse(v["exists"], "a recorded-but-missing PNG must be reported, not assumed present")
        _png(os.path.join(self.base, "deck", "scene_night.png"))
        v = [x for x in HS.collect_variants(self.base) if x["room"] == "deck"][0]
        self.assertTrue(v["exists"])

    def test_a_boxed_variant_is_not_reported_as_full_scene(self):
        HS._add_variant("deck", "mainsail",
                        {"state": "furled", "box": [0.1, 0.2, 0.3, 0.6],
                         "panorama": "deck/var_mainsail_furled.png"}, self.base)
        v = [x for x in HS.collect_variants(self.base) if x["state"] == "furled"][0]
        self.assertFalse(v["fullScene"], "a boxed variant must regenerate through gen-variant-room, "
                                         "not the whole-panorama re-light")

    def test_empty_scenario_reports_no_variants_rather_than_failing(self):
        self.assertEqual(HS.collect_variants(self.base), [])

    def test_the_door_open_partner_is_listed_view_only(self):
        """`panoramaOpen` is committed WITH the base, never declared as a hotspot variant, so it used to
        be the one piece of alternate room art the gallery could never show (2026-08-27, Lucas)."""
        doc = json.load(open(os.path.join(self.base, "scenario.json"), encoding="utf-8"))
        doc["rooms"][0]["panoramaOpen"] = "deck/scene_open.png"
        with open(os.path.join(self.base, "scenario.json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)
        _png(os.path.join(self.base, "deck", "scene_open.png"))
        v = [x for x in HS.collect_variants(self.base) if x["room"] == "deck"][0]
        self.assertTrue(v["readOnly"], "there is no prompt to re-fire — the gallery may only show it")
        self.assertEqual(v["panorama"], "deck/scene_open.png")
        self.assertEqual(v["base"], "deck/scene.png")
        self.assertTrue(v["exists"])
        self.assertTrue(v["whenLabel"], "a door-open partner has no `when` — it needs its own caption")

    def test_a_door_open_partner_already_declared_as_a_variant_is_not_listed_twice(self):
        HS._add_variant("deck", "mainsail",
                        {"state": "open", "box": [0, 0, 1, 1], "prompt": "hatch swung wide",
                         "panorama": "deck/scene_open.png"}, self.base)
        doc = json.load(open(os.path.join(self.base, "scenario.json"), encoding="utf-8"))
        for r in doc["rooms"]:
            if r["key"] == "deck":
                r["panoramaOpen"] = "deck/scene_open.png"
        with open(os.path.join(self.base, "scenario.json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)
        deck = [x for x in HS.collect_variants(self.base) if x["room"] == "deck"]
        self.assertEqual(len(deck), 1, "same file by two routes must appear once, and editable")
        self.assertFalse(deck[0]["readOnly"])


class KeyResolution(unittest.TestCase):
    """The failure that cost the first live Egypt run: a daemon-launched child has no rc file and no key."""

    def test_an_existing_env_key_is_passed_straight_through(self):
        os.environ["OPENAI_API_KEY"] = "sentinel-not-a-real-key"
        try:
            self.assertEqual(art_cli._gen_env()["OPENAI_API_KEY"], "sentinel-not-a-real-key")
            self.assertTrue(art_cli._have_image_key(art_cli._gen_env()))
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_absent_key_is_reported_as_absent_not_as_empty_string(self):
        self.assertFalse(art_cli._have_image_key({}))
        self.assertFalse(art_cli._have_image_key({"OPENAI_API_KEY": ""}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
