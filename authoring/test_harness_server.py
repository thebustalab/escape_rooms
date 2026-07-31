#!/usr/bin/env python3
"""
test_harness_server.py — smoke tests for the four-column generation concurrency
in harness_server.py. No network, no gpt-image-2 calls: exercises only the pure
job-state helpers (_sanitize_tag, _reserve, _start).

Run:  python3 test_harness_server.py   ->  prints "all tests passed" or asserts.

FAILURE MODE UNDER TEST — index collision. Four generate columns run
concurrently. Filenames are namespaced by tag (`gpt_<tag>_NNN.png`), and the
next index is handed out by _reserve(). If _reserve were replaced by a bare
_disk_next() read (as the single-worker version effectively was), two jobs with
the same tag would both compute the same start index and silently overwrite each
other's PNGs. test_reserve_non_overlapping guards exactly that.
"""
import os
import sys
import time
import json
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness_server as hs  # noqa: E402  (path insert must precede import)


def test_sanitize_tag():
    assert hs._sanitize_tag("room1") == "room1"
    assert hs._sanitize_tag("Room 1") == "room_1"
    assert hs._sanitize_tag("a--b__c") == "a_b_c"
    assert hs._sanitize_tag("") == "gen"
    assert hs._sanitize_tag(None) == "gen"
    assert hs._sanitize_tag("__weird__") == "weird"


def test_reserve_non_overlapping():
    """Consecutive reservations for one prefix must not overlap (the collision guard)."""
    prefix = "gpt_zzztest_"  # unlikely to exist on disk
    hs.RESERVED.pop(prefix, None)
    a = hs._reserve(prefix, 3)      # hands out a, a+1, a+2
    b = hs._reserve(prefix, 2)      # must start at or after a+3
    c = hs._reserve(prefix, 1)
    assert b >= a + 3, (a, b)
    assert c >= b + 2, (b, c)
    hs.RESERVED.pop(prefix, None)


def test_reserve_distinct_tags_independent():
    for p in ("gpt_taga_", "gpt_tagb_"):
        hs.RESERVED.pop(p, None)
    a = hs._reserve("gpt_taga_", 4)
    b = hs._reserve("gpt_tagb_", 4)
    # distinct prefixes each start fresh; no interference
    assert a >= 1 and b >= 1
    for p in ("gpt_taga_", "gpt_tagb_"):
        hs.RESERVED.pop(p, None)


def test_start_busy_reject_and_concurrent_slots():
    for s in ("t1", "t2"):
        hs.JOBS.pop(s, None)
    gate = threading.Event()

    def block():
        gate.wait(2)

    assert hs._start("t1", "test", block, 1) is True       # slot t1 now active
    assert hs._start("t1", "test", block, 1) is False       # same slot busy -> rejected
    assert hs._start("t2", "test", block, 1) is True        # different slot -> allowed concurrently
    assert hs.JOBS["t1"]["active"] is True
    assert hs.JOBS["t2"]["active"] is True
    gate.set()
    time.sleep(0.05)
    # bare block() target doesn't clear active (only _run_* do); tidy up for isolation
    for s in ("t1", "t2"):
        hs.JOBS.pop(s, None)


def test_status_idle_default_shape():
    # the shape /api/status?slot=<unknown> returns
    assert hs._IDLE["active"] is False
    assert set(hs._IDLE) >= {"active", "kind", "done", "total", "outputs", "error", "tag"}


# --- commit-to-room ("Send to room") ---------------------------------------
# FAILURE MODE UNDER TEST — a broken commit. "Send to room" must copy the closed
# base AND its `_open` partner under STABLE names (scene.png / scene_open.png) into
# a directory INSIDE the escape_rooms tree, carrying the re-keyed wrap + hotspots —
# and must reject a roomDir that escapes the tree. A half-committed or escaping room
# would silently break the door swap or write outside the site.

def _png(path):
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n")


def test_commit_room_full_pair():
    with tempfile.TemporaryDirectory() as scene, tempfile.TemporaryDirectory() as root:
        hs.SCENE, hs.ESCAPE_ROOT = scene, root
        _png(os.path.join(scene, "gpt_r_3.png"))
        _png(os.path.join(scene, "gpt_r_3_open.png"))
        json.dump({"gpt_r_3.png": {"haov": 360, "vaov": 90, "hfov": 120, "vOffset": -5, "pitch": -6}},
                  open(os.path.join(scene, "wrap.json"), "w"))
        written, rd, seed_wrap = hs._commit_room("gpt_r_3.png", "data_vis/case/room1")
        dest = os.path.join(root, "data_vis", "case", "room1")
        assert rd == "data_vis/case/room1"
        # Finding 3: only the image pair is copied — NO roomN/wrap.json or hotspots.json sidecars
        assert set(written) == {"scene.png", "scene_open.png"}
        assert os.path.exists(os.path.join(dest, "scene.png"))
        assert os.path.exists(os.path.join(dest, "scene_open.png"))       # door pair kept together
        assert not os.path.exists(os.path.join(dest, "wrap.json"))        # dead sidecar retired
        assert not os.path.exists(os.path.join(dest, "hotspots.json"))    # dead sidecar retired
        assert seed_wrap["vaov"] == 90 and seed_wrap["pitch"] == -6       # tuned wrap returned for the node


def test_commit_room_no_open_partner():
    with tempfile.TemporaryDirectory() as scene, tempfile.TemporaryDirectory() as root:
        hs.SCENE, hs.ESCAPE_ROOT = scene, root
        _png(os.path.join(scene, "a.png"))
        written, _, seed = hs._commit_room("a.png", "d/r")
        assert "scene.png" in written and "scene_open.png" not in written and seed is None


def test_commit_room_rejects_escape_and_missing():
    with tempfile.TemporaryDirectory() as scene, tempfile.TemporaryDirectory() as root:
        hs.SCENE, hs.ESCAPE_ROOT = scene, root
        _png(os.path.join(scene, "a.png"))
        for bad in ("../../etc", "..", ""):
            try:
                hs._commit_room("a.png", bad)
                raise AssertionError(f"should have rejected roomDir={bad!r}")
            except ValueError:
                pass
        try:
            hs._commit_room("nope.png", "d/r")
            raise AssertionError("should have rejected a missing image")
        except ValueError:
            pass


# --- scenario awareness (Phase 3) -----------------------------------------
# FAILURE MODE UNDER TEST — the harness authoring into the wrong scenario. The
# active scenario must drive SCENE (candidate pool) + COMMIT_BASE (send-to-room
# target), be discoverable by scanning rooms/*/*/scenario.json, reject a scenario
# path that escapes rooms/, and map a bare room key to rooms/<ch>/<sc>/<key>.

def _mkscenario(root, chapter, scenario, title):
    d = os.path.join(root, chapter, scenario)
    os.makedirs(d, exist_ok=True)
    json.dump({"title": title, "authoring": {"series": [{"key": "room1", "tag": "room1"}]}},
              open(os.path.join(d, "scenario.json"), "w"))
    return d


def _with_rooms_root(fn):
    """Run fn(tmp) with hs.ROOMS_ROOT/ESCAPE_ROOT/ACTIVE pointed at a temp tree, restored after."""
    save = (hs.ROOMS_ROOT, hs.ESCAPE_ROOT, dict(hs.ACTIVE), hs.SCENE, hs.COMMIT_BASE)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            hs.ESCAPE_ROOT = tmp
            hs.ROOMS_ROOT = os.path.join(tmp, "rooms")
            os.makedirs(hs.ROOMS_ROOT, exist_ok=True)
            fn(tmp)
    finally:
        hs.ROOMS_ROOT, hs.ESCAPE_ROOT, act, hs.SCENE, hs.COMMIT_BASE = save
        hs.ACTIVE.clear(); hs.ACTIVE.update(act)


def test_list_scenarios():
    def body(tmp):
        _mkscenario(hs.ROOMS_ROOT, "data_vis", "alaska", "Signal in the Cold")
        _mkscenario(hs.ROOMS_ROOT, "data_vis", "hawaii_aquifers", "Saltwater Intrusion")
        got = hs._list_scenarios()
        keys = {(s["chapter"], s["scenario"]) for s in got}
        assert keys == {("data_vis", "alaska"), ("data_vis", "hawaii_aquifers")}, keys
        assert any(s["title"] == "Saltwater Intrusion" for s in got)
    _with_rooms_root(body)


def test_scenario_dir_rejects_escape():
    def body(tmp):
        for bad in (("..", ".."), ("..", "etc"), ("data_vis", "../../..")):
            try:
                hs._scenario_dir(*bad)
                raise AssertionError(f"should reject {bad}")
            except ValueError:
                pass
        ok = hs._scenario_dir("data_vis", "alaska")   # a normal one is fine
        assert ok.startswith(os.path.abspath(hs.ROOMS_ROOT) + os.sep)
    _with_rooms_root(body)


def test_select_scenario_sets_scene_and_base():
    def body(tmp):
        _mkscenario(hs.ROOMS_ROOT, "data_vis", "hawaii_aquifers", "Saltwater Intrusion")
        hs._select_scenario("data_vis", "hawaii_aquifers")
        assert hs.ACTIVE == {"chapter": "data_vis", "scenario": "hawaii_aquifers"}
        assert hs.COMMIT_BASE.endswith(os.path.join("data_vis", "hawaii_aquifers"))
        assert hs.SCENE.endswith("_scratch") and os.path.isdir(hs.SCENE)  # scratch auto-created
        # a scenario with no scenario.json is rejected
        os.makedirs(os.path.join(hs.ROOMS_ROOT, "data_vis", "empty"), exist_ok=True)
        try:
            hs._select_scenario("data_vis", "empty")
            raise AssertionError("should reject a scenario with no scenario.json")
        except ValueError:
            pass
    _with_rooms_root(body)


def test_room_dir_for_key_confined_and_sanitised():
    def body(tmp):
        _mkscenario(hs.ROOMS_ROOT, "data_vis", "alaska", "x")
        hs._select_scenario("data_vis", "alaska")
        assert hs._room_dir_for_key("room2") == os.path.join("rooms", "data_vis", "alaska", "room2")
        # traversal / junk chars are stripped to a single segment
        assert hs._room_dir_for_key("../../etc") == os.path.join("rooms", "data_vis", "alaska", "etc")
        try:
            hs._room_dir_for_key("///")
            raise AssertionError("empty key should raise")
        except ValueError:
            pass
    _with_rooms_root(body)


# --- scenario.json read/write (Phase 6 — the IDE's source of truth) ------------
# FAILURE MODE UNDER TEST — a save that clobbers. Patches must shallow-MERGE (only the
# provided fields change; wrap/hotspots and other rooms are preserved), reject an unknown
# room key, and leave a `.bak` before every write. If a patch replaced the whole node (or
# the whole doc), a wrap-tab save would wipe the hotspots a different tab just wrote.

def _write_scenario(chapter, scenario, doc):
    d = os.path.join(hs.ROOMS_ROOT, chapter, scenario)
    os.makedirs(d, exist_ok=True)
    json.dump(doc, open(os.path.join(d, "scenario.json"), "w"))
    return d


def test_room_patch_merges_and_backs_up():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {"title": "T", "rooms": [
            {"key": "room1", "title": "A", "wrap": {"haov": 360}, "hotspots": [{"id": "h1"}]},
            {"key": "room2", "title": "B"},
        ]})
        hs._select_scenario("data_vis", "x")
        node = hs._room_patch("room1", {"title": "A2", "technique": "filter"})
        assert node["title"] == "A2" and node["technique"] == "filter"
        assert node["wrap"] == {"haov": 360}             # untouched fields preserved
        assert node["hotspots"] == [{"id": "h1"}]
        disk = json.load(open(os.path.join(d, "scenario.json")))
        assert disk["rooms"][0]["title"] == "A2"
        assert disk["rooms"][1]["title"] == "B"          # sibling room untouched
        assert os.path.exists(os.path.join(d, "scenario.json.bak"))
    _with_rooms_root(body)


def test_room_patch_rejects_unknown_key():
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room1"}]})
        hs._select_scenario("data_vis", "x")
        try:
            hs._room_patch("nope", {"title": "B"})
            raise AssertionError("should reject unknown room key")
        except ValueError:
            pass
    _with_rooms_root(body)


def test_scenario_patch_top_level_merges():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {"title": "T", "rooms": [{"key": "room1"}]})
        hs._select_scenario("data_vis", "x")
        hs._scenario_patch({"story": "once upon a time"})
        disk = json.load(open(os.path.join(d, "scenario.json")))
        assert disk["story"] == "once upon a time"
        assert disk["title"] == "T"                      # existing top-level preserved
        assert disk["rooms"][0]["key"] == "room1"        # rooms preserved
    _with_rooms_root(body)


# --- test-play sound-mixer writeback (_apply_mix) ------------------------------
# FAILURE MODE UNDER TEST — a volume save that clobbers. The mixer balances volumes live, then writes
# them back. It must touch ONLY the `volume` of layers matched by src (leaving mode/delay/duck and any
# unmatched layer intact), set scenario `musicVolume`, clamp to 0–1, and — being a fresh reload-modify-
# write — never disturb a layer the harness added between test-play start and save.

def test_apply_mix_volume_only_by_src():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {"title": "T", "musicVolume": 0.1, "rooms": [
            {"key": "room1", "sfx": [
                {"src": "room1/hum.mp3", "mode": "loop", "volume": 0.7, "duckMusicTo": 0.3},
                {"src": "room1/beep.mp3", "mode": "interval", "volume": 0.5},
            ]},
            {"key": "room2", "sfx": [{"src": "room2/wind.mp3", "mode": "loop", "volume": 0.4}]},
        ]})
        hs._select_scenario("data_vis", "x")
        out = hs._apply_mix(0.25, {"room1": {"room1/hum.mp3": 0.9, "room1/nope.mp3": 0.1}})
        assert out == {"music": True, "layers": 1, "solves": 0}   # only the matched src counted
        disk = json.load(open(os.path.join(d, "scenario.json")))
        assert disk["musicVolume"] == 0.25
        r1 = disk["rooms"][0]["sfx"]
        assert r1[0]["volume"] == 0.9 and r1[0]["duckMusicTo"] == 0.3 and r1[0]["mode"] == "loop"  # only volume moved
        assert r1[1]["volume"] == 0.5                        # unmatched layer untouched
        assert disk["rooms"][1]["sfx"][0]["volume"] == 0.4   # untouched room untouched
    _with_rooms_root(body)


def test_apply_mix_clamps_and_handles_single_object_sfx():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {"rooms": [
            {"key": "room1", "sfx": {"src": "room1/hum.mp3", "volume": 0.5}},   # legacy single-object shape
        ]})
        hs._select_scenario("data_vis", "x")
        out = hs._apply_mix(2.0, {"room1": {"room1/hum.mp3": -3}})
        assert out == {"music": True, "layers": 1, "solves": 0}
        disk = json.load(open(os.path.join(d, "scenario.json")))
        assert disk["musicVolume"] == 1.0                    # clamped high
        assert disk["rooms"][0]["sfx"]["volume"] == 0.0      # clamped low, shape preserved
    _with_rooms_root(body)


def test_apply_mix_no_music_no_op_when_nothing_matches():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {"rooms": [
            {"key": "room1", "sfx": [{"src": "room1/hum.mp3", "volume": 0.5}]},
        ]})
        hs._select_scenario("data_vis", "x")
        out = hs._apply_mix(None, {"room1": {"room1/ghost.mp3": 0.9}, "nope": {"a": 0.1}})
        assert out == {"music": False, "layers": 0, "solves": 0}
        # nothing matched and no music → no backup written (never touched the file)
        assert not os.path.exists(os.path.join(d, "scenario.json.bak"))
        assert json.load(open(os.path.join(d, "scenario.json")))["rooms"][0]["sfx"][0]["volume"] == 0.5
    _with_rooms_root(body)


# FAILURE MODE UNDER TEST — a solve/door sting had no volume slider in the mixer, so its volume could
# never be tuned. _apply_mix must now set the volume of a `solveSfx` matched by src, at whichever level
# defines it (gate hotspot / room / scenario), promoting a bare-string form to {src, volume}, touching
# nothing else, and never minting a spurious own copy on a gate that merely inherits the sting.

def test_apply_mix_solve_volume_by_src_across_levels():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {"rooms": [
            {"key": "room1", "solveSfx": "room1/door.mp3", "hotspots": [        # room-level, bare string
                {"id": "p1", "type": "puzzle", "solveSfx": {"src": "room1/ding.mp3", "volume": 0.4}},
                {"id": "p2", "type": "lock"},                                    # inherits room sting, no own
            ]},
            {"key": "room2", "hotspots": [{"id": "p3", "type": "puzzle"}]},      # falls back to scenario sting
        ], "solveSfx": {"src": "shared/chime.mp3", "volume": 0.5}})
        hs._select_scenario("data_vis", "x")
        out = hs._apply_mix(None, {}, solve_vols={
            "room1": {"room1/ding.mp3": 0.8, "room1/door.mp3": 0.2},
            "room2": {"shared/chime.mp3": 0.3},
        })
        assert out == {"music": False, "layers": 0, "solves": 3}
        disk = json.load(open(os.path.join(d, "scenario.json")))
        r1 = disk["rooms"][0]
        assert r1["hotspots"][0]["solveSfx"] == {"src": "room1/ding.mp3", "volume": 0.8}  # object updated
        assert r1["solveSfx"] == {"src": "room1/door.mp3", "volume": 0.2}                  # string promoted
        assert "solveSfx" not in r1["hotspots"][1]                                         # inheritor untouched
        assert disk["solveSfx"] == {"src": "shared/chime.mp3", "volume": 0.3}              # scenario level set
    _with_rooms_root(body)


# --- perceived-loudness auto-balance (_apply_balance) --------------------------------------------
# FAILURE MODE UNDER TEST — an effect that PLAYS louder than the music slips through. _apply_balance
# must lower ONLY effects whose played loudness (LUFS + 20log10(volume)) exceeds the music's played
# loudness, leave quieter ones alone, promote a bare-string solveSfx it lowers to {src, volume}, keep
# every other field, and (apply=False) compute without writing. Loudness measurement is stubbed so the
# test is deterministic and never shells out to ffmpeg.

def _stub_loudness(monkey_map):
    """Return a fake _audio_loudness keyed by src (dict src->LUFS); (None,None) for unknown/None."""
    def fake(base, src):
        v = monkey_map.get(src)
        return (v, "lufs") if v is not None else (None, None)
    return fake


def test_apply_balance_lowers_over_music_and_promotes_string():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {
            "music": "audio/m.mp3", "musicVolume": 0.5,
            "rooms": [{"key": "room1",
                       "sfx": [{"src": "audio/loud.mp3", "mode": "loop", "volume": 0.9, "duckMusicTo": 0.3},
                               {"src": "audio/quiet.mp3", "mode": "loop", "volume": 0.2}],
                       "hotspots": [{"id": "p", "type": "puzzle", "solveSfx": "audio/sting.mp3"}]}],
            "solveSfx": {"src": "audio/scen.mp3", "volume": 0.8},
        })
        # music −14 @ 0.5 → played −20.0. loud −6 & sting −10 play OVER it; quiet −40 & scen −30 sit under.
        loud = {"audio/m.mp3": -14.0, "audio/loud.mp3": -6.0, "audio/quiet.mp3": -40.0,
                "audio/sting.mp3": -10.0, "audio/scen.mp3": -30.0}
        orig = hs._audio_loudness
        hs._audio_loudness = _stub_loudness(loud)
        try:
            out = hs._apply_balance(d, apply=True)
        finally:
            hs._audio_loudness = orig
        assert out["nChanged"] == 2 and "error" not in out
        disk = json.load(open(os.path.join(d, "scenario.json")))
        r1 = disk["rooms"][0]
        assert abs(r1["sfx"][0]["volume"] - 0.199) < 0.002        # 0.5·10**((−14−−6)/20) ≈ 0.199
        assert r1["sfx"][0]["duckMusicTo"] == 0.3 and r1["sfx"][0]["mode"] == "loop"   # only volume moved
        assert r1["sfx"][1]["volume"] == 0.2                      # quiet layer untouched
        sting = r1["hotspots"][0]["solveSfx"]                     # string promoted to {src, volume}
        assert sting["src"] == "audio/sting.mp3" and abs(sting["volume"] - 0.316) < 0.002
        assert disk["solveSfx"] == {"src": "audio/scen.mp3", "volume": 0.8}   # already under music → untouched
    _with_rooms_root(body)


def test_apply_balance_dry_run_and_no_music():
    def body(tmp):
        # dry run computes but writes nothing
        d = _write_scenario("data_vis", "x", {"music": "audio/m.mp3", "musicVolume": 0.5, "rooms": [
            {"key": "room1", "sfx": [{"src": "audio/loud.mp3", "volume": 0.9}]}]})
        orig = hs._audio_loudness
        hs._audio_loudness = _stub_loudness({"audio/m.mp3": -14.0, "audio/loud.mp3": -6.0})
        try:
            out = hs._apply_balance(d, apply=False)
            assert out["nChanged"] == 1 and out["applied"] is False
            assert json.load(open(os.path.join(d, "scenario.json")))["rooms"][0]["sfx"][0]["volume"] == 0.9  # unwritten
            # no measurable music → error, nothing changed
            d2 = _write_scenario("data_vis", "y", {"rooms": [
                {"key": "room1", "sfx": [{"src": "audio/loud.mp3", "volume": 0.9}]}]})
            out2 = hs._apply_balance(d2, apply=True)
            assert out2.get("error") and out2["nChanged"] == 0
        finally:
            hs._audio_loudness = orig
    _with_rooms_root(body)


# INTEGRATION — exercises the REAL ffmpeg measurement path (the stubbed tests above can't catch an
# ffmpeg-invocation regression, e.g. the `framelog=quiet`-returns-0.0 bug that shipped 0.0 LUFS for
# every file during dev). Generates three sine tones — a music bed + a clearly-louder and a clearly-
# quieter effect — and asserts the loud one is lowered and the quiet one is left alone. Skips (no-op,
# so it's safe under both the plain-script runner and pytest) when ffmpeg isn't on PATH.

def test_apply_balance_real_ffmpeg_lowers_only_loud():
    import shutil
    import subprocess as _sp
    if not shutil.which("ffmpeg"):
        print("  skip test_apply_balance_real_ffmpeg_lowers_only_loud (no ffmpeg on PATH)")
        return

    def body(tmp):
        d = _write_scenario("data_vis", "x", {
            "music": "audio/music.wav", "musicVolume": 0.5,
            "rooms": [{"key": "room1", "sfx": [
                {"src": "audio/loud.wav", "mode": "loop", "volume": 1.0},
                {"src": "audio/quiet.wav", "mode": "loop", "volume": 1.0}]}]})
        adir = os.path.join(d, "audio")
        os.makedirs(adir, exist_ok=True)

        def tone(name, vol):
            _sp.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
                     "-filter:a", "volume=%s" % vol, os.path.join(adir, name)],
                    capture_output=True, check=True)

        tone("music.wav", 0.3)      # the bed
        tone("loud.wav", 0.9)       # plays well over the bed → must be lowered
        tone("quiet.wav", 0.02)     # far under the bed → left alone
        out = hs._apply_balance(d, apply=True)
        assert "error" not in out, out
        sfx = {l["src"]: l for l in json.load(open(os.path.join(d, "scenario.json")))["rooms"][0]["sfx"]}
        assert sfx["audio/loud.wav"]["volume"] < 1.0        # real LUFS measurement lowered it
        assert sfx["audio/quiet.wav"]["volume"] == 1.0      # quiet one untouched
    _with_rooms_root(body)


def test_commit_node_points_and_builds():
    """Committing points the node at images + marks built; seeds wrap from the passed seed_wrap
    (the candidate's tuned wrap), else a sane default so the room is ALWAYS playable (Finding 1
    belt); preserves other fields; no panoramaOpen when no _open was committed."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room2", "title": "R2", "built": False},
                                                    {"key": "room3", "title": "R3", "built": False}]})
        hs._select_scenario("data_vis", "x")
        node = hs._commit_node("room2", ["scene.png", "scene_open.png"], {"haov": 360, "vaov": 90})
        assert node["panorama"] == "room2/scene.png"
        assert node["panoramaOpen"] == "room2/scene_open.png"
        assert node["built"] is True
        assert node["wrap"] == {"haov": 360, "vaov": 90}   # seeded from seed_wrap
        assert node["title"] == "R2"                        # existing field preserved
        # no seed + no existing wrap -> sane default wrap (never leaves a wrapless built room)
        n3 = hs._commit_node("room3", ["scene.png"], None)
        assert n3["wrap"]["haov"] == 360 and "vaov" in n3["wrap"]
        assert "panoramaOpen" not in n3                     # no _open committed
    _with_rooms_root(body)


def test_add_room_appends_stub_linear():
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room1", "built": True}]})
        hs._select_scenario("data_vis", "x")
        node = hs._add_room("room2", title="Coast")
        assert node["key"] == "room2" and node["title"] == "Coast" and node["built"] is False
        assert node["unlockedWhen"] == {"solved": "room1"}          # linear on the previous room
        disk = json.load(open(os.path.join(hs.COMMIT_BASE, "scenario.json")))
        assert [r["key"] for r in disk["rooms"]] == ["room1", "room2"]
        try:
            hs._add_room("room2")                                    # duplicate rejected
            raise AssertionError("should reject duplicate room key")
        except ValueError:
            pass
    _with_rooms_root(body)


def test_new_scenario_scaffolds_fresh_id():
    def body(tmp):
        # an existing scenario with id 6 so the new one must jump past both it and the archived 1–5
        _write_scenario("data_vis", "alaska", {"id": 6, "rooms": [{"key": "room1"}]})
        info = hs._new_scenario("data_vis", "sierra", title="Snowmelt")
        assert info["chapter"] == "data_vis" and info["scenario"] == "sierra"
        assert info["id"] == 7                                        # max(6,5)+1
        p = os.path.join(hs.ROOMS_ROOT, "data_vis", "sierra", "scenario.json")
        doc = json.load(open(p))
        assert doc["title"] == "Snowmelt" and [r["key"] for r in doc["rooms"]] == ["room1"]
        assert os.path.isdir(os.path.join(hs.ROOMS_ROOT, "data_vis", "sierra", "_scratch"))
        try:
            hs._new_scenario("data_vis", "sierra")                    # already exists
            raise AssertionError("should reject an existing scenario")
        except ValueError:
            pass
    _with_rooms_root(body)


def test_room_patch_explicit_base_no_cross_scenario_clobber():
    """Finding 2: a patch with explicit chapter+scenario targets THAT scenario, not whatever is
    ACTIVE — even when both scenarios share a room key. No silent cross-scenario overwrite."""
    def body(tmp):
        _write_scenario("data_vis", "a", {"rooms": [{"key": "room1", "title": "A1"}]})
        _write_scenario("data_vis", "b", {"rooms": [{"key": "room1", "title": "B1"}]})
        hs._select_scenario("data_vis", "a")                         # ACTIVE = a
        base_b = hs._scenario_base("data_vis", "b")
        hs._room_patch("room1", {"title": "B1-edited"}, base_b)      # explicitly target b
        a = json.load(open(os.path.join(hs.ROOMS_ROOT, "data_vis", "a", "scenario.json")))
        b = json.load(open(os.path.join(hs.ROOMS_ROOT, "data_vis", "b", "scenario.json")))
        assert a["rooms"][0]["title"] == "A1"                        # ACTIVE scenario NOT clobbered
        assert b["rooms"][0]["title"] == "B1-edited"
        assert hs._scenario_base("", "") == hs.COMMIT_BASE           # blank -> active fallback
        try:
            hs._scenario_base("data_vis", "nope")                    # nonexistent rejected
            raise AssertionError("should reject nonexistent scenario")
        except ValueError:
            pass
    _with_rooms_root(body)


def test_commit_explicit_base_no_cross_scenario_commit():
    """Finding 2, commit leg: a commit given an explicit scenario base reads that scenario's
    _scratch pool and patches THAT scenario's node — even when another scenario is ACTIVE and
    both share room keys. Without the explicit base, a second board tab moving ACTIVE would
    commit tab one's pick into the wrong scenario."""
    def body(tmp):
        _write_scenario("data_vis", "a", {"rooms": [{"key": "room1", "built": False}]})
        _write_scenario("data_vis", "b", {"rooms": [{"key": "room1", "built": False}]})
        base_b = hs._scenario_base("data_vis", "b")
        scratch_b = os.path.join(base_b, "_scratch")
        os.makedirs(scratch_b, exist_ok=True)
        _png(os.path.join(scratch_b, "gpt_room1_1.png"))
        hs._select_scenario("data_vis", "a")                          # ACTIVE = a (empty scratch)
        room_dir = os.path.relpath(os.path.join(base_b, "room1"), hs.ESCAPE_ROOT)
        written, _, _ = hs._commit_room("gpt_room1_1.png", room_dir, scene=scratch_b)
        node = hs._commit_node("room1", written, None, base_b)
        assert node["built"] is True and node["panorama"] == "room1/scene.png"
        assert os.path.exists(os.path.join(base_b, "room1", "scene.png"))   # landed in b
        a = json.load(open(os.path.join(hs.ROOMS_ROOT, "data_vis", "a", "scenario.json")))
        assert a["rooms"][0]["built"] is False                        # ACTIVE scenario untouched
    _with_rooms_root(body)


def test_room_patch_concurrent_no_lost_update():
    """FAILURE MODE UNDER TEST — a lost update. Patches are load-modify-write and can run
    concurrently (ThreadingHTTPServer handlers + the door-open background thread's panoramaOpen
    patch). Without SAVE_LOCK two interleaved patches both load, then last-writer-wins — silently
    dropping the other's fields. Two threads patch DIFFERENT fields of the same room; both final
    values must survive."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room1"}]})
        hs._select_scenario("data_vis", "x")
        errs = []

        def worker(field):
            try:
                for i in range(40):
                    hs._room_patch("room1", {field: i})
            except Exception as e:  # noqa: BLE001
                errs.append(e)
        ta = threading.Thread(target=worker, args=("fieldA",))
        tb = threading.Thread(target=worker, args=("fieldB",))
        ta.start(); tb.start(); ta.join(); tb.join()
        assert not errs, errs
        node = json.load(open(os.path.join(hs.COMMIT_BASE, "scenario.json")))["rooms"][0]
        assert node.get("fieldA") == 39 and node.get("fieldB") == 39, node
    _with_rooms_root(body)


def test_draft_per_image_and_commit_promotes():
    """Per-candidate draft (2026-07-20): wrap/hotspots are stored under draft['imgs'][<image>], so
    different candidates keep INDEPENDENT progress (editing wrap on candidate A never bleeds into B).
    Commit promotes the COMMITTED candidate's wrap + hotspots onto the node and records `builtFrom`;
    the draft is then cleared.

    FAILURE MODE UNDER TEST — cross-candidate bleed. With one shared room-level wrap/hotspots blob,
    framing wrap on A then marking hotspots on B mismatched them; per-image keying prevents that."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room1", "title": "R1", "built": False}]})
        hs._select_scenario("data_vis", "x")
        # candidate A: hotspots then wrap (two tabs, both send image A) — both land under imgs[A]
        hs._draft_room_merge("room1", {"image": "gpt_room1_1.png",
                                       "hotspots": [{"id": "laptop", "type": "puzzle", "box": [0.4, 0.5, 0.5, 0.6]}]})
        hs._draft_room_merge("room1", {"image": "gpt_room1_1.png", "wrap": {"haov": 360, "vaov": 88}})
        # candidate B: a different wrap — must NOT touch A's entry
        hs._draft_room_merge("room1", {"image": "gpt_room1_2.png", "wrap": {"haov": 300, "vaov": 70}})
        d = hs._load_draft().get("room1")
        assert d["image"] == "gpt_room1_2.png"                          # last-picked selection
        assert d["imgs"]["gpt_room1_1.png"]["wrap"]["vaov"] == 88
        assert d["imgs"]["gpt_room1_1.png"]["hotspots"][0]["id"] == "laptop"
        assert d["imgs"]["gpt_room1_2.png"]["wrap"]["vaov"] == 70       # B independent of A
        assert "hotspots" not in d["imgs"]["gpt_room1_2.png"]           # B never got hotspots
        # commit candidate A (explicit image) → promotes A's wrap + hotspots, records builtFrom (not B's)
        node = hs._commit_node("room1", ["scene.png"], None, None, draft=d, image="gpt_room1_1.png")
        assert node["built"] is True and node["panorama"] == "room1/scene.png"
        assert node["builtFrom"] == "gpt_room1_1.png"
        assert node["wrap"] == {"haov": 360, "vaov": 88}               # A's wrap promoted, not B's
        assert node["hotspots"][0]["id"] == "laptop"
        hs._draft_clear("room1")
        assert "room1" not in hs._load_draft()
    _with_rooms_root(body)


def test_delete_scene_removes_files_and_state():
    """delete-scene removes a _scratch candidate + its `_open` partner, drops its wrap.json entry and
    its per-candidate draft state (imgs entry + a selection pointing at it), and rejects a
    non-png / traversal name — confined to _scratch, so a committed scene.png is never touched."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room1", "built": False}]})
        hs._select_scenario("data_vis", "x")
        base = hs.COMMIT_BASE
        scratch = os.path.join(base, "_scratch")
        os.makedirs(scratch, exist_ok=True)
        _png(os.path.join(scratch, "gpt_room1_1.png"))
        _png(os.path.join(scratch, "gpt_room1_1_open.png"))
        json.dump({"gpt_room1_1.png": {"haov": 360}}, open(os.path.join(scratch, "wrap.json"), "w"))
        hs._draft_room_merge("room1", {"image": "gpt_room1_1.png", "wrap": {"haov": 360}})
        removed = hs._delete_scene(base, "gpt_room1_1.png")
        assert set(removed) == {"gpt_room1_1.png", "gpt_room1_1_open.png"}
        assert not os.path.exists(os.path.join(scratch, "gpt_room1_1.png"))
        assert not os.path.exists(os.path.join(scratch, "gpt_room1_1_open.png"))
        assert "gpt_room1_1.png" not in json.load(open(os.path.join(scratch, "wrap.json")))
        d = hs._load_draft().get("room1", {})
        assert "gpt_room1_1.png" not in (d.get("imgs") or {})
        assert d.get("image") != "gpt_room1_1.png"
        for bad in ("../scenario.json", "notapng", ""):
            try:
                hs._delete_scene(base, bad)
                raise AssertionError(f"should reject {bad!r}")
            except ValueError:
                pass
    _with_rooms_root(body)


def test_set_cover_copies_and_patches():
    """set-cover copies a _scratch candidate to <scenario>/cover.png and points scenario.cover at it;
    an image name with path parts is confined to _scratch by basename, so it can't escape the tree."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room1", "built": False}]})
        hs._select_scenario("data_vis", "x")
        base = hs.COMMIT_BASE
        with open(os.path.join(hs.SCENE, "gpt_cover_1.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"x" * 20)          # dummy candidate in _scratch
        cover = hs._set_cover("gpt_cover_1.png", base)
        assert cover == "cover.png"
        assert os.path.isfile(os.path.join(base, "cover.png"))
        assert hs._load_scenario(base)["cover"] == "cover.png"
        try:
            hs._set_cover("../scenario.json", base)             # traversal -> basename -> not in _scratch
            raise AssertionError("should reject a traversal image name")
        except ValueError:
            pass
    _with_rooms_root(body)


# --- planned-content decoupling (author content BEFORE art) --------------------
# FAILURE MODE UNDER TEST — content that has to wait on art. Puzzle/clue content is authored on a
# room's plannedHotspots before any scene exists; at commit `_attach_planned_content` must copy it
# onto the placed box (matched by type+slug(label)) without clobbering placement, and a bare planned
# manifest must change nothing (so old-style post-commit wiring is unaffected).

def test_attach_planned_content_by_slug():
    planned = [
        {"type": "puzzle", "label": "The Laptop", "note": "design only",
         "starterCode": "trees", "question": {"prompt": "which?", "options": ["a", "b"], "correct": 1}},
        {"type": "clue", "label": "Field Notes", "body": "warm water lingers", "pickup": "a short line"},
        {"type": "door", "label": "North Door"},                       # bare manifest, no authored content
    ]
    placed = [
        {"id": "the_laptop", "type": "puzzle", "label": "The Laptop", "box": [0.1, 0.1, 0.2, 0.2],
         "starterCode": "", "check": {"prompt": "", "expr": ""}},       # empty skeleton, to be overwritten
        {"id": "field_notes", "type": "clue", "label": "Field Notes", "box": [0.3, 0.3, 0.4, 0.4], "body": ""},
        {"id": "north_door", "type": "door", "label": "North Door", "box": [0.5, 0, 0.6, 0.9], "direction": "forward"},
    ]
    out = hs._attach_planned_content(placed, planned)
    laptop = out[0]
    assert laptop["box"] == [0.1, 0.1, 0.2, 0.2] and laptop["id"] == "the_laptop"   # placement preserved
    assert laptop["starterCode"] == "trees" and laptop["question"]["correct"] == 1  # content copied
    assert "check" not in laptop                                        # planned chose question → drop skeleton
    assert "note" not in laptop                                         # design-only field never copied
    assert out[1]["body"] == "warm water lingers" and out[1]["pickup"] == "a short line"
    assert out[2] == {"id": "north_door", "type": "door", "label": "North Door",
                      "box": [0.5, 0, 0.6, 0.9], "direction": "forward"}  # bare manifest → unchanged
    # slug match is label-based: a relabelled box (different slug) inherits nothing
    out2 = hs._attach_planned_content([{"id": "x", "type": "puzzle", "label": "Renamed", "box": [0, 0, 1, 1]}], planned)
    assert "starterCode" not in out2[0]
    # no planned → identity
    same = [{"id": "y", "type": "clue", "label": "Z"}]
    assert hs._attach_planned_content(same, []) is same


def test_commit_attaches_planned_content():
    """End-to-end: content authored on plannedHotspots (pre-art) lands on the placed boxes at commit."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{
            "key": "room1", "title": "R1", "built": False,
            "plannedHotspots": [
                {"type": "puzzle", "label": "Monorail", "starterCode": "cars",
                 "question": {"prompt": "which grouping?", "options": ["a", "b", "c"], "correct": 2}},
                {"type": "clue", "label": "Ticket", "body": "each car used one grouping"},
            ],
        }]})
        hs._select_scenario("data_vis", "x")
        # box-marking draft: boxes carry only structural fields (what makeSpot seeds), no content yet
        hs._draft_room_merge("room1", {"image": "gpt_room1_1.png", "hotspots": [
            {"id": "monorail", "type": "puzzle", "label": "Monorail", "box": [0.4, 0.5, 0.5, 0.6], "starterCode": ""},
            {"id": "ticket", "type": "clue", "label": "Ticket", "box": [0.1, 0.1, 0.2, 0.2], "body": ""},
        ]})
        d = hs._load_draft().get("room1")
        node = hs._commit_node("room1", ["scene.png"], None, None, draft=d, image="gpt_room1_1.png")
        spots = {h["id"]: h for h in node["hotspots"]}
        assert spots["monorail"]["starterCode"] == "cars"              # planned content attached
        assert spots["monorail"]["question"]["correct"] == 2
        assert spots["monorail"]["box"] == [0.4, 0.5, 0.5, 0.6]        # placement preserved
        assert spots["ticket"]["body"] == "each car used one grouping"
    _with_rooms_root(body)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"all tests passed ({len(tests)})")
