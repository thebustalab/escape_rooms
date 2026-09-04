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


def test_valid_size():
    """Phase 1 native higher-res guard: accept panorama sizes, reject over-limit ones."""
    # accepted: current default, wide panorama, native 2x, square cover
    for s in ("1536x1024", "1536x512", "3072x1024", "1024x1024"):
        ok, msg = hs._valid_size(s)
        assert ok, f"{s} should be valid, got: {msg}"
    # rejected, one reason each
    assert hs._valid_size("3072x3072")[0] is False   # >8.29M px
    assert hs._valid_size("4000x1024")[0] is False    # edge >3840
    assert hs._valid_size("3072x1000")[0] is False    # not a multiple of 16
    assert hs._valid_size("3072x256")[0] is False     # aspect >3:1
    assert hs._valid_size("512x256")[0] is False       # <655360 px
    assert hs._valid_size("not-a-size")[0] is False    # unparseable
    assert hs._valid_size("1536")[0] is False          # missing axis


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
    for s in ("t1", "t2"):
        hs.JOBS.pop(s, None)


# FAILURE MODE UNDER TEST — a job slot wedged FOREVER by a thread body that dies before clearing it.
# JOBS lives in memory, so a claimed-and-never-released slot refuses every later job on it ("a variant
# job is already running") until the server is restarted, while /api/status reports active with no error
# and nothing is actually running. Hit for real on 2026-08-26: /api/gen-fullscene-variant's lambda
# dropped the leading `slot` arg, so every parameter shifted one place left, the body raised on a
# nonsense path, and its except handler then indexed JOBS by a filesystem path -> KeyError -> the
# thread died before `active = False`. Both halves are pinned: the lambda passes its slot, and _start
# releases the slot in a `finally` whatever the body does.

def test_start_releases_slot_when_body_raises():
    hs.JOBS.pop("t3", None)

    def boom():
        raise KeyError("/some/path/that/is/not/a/slot")

    assert hs._start("t3", "test", boom, 1) is True
    for _ in range(100):                       # the guard runs on the job thread
        if not hs.JOBS["t3"]["active"]:
            break
        time.sleep(0.01)
    assert hs.JOBS["t3"]["active"] is False, "a crashed job body must not wedge its slot"
    assert "crashed" in (hs.JOBS["t3"]["error"] or ""), "the crash must be reported, not silent"
    assert hs._start("t3", "test", lambda: None, 1) is True, "the slot must be re-claimable"
    time.sleep(0.05)
    hs.JOBS.pop("t3", None)


def test_fullscene_variant_lambda_passes_its_slot():
    """The dispatch lambda must hand _run_fullscene its slot name first, or every arg shifts left."""
    import inspect, re as _re
    src = inspect.getsource(hs)
    m = _re.search(r"lambda: _run_fullscene\(([^)]*)\)", src)
    assert m, "the /api/gen-fullscene-variant dispatch lambda is gone — retarget this guard"
    assert m.group(1).lstrip().startswith('"variant"'), \
        "_run_fullscene(slot, base, room_key, state, prompt, ...) — slot must be passed first"
    # and the call must satisfy the real signature positionally
    sig = inspect.signature(hs._run_fullscene)
    sig.bind("variant", "base", "rk", "state", "prompt", None, None)


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


# FAILURE MODE UNDER TEST — a DIAL's one-shot throw lives on the hotspot's `sfx`, not `solveSfx`, but
# pano-player's solveSounds() lists it in the mixer's "Solve / door sounds" section with a slider like
# any other sting. _apply_mix only ever looked at `solveSfx`, so moving that slider and hitting Save
# matched nothing, wrote nothing, and reported "saved ✓ nothing changed" — a silent no-op on a control
# the mixer had offered (2026-08-27, Lucas, on Egypt's deck cast-off / Pharos lamp dial). A room's own
# `sfx` must stay out of it: that's the ambience-layer list, handled by the `rooms` path.

def test_apply_mix_saves_a_dial_one_shot_which_lives_on_sfx_not_solvesfx():
    def body(tmp):
        d = _write_scenario("data_vis", "x", {"rooms": [
            {"key": "room1", "sfx": [{"src": "room1/hum.mp3", "volume": 0.5}], "hotspots": [
                {"id": "lever", "type": "dial", "sfx": {"src": "room1/throw.mp3", "volume": 0.8}},
                {"id": "bell", "type": "dial", "sfx": "room1/bell.mp3"},          # bare string form
            ]},
        ]})
        hs._select_scenario("data_vis", "x")
        out = hs._apply_mix(None, {}, solve_vols={
            "room1": {"room1/throw.mp3": 0.3, "room1/bell.mp3": 0.6,
                      "room1/hum.mp3": 0.1},        # the ROOM's ambience layer — must NOT count here
        })
        assert out == {"music": False, "layers": 0, "solves": 2}
        disk = json.load(open(os.path.join(d, "scenario.json")))
        hs_ = disk["rooms"][0]["hotspots"]
        assert hs_[0]["sfx"] == {"src": "room1/throw.mp3", "volume": 0.3}
        assert hs_[1]["sfx"] == {"src": "room1/bell.mp3", "volume": 0.6}   # string promoted
        assert disk["rooms"][0]["sfx"] == [{"src": "room1/hum.mp3", "volume": 0.5}]   # untouched
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


def test_set_world_plate_copies_and_patches():
    """Phase 2: set-world-plate copies a _scratch candidate to <scenario>/_world/plate.png and points
    scenario.worldPlate at it; _world_plate_abs reports None until it exists, then the path. A name
    with path parts is confined to _scratch by basename, so it can't escape the tree."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [{"key": "room1", "built": False}]})
        hs._select_scenario("data_vis", "x")
        base = hs.COMMIT_BASE
        assert hs._world_plate_abs(base) is None                 # none set yet
        with open(os.path.join(hs.SCENE, "gpt_room1_3.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"x" * 20)             # dummy candidate in _scratch
        plate = hs._set_world_plate("gpt_room1_3.png", base)
        assert plate == "_world/plate.png"
        assert os.path.isfile(os.path.join(base, "_world", "plate.png"))
        assert hs._load_scenario(base)["worldPlate"] == "_world/plate.png"
        assert hs._world_plate_abs(base) == os.path.join(base, "_world", "plate.png")
        try:
            hs._set_world_plate("../scenario.json", base)        # traversal -> basename -> not in _scratch
            raise AssertionError("should reject a traversal image name")
        except ValueError:
            pass
    _with_rooms_root(body)


def test_variant_add_remove():
    """Phase 3: _add_variant writes nested into hotspots[].variants (idempotent per state),
    _remove_variant drops by state, and a missing room/hotspot raises ValueError."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [
            {"key": "room1", "built": True, "hotspots": [
                {"id": "lever", "type": "puzzle", "box": [0.1, 0.1, 0.2, 0.2]}]}]})
        hs._select_scenario("data_vis", "x")
        base = hs.COMMIT_BASE
        spot_of = lambda: next(h for h in hs._load_scenario(base)["rooms"][0]["hotspots"] if h["id"] == "lever")
        v = {"state": "thrown", "box": [0.1, 0.1, 0.2, 0.2], "prompt": "lever thrown",
             "panorama": "room1/var_lever_thrown.png"}
        hs._add_variant("room1", "lever", v, base)
        assert spot_of()["variants"][0]["state"] == "thrown"
        hs._add_variant("room1", "lever", {**v, "prompt": "changed"}, base)      # same state → merge new fields
        assert len(spot_of()["variants"]) == 1 and spot_of()["variants"][0]["prompt"] == "changed"
        hs._add_variant("room1", "lever", {**v, "state": "broken",
                                           "panorama": "room1/var_lever_broken.png"}, base)  # new state → append
        assert {x["state"] for x in spot_of()["variants"]} == {"thrown", "broken"}
        # _update_variant tunes the trigger without regenerating the image
        hs._update_variant("room1", "lever", "broken", {"when": {"solved": "room2"}}, base)
        broken = next(x for x in spot_of()["variants"] if x["state"] == "broken")
        assert broken["when"] == {"solved": "room2"} and broken["panorama"] == "room1/var_lever_broken.png"
        try:
            hs._update_variant("room1", "lever", "ghost", {"when": True}, base)
            raise AssertionError("should reject a missing variant state")
        except ValueError:
            pass
        hs._remove_variant("room1", "lever", "broken", base)
        assert {x["state"] for x in spot_of()["variants"]} == {"thrown"}
        try:
            hs._add_variant("room1", "nope", v, base)
            raise AssertionError("should reject a missing hotspot")
        except ValueError:
            pass
    _with_rooms_root(body)


def test_cinemagraph_pool_pick_uncommit_delete():
    """The cinemagraph POOL model (2026-08-06): picking marks a candidate ACTIVE but KEEPS the pool (store-
    but-deploy is a toggle); un-committing drops only the active pointer; deleting a candidate removes it and,
    if it was the active one, also clears `cinemagraph`. Regression for the old behaviour that deleted the
    whole pool on pick."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [
            {"key": "room1", "built": True, "hotspots": [
                {"id": "lantern", "type": "ambient", "box": [0.1, 0.1, 0.2, 0.2], "cinemagraphCandidates": [
                    {"video": "room1/a.mp4", "loop": "boomerang", "box": [0.1, 0.1, 0.2, 0.2]},
                    {"video": "room1/b.mp4", "loop": "boomerang", "box": [0.1, 0.1, 0.2, 0.2]},
                    {"video": "room1/c.mp4", "loop": "crossfade", "box": [0.1, 0.1, 0.2, 0.2]}]}]}]})
        hs._select_scenario("data_vis", "x")
        base = hs.COMMIT_BASE
        spot = lambda: next(h for h in hs._load_scenario(base)["rooms"][0]["hotspots"] if h["id"] == "lantern")
        # pick candidate 1 → active, POOL KEPT
        hs._pick_cinemagraph("room1", "lantern", 1, base)
        assert spot()["cinemagraph"]["video"] == "room1/b.mp4"
        assert len(spot()["cinemagraphCandidates"]) == 3          # NOT cleared
        # un-commit → active dropped, pool kept
        hs._remove_cinemagraph("room1", "lantern", base)
        assert "cinemagraph" not in spot() and len(spot()["cinemagraphCandidates"]) == 3
        # delete a NON-active candidate → pool shrinks, no active affected
        hs._pick_cinemagraph("room1", "lantern", 0, base)         # a.mp4 active
        hs._delete_cinemagraph_candidate("room1", "lantern", 2, base)   # delete c.mp4 (not active)
        assert len(spot()["cinemagraphCandidates"]) == 2 and spot()["cinemagraph"]["video"] == "room1/a.mp4"
        # delete the ACTIVE candidate → it's removed AND the active pointer clears
        hs._delete_cinemagraph_candidate("room1", "lantern", 0, base)   # a.mp4 was active
        assert len(spot()["cinemagraphCandidates"]) == 1 and "cinemagraph" not in spot()
    _with_rooms_root(body)


def test_uncommit_folds_standalone_active_into_pool():
    """Un-checking (✓ off) must NEVER lose a clip. A legacy single-committed clip lives ONLY in `cinemagraph`
    with no pool entry; un-committing folds it into the pool first, then clears the active pointer — so it
    stays visible as a stored candidate. Regression for the vanishing-cinemagraph bug (trees boss, 2026-08-06)."""
    def body(tmp):
        _write_scenario("data_vis", "x", {"rooms": [
            {"key": "room1", "built": True, "hotspots": [
                {"id": "motes", "type": "ambient", "box": [0.3, 0.3, 0.4, 0.4],
                 "cinemagraph": {"video": "room1/motes.mp4", "loop": "boomerang", "box": [0.3, 0.3, 0.4, 0.4],
                                 "prompt": "motes drifting", "seed": 42}}]}]})   # standalone active, NO pool
        hs._select_scenario("data_vis", "x")
        base = hs.COMMIT_BASE
        spot = lambda: next(h for h in hs._load_scenario(base)["rooms"][0]["hotspots"] if h["id"] == "motes")
        hs._uncommit_cinemagraph("room1", "motes", base)
        s = spot()
        assert "cinemagraph" not in s                                   # un-deployed
        assert len(s.get("cinemagraphCandidates", [])) == 1             # but FOLDED into the pool, not lost
        assert s["cinemagraphCandidates"][0]["video"] == "room1/motes.mp4"
        assert s["cinemagraphCandidates"][0]["prompt"] == "motes drifting"   # metadata preserved
        # re-deploy from the pool, then a plain hard-remove leaves the pool intact (that path is the ✕ on a standalone)
        hs._pick_cinemagraph("room1", "motes", 0, base)
        assert spot().get("cinemagraph", {}).get("video") == "room1/motes.mp4" and len(spot()["cinemagraphCandidates"]) == 1
    _with_rooms_root(body)


def test_add_variant_merges_onto_switch_door_nav():
    """_add_variant MERGES the generated door-open ART onto a hand-wired SWITCH-DOOR nav variant instead of
    replacing it — so a monorail car's `{state, when, to, direction}` (no art yet) KEEPS its to/direction/when
    when the art step paints the reveal in and adds panorama/box/prompt for the same state. Regression for the
    art-clobbers-nav bug (2026-08-05): without the merge, generating the door view would drop where the door
    leads. Order-independent (nav first here; the reverse composes the same way)."""
    def body(tmp):
        _write_scenario("wrangling", "trees", {"rooms": [
            {"key": "car_sq", "built": True, "hotspots": [
                {"id": "square_door", "type": "door", "box": [0.7, 0.1, 0.8, 0.9], "direction": "open",
                 "to": "station2", "variants": [
                     {"state": "to_station2", "when": {"eq": ["car_sq_dir", "forward"]}, "to": "station2", "direction": "open"},
                     {"state": "to_station1", "when": {"eq": ["car_sq_dir", "back"]}, "to": "station1", "direction": "back"}]}]}]})
        hs._select_scenario("wrangling", "trees")
        base = hs.COMMIT_BASE
        # the art step attaches a state-tagged reveal (what _run_variant builds) for the SAME state
        hs._add_variant("car_sq", "square_door",
                        {"state": "to_station2", "box": [0.7, 0.1, 0.8, 0.9],
                         "prompt": "open onto station two", "panorama": "car_sq/var_square_door_to_station2.png"}, base)
        door = next(h for h in hs._load_scenario(base)["rooms"][0]["hotspots"] if h["id"] == "square_door")
        fv = next(v for v in door["variants"] if v["state"] == "to_station2")
        assert fv["to"] == "station2" and fv["direction"] == "open"          # nav SURVIVED the art attach
        assert fv["when"] == {"eq": ["car_sq_dir", "forward"]}               # gating survived
        assert fv["panorama"] == "car_sq/var_square_door_to_station2.png"    # art added
        assert len(door["variants"]) == 2                                    # no duplicate; the back variant untouched
        bv = next(v for v in door["variants"] if v["state"] == "to_station1")
        assert bv["to"] == "station1" and "panorama" not in bv              # the un-generated state is left alone
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


# --- build-world level-1 candidate panos (up to MAX per room) -------------------
# FAILURE MODE UNDER TEST — the multi-candidate pano model. A room keeps up to
# MAX_PANO_CANDIDATES candidates in _scratch (l1_<room>_<n>.png). The listing must
# order indexed candidates by n and keep a legacy no-index pano visible; the next
# index must FILL A GAP left by a delete (not blindly append); and the candidate
# name-match must exclude the _preseam/_seamtmp siblings so deleting/committing
# can't be tricked onto a sibling or a path-escape.

def test_pano_candidates_and_gap_fill():
    with tempfile.TemporaryDirectory() as base:
        scratch = os.path.join(base, "_scratch")
        os.makedirs(scratch)
        for n in (1, 3):                       # two indexed candidates + a seam sibling that must be ignored
            _png(os.path.join(scratch, "l1_car_sq_%d.png" % n))
        _png(os.path.join(scratch, "l1_car_sq_1_preseam.png"))
        assert hs._pano_candidates(base, "car_sq") == ["l1_car_sq_1.png", "l1_car_sq_3.png"]
        assert hs._next_pano_idx(base, "car_sq") == 2          # fills the gap, not 4
        _png(os.path.join(scratch, "l1_car_sq_2.png"))
        assert hs._next_pano_idx(base, "car_sq") is None       # 3 used -> full
        assert len(hs._pano_candidates(base, "car_sq")) == hs.MAX_PANO_CANDIDATES


def test_pano_candidates_keeps_legacy_single():
    with tempfile.TemporaryDirectory() as base:
        scratch = os.path.join(base, "_scratch")
        os.makedirs(scratch)
        _png(os.path.join(scratch, "l1_boss.png"))             # pre-multi-candidate pano
        _png(os.path.join(scratch, "l1_boss_1.png"))
        assert hs._pano_candidates(base, "boss") == ["l1_boss_1.png", "l1_boss.png"]
        # a room-key prefix must not leak across rooms (l1_boss* vs l1_boss2*)
        _png(os.path.join(scratch, "l1_boss2_1.png"))
        assert hs._pano_candidates(base, "boss") == ["l1_boss_1.png", "l1_boss.png"]


def test_delete_room_pano_rejects_siblings_and_escape():
    with tempfile.TemporaryDirectory() as base:
        scratch = os.path.join(base, "_scratch")
        os.makedirs(scratch)
        _png(os.path.join(scratch, "l1_vault_1.png"))
        _png(os.path.join(scratch, "l1_vault_1_undo0.png"))
        _png(os.path.join(scratch, "l1_vault_1_undo1.png"))
        for bad in ("l1_vault_1_undo0.png", "../scenario.json", "l1_other_1.png", ""):
            try:
                hs._delete_room_pano(base, "vault", bad)
                raise AssertionError("should have rejected %r" % bad)
            except ValueError:
                pass
        # deleting the candidate also sweeps its whole undo stack
        out = hs._delete_room_pano(base, "vault", "l1_vault_1.png")
        assert "l1_vault_1.png" in out["removed"]
        assert "l1_vault_1_undo0.png" in out["removed"] and "l1_vault_1_undo1.png" in out["removed"]
        assert not os.path.isfile(os.path.join(scratch, "l1_vault_1.png"))


def test_seamfix_argv_threads_left_right():
    """The seam band passes independent left/right band extents + a feather radius; _seamfix_argv must
    append each flag only when supplied (absent → generate_scene falls back to symmetric --width + auto
    feather). Regression for the asymmetric seam-strip + feather control (2026-08-05)."""
    base = hs._seamfix_argv("in.png", "out.png")
    assert "--left" not in base and "--right" not in base and "--feather" not in base   # all fallback
    both = hs._seamfix_argv("in.png", "out.png", 0.03, 0.09, 0.02)
    assert both[both.index("--left") + 1] == "0.03"
    assert both[both.index("--right") + 1] == "0.09"
    assert both[both.index("--feather") + 1] == "0.02"
    one = hs._seamfix_argv("in.png", "out.png", 0.05, None)
    assert "--left" in one and "--right" not in one and "--feather" not in one and "--full" not in one
    off = hs._seamfix_argv("in.png", "out.png", None, None, 0.0)   # feather OFF is an explicit 0, not "falsy → skip"
    assert off[off.index("--feather") + 1] == "0.0"
    full = hs._seamfix_argv("in.png", "out.png", None, None, None, True)   # full = whole-output mode (flag, no value)
    assert "--full" in full
    pos = hs._seamfix_argv("in.png", "out.png", None, None, 0.0, False, 0.5)   # fix a mid-image seam
    assert pos[pos.index("--pos") + 1] == "0.5"


def test_seam_bounds_clamps_and_filters():
    """Band params are clamped (left/right to 0.45, feather to 0.1); junk / non-positive values drop to
    None so the run uses the symmetric/auto fallback rather than a broken strip."""
    assert hs._seam_bounds({"left": 0.06, "right": 0.06}) == (0.06, 0.06, None, False, None)
    assert hs._seam_bounds({"left": 9.0, "right": 0.0, "feather": 5}) == (0.9, None, 0.1, False, None)   # over-caps clamped; side 0 → None
    # The side cap is 0.9, not 0.45 (raised 2026-08-07 so the band reaches the whole frame — it doubles as
    # the region selector for patch/occluder). A 0.45 here again means the UI's reach was silently halved.
    assert hs._seam_bounds({"left": 0.8, "right": 0.75}) == (0.8, 0.75, None, False, None)
    assert hs._seam_bounds({"feather": 0.02}) == (None, None, 0.02, False, None)    # feather alone is fine
    assert hs._seam_bounds({"feather": 0}) == (None, None, 0.0, False, None)        # feather 0 KEPT (OFF), not dropped to auto
    assert hs._seam_bounds({"feather": -1}) == (None, None, None, False, None)      # negative feather → None (auto)
    assert hs._seam_bounds({"full": True}) == (None, None, None, True, None)        # whole-output mode toggle
    assert hs._seam_bounds({"pos": 0.5}) == (None, None, None, False, 0.5)          # target a mid-image seam
    assert hs._seam_bounds({"pos": 9}) == (None, None, None, False, 1.0)            # pos clamped to [0,1]
    assert hs._seam_bounds({"left": "x"}) == (None, None, None, False, None)        # unparseable → None
    assert hs._seam_bounds({}) == (None, None, None, False, None)                   # absent → symmetric/auto/composite fallback at the wrap


def test_seam_undo_stack_scratch():
    """Each seam-fix stage pushes one undo snapshot; undo pops back stage-by-stage (stage 2 → stage-1 result
    → original), not all the way at once. Regression for the per-stage undo stack (2026-08-05)."""
    with tempfile.TemporaryDirectory() as base:
        scratch = os.path.join(base, "_scratch")
        os.makedirs(scratch)
        img = os.path.join(scratch, "l1_s3_3.png")

        def write(s):
            with open(img, "wb") as f:
                f.write(s)

        def read():
            with open(img, "rb") as f:
                return f.read()

        write(b"ORIG")
        hs._seam_push(scratch, "l1_s3_3", img); write(b"STAGE1")   # stage 1
        hs._seam_push(scratch, "l1_s3_3", img); write(b"STAGE2")   # stage 2
        assert hs._seam_depth(scratch, "l1_s3_3") == 2
        assert hs._undo_seam_scratch(base, "l1_s3_3.png")["depth"] == 1   # undo stage 2 …
        assert read() == b"STAGE1"                                        # … → stage-1 result, NOT original
        assert hs._undo_seam_scratch(base, "l1_s3_3.png")["depth"] == 0   # undo stage 1 …
        assert read() == b"ORIG"                                          # … → original
        for bad in ("l1_s3_3.png", "l1_s3_3_undo0.png", "l1_s3_3.txt", ""):
            try:
                hs._undo_seam_scratch(base, bad)   # empty stack / snapshot input / non-png / empty
                raise AssertionError("should have rejected %r" % bad)
            except ValueError:
                pass


def test_seam_undo_room():
    """Committed-room per-stage undo: each fix pushes a scene snapshot; undo pops one back. Empty → raises."""
    with tempfile.TemporaryDirectory() as base:
        d = os.path.join(base, "station3")
        os.makedirs(d)
        scene = os.path.join(d, "scene.png")
        with open(scene, "wb") as f:
            f.write(b"ORIG")
        hs._seam_push(d, "scene", scene)
        with open(scene, "wb") as f:
            f.write(b"FIX")
        assert hs._seam_depth(d, "scene") == 1
        assert hs._undo_seam_room(base, "station3")["depth"] == 0
        with open(scene, "rb") as f:
            assert f.read() == b"ORIG"
        try:
            hs._undo_seam_room(base, "station3")   # empty stack now
            raise AssertionError("empty stack should raise")
        except ValueError:
            pass


def test_cover_spec_bundle_roundtrips():
    """The scenario-level `cover` key in the spec bundle → scenario.json coverPrompt/title/ambient, and it
    round-trips back out via _scene_specs. Regression for cover+landing in the spec (2026-08-05)."""
    with tempfile.TemporaryDirectory() as base:
        with open(os.path.join(base, "scenario.json"), "w") as f:
            json.dump({"rooms": [{"key": "r1"}]}, f)
        hs._save_scene_specs(base, {"cover": {"prompt": "a poster", "title": "The Vault", "ambient": "embers"}})
        doc = json.load(open(os.path.join(base, "scenario.json")))
        assert doc["coverPrompt"] == "a poster" and doc["title"] == "The Vault" and doc["ambient"] == "embers"
        bundle = hs._scene_specs(base)
        assert bundle["cover"] == {"prompt": "a poster", "title": "The Vault", "ambient": "embers"}
        # a non-object cover is rejected, not crashed
        out = hs._save_scene_specs(base, {"cover": "oops"})
        assert "error" in out["cover"]


def test_story_spec_bundle_roundtrips():
    """The scenario-level `story` key → scenario.json story/enterLabel/done/escapeDone + per-room entry, and
    round-trips back out. Lets the whole narrative be authored in the spec (2026-08-05)."""
    with tempfile.TemporaryDirectory() as base:
        with open(os.path.join(base, "scenario.json"), "w") as f:
            json.dump({"rooms": [{"key": "r1"}, {"key": "r2"}]}, f)
        hs._save_scene_specs(base, {"story": {
            "opening": "You wake in a vault.", "enterLabel": "Begin",
            "analysisFinish": {"title": "Solved", "body": "the analysis is done"},
            "escapeFinish": {"title": "Free", "body": "you escape"},
            "entries": {"r2": {"title": "Room two", "text": "onward"}},
        }})
        doc = json.load(open(os.path.join(base, "scenario.json")))
        assert doc["story"] == "You wake in a vault." and doc["enterLabel"] == "Begin"
        assert doc["done"]["title"] == "Solved" and doc["escapeDone"]["body"] == "you escape"
        assert doc["rooms"][1]["entry"] == {"title": "Room two", "text": "onward"}
        bundle = hs._scene_specs(base)
        assert bundle["story"]["opening"] == "You wake in a vault."
        assert bundle["story"]["entries"]["r2"]["text"] == "onward"


def test_story_flow_puzzle_prompts_surface_and_write_back():
    """The build-world story flow surfaces every editable puzzle prompt in room order (committed hotspots are
    the truth; a plannedHotspot only shows when no committed puzzle of the same label exists), and a bulk save
    writes each edit back into its own nested field — question.prompt / check.prompt / pick.instructions —
    without disturbing the rest of the hotspot. Regression for the editable story flow (2026-08-05)."""
    with tempfile.TemporaryDirectory() as base:
        doc = {"rooms": [
            {"key": "r1", "hotspots": [
                {"id": "p1", "type": "puzzle", "label": "Laptop", "question": {"prompt": "How many?", "options": ["a", "b"], "correct": 0}},
                {"id": "c1", "type": "clue", "label": "note", "body": "x"},
            ]},
            {"key": "r2", "hotspots": [
                {"id": "p2", "type": "puzzle", "label": "Console", "check": {"prompt": "Filter it.", "expr": "nrow(x)"}},
                {"id": "pk", "type": "puzzle", "label": "Basin", "pick": {"prompt": "Click your lake.", "answer": "L", "plotCode": "p"}},
            ]},
            {"key": "r3", "plannedHotspots": [   # unbuilt room — prompt lives on the planned stub
                {"type": "puzzle", "label": "Beacon", "question": {"prompt": "Which is warmest?"}},
            ]},
        ]}
        with open(os.path.join(base, "scenario.json"), "w") as f:
            json.dump(doc, f)
        st = hs._scenario_state(base)
        pp = {r["key"]: r["puzzlePrompts"] for r in st["rooms"]}
        assert [x["kind"] for x in pp["r1"]] == ["mcq"] and pp["r1"][0]["prompt"] == "How many?"
        assert [x["kind"] for x in pp["r2"]] == ["check", "pick"]
        assert pp["r3"][0]["source"] == "plannedHotspots" and pp["r3"][0]["prompt"] == "Which is warmest?"
        # bulk write-back: one edit per kind + the planned one
        res = hs._set_puzzle_prompts(base, [
            {"roomKey": "r1", "source": "hotspots", "index": 0, "prompt": "How many now?"},
            {"roomKey": "r2", "source": "hotspots", "index": 0, "prompt": "Filter it better."},
            {"roomKey": "r2", "source": "hotspots", "index": 1, "prompt": "Click your NEW lake."},
            {"roomKey": "r3", "source": "plannedHotspots", "index": 0, "prompt": "Which is coldest?"},
        ])
        assert res["updated"] == 4 and not res["errors"]
        disk = json.load(open(os.path.join(base, "scenario.json")))
        rr = {r["key"]: r for r in disk["rooms"]}
        assert rr["r1"]["hotspots"][0]["question"]["prompt"] == "How many now?"
        assert rr["r1"]["hotspots"][0]["question"]["options"] == ["a", "b"]   # siblings untouched
        assert rr["r2"]["hotspots"][0]["check"]["prompt"] == "Filter it better."
        assert rr["r2"]["hotspots"][0]["check"]["expr"] == "nrow(x)"
        assert rr["r2"]["hotspots"][1]["pick"]["prompt"] == "Click your NEW lake."
        assert rr["r2"]["hotspots"][1]["pick"]["plotCode"] == "p"   # pick siblings untouched
        assert rr["r3"]["plannedHotspots"][0]["question"]["prompt"] == "Which is coldest?"
        # a bad index is reported, not fatal, and doesn't corrupt the file
        bad = hs._set_puzzle_prompts(base, [{"roomKey": "r1", "source": "hotspots", "index": 9, "prompt": "z"}])
        assert bad["updated"] == 0 and bad["errors"][0]["error"]


def test_story_flow_clues_surface_and_write_back():
    """The build-world story flow surfaces every clue's player-facing `body` in room order (committed hotspots
    are the truth; a plannedHotspot clue only shows when no committed clue of the same label exists yet), and a
    bulk save writes each edit back into that clue's `body` without disturbing sibling fields. A non-clue index
    is rejected per-item, not fatal. Regression for clues in the editable story flow (2026-08-06)."""
    with tempfile.TemporaryDirectory() as base:
        doc = {"rooms": [
            {"key": "r1", "hotspots": [
                {"id": "c1", "type": "clue", "label": "Field-card", "body": "the beetles", "pickup": True},
                {"id": "p1", "type": "puzzle", "label": "Laptop", "question": {"prompt": "How many?"}},
            ]},
            {"key": "r2", "plannedHotspots": [   # unbuilt room — clue body authored on the planned stub
                {"type": "clue", "label": "Compass", "note": "design-only", "body": "orthogonal headings"},
            ]},
        ]}
        with open(os.path.join(base, "scenario.json"), "w") as f:
            json.dump(doc, f)
        st = hs._scenario_state(base)
        cl = {r["key"]: r["clues"] for r in st["rooms"]}
        assert [c["label"] for c in cl["r1"]] == ["Field-card"] and cl["r1"][0]["body"] == "the beetles"
        assert cl["r2"][0]["source"] == "plannedHotspots" and cl["r2"][0]["planned"] and cl["r2"][0]["body"] == "orthogonal headings"
        # bulk write-back: committed + planned
        res = hs._set_clues(base, [
            {"roomKey": "r1", "source": "hotspots", "index": 0, "body": "the gleam-beetles again"},
            {"roomKey": "r2", "source": "plannedHotspots", "index": 0, "body": "two headings, 90° apart"},
        ])
        assert res["updated"] == 2 and not res["errors"]
        disk = json.load(open(os.path.join(base, "scenario.json")))
        rr = {r["key"]: r for r in disk["rooms"]}
        assert rr["r1"]["hotspots"][0]["body"] == "the gleam-beetles again"
        assert rr["r1"]["hotspots"][0]["pickup"] is True   # sibling field untouched
        assert rr["r2"]["plannedHotspots"][0]["body"] == "two headings, 90° apart"
        assert rr["r2"]["plannedHotspots"][0]["note"] == "design-only"   # design note untouched
        # pointing at a non-clue hotspot is reported, not fatal
        bad = hs._set_clues(base, [{"roomKey": "r1", "source": "hotspots", "index": 1, "body": "z"}])
        assert bad["updated"] == 0 and "not a clue" in bad["errors"][0]["error"]


def test_apply_spec_queue_accounting_and_candidate_skip():
    """'Place all hotspots' (_apply_spec) counts cinemagraph vs door-open-VARIANT jobs separately, and does
    NOT re-queue a cinemagraph for an element that already has an activated clip OR an unpicked candidate pool
    (the author left all 5 candidates unpicked because none were liked — re-generating is a per-hotspot action,
    not a side effect of re-running). Regression for the over-queue + mislabelled 'N cinemagraphs' count
    (2026-08-06)."""
    with tempfile.TemporaryDirectory() as base:
        spec = {"room": "r1", "elements": [
            {"id": "mist", "at": "on the left", "desc": "drifting mist",
             "animate": {"motion": "mist drifting", "loop": "crossfade"}},
            {"id": "lanterns", "at": "to the right", "desc": "swaying lanterns",
             "animate": {"motion": "lanterns swaying", "loop": "boomerang"}},
            {"id": "door1", "at": "dead ahead", "desc": "a sliding door",
             "door": {"direction": "forward", "to": "r2",
                      "opensOnto": [{"state": "open", "reveal": "the door slides open onto the room beyond"}]}},
        ]}
        doc = {"rooms": [{
            "key": "r1", "panorama": "r1/scene.png",       # built → hotspots carry real boxes
            "authoring": {"sceneSpec": spec},
            # 'lanterns' already has a candidate POOL but no activated clip — must NOT be re-queued.
            "hotspots": [{"id": "lanterns", "type": "ambient", "box": [0.7, 0.25, 0.86, 0.8],
                          "cinemagraphCandidates": [{"video": "r1/l1.mp4"}, {"video": "r1/l2.mp4"}]}],
        }]}
        with open(os.path.join(base, "scenario.json"), "w") as f:
            json.dump(doc, f)
        res = hs._apply_spec(base, "r1")
        # BOX CINEMAGRAPHS RETIRED (2026-09-02): motion is baked whole-scene from `motionSpec`, so no
        # per-object job is queued for an `animate` element and no `ambient` carrier is created for one.
        # This test previously asserted `queuedCine == ["mist"]`; it now pins the retirement instead.
        # The VARIANT half is untouched and still asserted — a door-open reveal is a boxed reveal, not
        # motion, and it must keep being queued and counted separately.
        assert res["queuedCine"] == [], res["queuedCine"]
        assert "mist" in res["skipped"] and "lanterns" in res["skipped"]
        assert res["queuedVar"] == ["door1:open"]      # door-open reveal is a VARIANT, counted separately
        q = hs._batch_read_queue(base)
        assert sum(1 for j in q if j["type"] == "cinemagraph") == 0
        assert sum(1 for j in q if j["type"] == "variant") == 1
        node = next(r for r in json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))["rooms"]
                    if r["key"] == "r1")
        assert not [h for h in node["hotspots"] if h.get("id") == "mist"], "animate must create no hotspot"
        # idempotent: a second run queues nothing (mist already queued, lanterns still has candidates)
        res2 = hs._apply_spec(base, "r1")
        assert res2["queuedCine"] == [] and res2["queuedVar"] == []


def test_set_review_flag_whitelist_and_persist():
    """Per-room review flags persist on the node's authoring; unknown flags and unknown rooms raise.
    Regression for the build-world placed/verified ✓ columns (2026-08-05)."""
    with tempfile.TemporaryDirectory() as base:
        with open(os.path.join(base, "scenario.json"), "w") as f:
            json.dump({"rooms": [{"key": "station2", "title": "S2"}]}, f)
        out = hs._set_review_flag(base, "station2", "hotspotsReviewed", True)
        assert out["value"] is True
        doc = json.load(open(os.path.join(base, "scenario.json")))
        assert doc["rooms"][0]["authoring"]["hotspotsReviewed"] is True
        hs._set_review_flag(base, "station2", "hotspotsReviewed", False)   # toggle back off
        doc = json.load(open(os.path.join(base, "scenario.json")))
        assert doc["rooms"][0]["authoring"]["hotspotsReviewed"] is False
        for field, rk in (("bogusFlag", "station2"), ("hotspotsReviewed", "nope")):
            try:
                hs._set_review_flag(base, rk, field, True)
                raise AssertionError("should have rejected %r/%r" % (rk, field))
            except ValueError:
                pass


# ---- seam targeting: scene.png, or a state VARIANT (2026-08-13) -----------------------------------
# Seam repair used to be hard-wired to scene.png, so a night/weather variant whose unmasked re-light had
# broken the wrap seam could not be fixed at all. `room_target` is the resolver that opened that up — and
# because `file` arrives from a query string, it is also the guard.

def _room_with(files):
    """Run a body with a temp rooms tree holding rooms/ch/sc/r1/<files>; yields the scenario base dir."""
    out = {}

    def body(tmp):
        d = _write_scenario("ch", "sc", {"title": "T", "rooms": [{"key": "r1"}]})
        os.makedirs(os.path.join(d, "r1"), exist_ok=True)
        for f in files:
            _png(os.path.join(d, "r1", f))
        out["base"] = d
        out["result"] = out["fn"](d)
    return body, out


def _run_room_target_case(files, fn):
    body, out = _room_with(files)
    out["fn"] = fn
    _with_rooms_root(body)
    return out.get("result")


def test_room_target_defaults_to_the_committed_scene():
    """Seam tools with no `file` must behave exactly as before — scene.png, undo stem "scene"."""
    p, stem = _run_room_target_case(["scene.png"], lambda base: hs.room_target(base, "r1", None))
    assert os.path.basename(p) == "scene.png", p
    assert stem == "scene", stem


def test_room_target_selects_a_state_variant_with_its_own_undo_stem():
    """A variant keeps a SEPARATE undo stack — otherwise undoing a night fix could restore the day scene
    over the night art, which is unrecoverable without regenerating."""
    p, stem = _run_room_target_case(["scene.png", "scene_night.png"],
                                    lambda base: hs.room_target(base, "r1", "scene_night.png"))
    assert os.path.basename(p) == "scene_night.png", p
    assert stem == "scene_night", stem


def _refuses(files, bad):
    def fn(base):
        try:
            hs.room_target(base, "r1", bad)
        except ValueError:
            return True
        return False
    return _run_room_target_case(files, fn)


def test_room_target_refuses_to_escape_the_room_directory():
    """`file` comes off a query string: basename it, then re-check the resolved parent."""
    for bad in ("../../../etc/passwd", "/etc/hosts", "../scene.png"):
        assert _refuses(["scene.png"], bad), "accepted a traversal target: %r" % bad


def test_room_target_refuses_undo_snapshots_and_working_files():
    """Seam-fixing an undo snapshot corrupts the stack; seam-fixing *_seam.png races the running job."""
    for bad in ("scene_undo0.png", "scene_seam.png"):
        assert _refuses(["scene.png", "scene_undo0.png", "scene_seam.png"], bad), \
            "accepted a protected target: %r" % bad


def test_room_target_rejects_a_missing_file_rather_than_inventing_one():
    assert _refuses(["scene.png"], "scene_fog.png")


def test_room_target_rejects_a_non_png():
    assert _refuses(["scene.png"], "notes.txt")




def test_scene_spec_explicit_label_wins_over_desc_truncation():
    """A spec element may name its in-world `label`; to_hotspots uses it verbatim. That label is the play-time
    MODAL TITLE and the key `_attach_planned_content` slug-matches on, so a truncated art prompt (the fallback)
    would both read as chopped prose and make pre-art content attachment fragile. Elements with no explicit
    label keep the legacy desc[:60] fallback. Regression for the Egypt wiring pass (2026-08-07)."""
    import scene_spec as ss
    spec = {"room": "r", "elements": [
        {"id": "desk", "at": "dead ahead in the centre", "label": "The customs writing-desk",
         "desc": "the customs writing-desk on the open deck: crates of amphorae standing open in their straw",
         "puzzle": True},
        {"id": "plain", "at": "to the left",
         "desc": "a weathered field card pinned to the living-wood railing beside the bench", "clue": True},
    ]}
    hs = {h["id"]: h for h in ss.to_hotspots(spec)}
    assert hs["desk"]["label"] == "The customs writing-desk"          # explicit label used verbatim
    assert hs["desk"]["type"] == "puzzle"
    assert hs["plain"]["label"] == "a weathered field card pinned to the living-wood railing bes"   # desc[:60]
    assert len(hs["plain"]["label"]) == 60


def test_scene_spec_grid_role_emits_grid_type():
    """An escape gate may be a KEYPAD (`lock:true` -> type 'lock') or a MATRIX-SELECT (`grid:true` -> type
    'grid', mechanic #15). The engine dispatches on the hotspot type (`openGrid` vs `openLock`), so a
    grid-select escape emitted as a 'lock' silently fails to open — and pre-art content, which attaches by
    (type, slug(label)), would not match either. Regression for the Egypt escape (2026-08-07)."""
    import scene_spec as ss
    spec = {"room": "r", "elements": [
        {"id": "door", "at": "dead ahead in the centre", "label": "The bronze door",
         "desc": "a heavy bronze door with a three-by-three grid of empty sockets", "grid": True},
        {"id": "pad", "at": "to the left", "label": "The keypad",
         "desc": "a brass keypad beside the hatch", "lock": True},
    ]}
    hs = {h["id"]: h for h in ss.to_hotspots(spec)}
    assert hs["door"]["type"] == "grid" and hs["door"]["label"] == "The bronze door"
    assert hs["pad"]["type"] == "lock"


def test_scene_spec_dial_role_and_variant_jobs():
    """Two art-pipeline gaps the Egypt finale needed (2026-08-07):
    (1) `dial:true` emits type 'dial' — the engine's ONLY world-state control. `switch` has no engine
        handler at all, so a switch hotspot is inert until hand-reclassified (every trees drive-lever was).
    (2) `variants:[{state, when, reveal}]` on ANY element emits a state-tagged variant job, so alternate-look
        art (the Pharos beam swung onto the player's ship) is produced in the normal art batch instead of a
        forgettable hand-gen. It is the general case of the door-only `opensOnto` shorthand; a variant with
        no `reveal` is skipped, exactly as dooropen_jobs skips one."""
    import scene_spec as ss
    spec = {"room": "pharos", "elements": [
        {"id": "lamp", "at": "just right of centre", "label": "The lamp dial",
         "desc": "the great fire-lamp on its geared turning-dial", "dial": True},
        {"id": "lever", "at": "to the left", "label": "A lever",
         "desc": "a brass lever in its slot", "switch": True},
        {"id": "harbour", "at": "on the far right", "label": "The harbour far below",
         "desc": "the dark harbour far below", "animate": {"motion": "lamps glinting", "loop": "boomerang"},
         "variants": [
            {"state": "beam_on_ship", "when": {"eq": ["pharos_beam", "ship"]},
             "reveal": "the beam swung down onto one moored ship"},
            {"state": "no_art_yet"},          # no reveal -> skipped
         ]},
    ]}
    hs = {h["id"]: h for h in ss.to_hotspots(spec)}
    assert hs["lamp"]["type"] == "dial" and hs["lamp"]["label"] == "The lamp dial"
    assert hs["lever"]["type"] == "switch"           # unchanged, still the generic control
    assert hs["harbour"]["type"] == "ambient"        # animated decor carries the variant art, no player marker
    jobs = ss.variant_jobs(spec)
    assert len(jobs) == 1, jobs                       # the reveal-less variant is skipped
    assert jobs[0] == {"type": "variant", "hotspotId": "harbour", "state": "beam_on_ship",
                       "prompt": "the beam swung down onto one moored ship",
                       "when": {"eq": ["pharos_beam", "ship"]}}
    assert ss.variant_jobs({"elements": [{"id": "x", "desc": "d"}]}) == []   # no variants -> no jobs


def test_apply_balance_covers_pre_art_planned_stings():
    """A `solveSfx` wired PRE-ART lives on `plannedHotspots` (content is authored there before any art and
    attaches to the placed box at commit). _apply_balance previously walked only committed `hotspots`, so a
    pre-art sting was silently never measured — it would ship louder than the music until someone re-ran the
    balance after commit. Regression for the Egypt sound pass (2026-08-07)."""
    def body(tmp):
        d = _write_scenario("wrangling", "y", {
            "music": "audio/m.mp3", "musicVolume": 0.5,
            "rooms": [{"key": "pharos", "built": False,
                       "plannedHotspots": [
                           {"type": "grid", "label": "The bronze door", "solveSfx": "audio/loudsting.mp3"},
                           {"type": "dial", "label": "The lamp dial",
                            "solveSfx": {"src": "audio/quietsting.mp3", "volume": 0.2}},
                       ]}],
        })
        # music −14 @ 0.5 → played −20.0. loudsting −6 plays OVER it; quietsting −40 sits well under.
        loud = {"audio/m.mp3": -14.0, "audio/loudsting.mp3": -6.0, "audio/quietsting.mp3": -40.0}
        orig = hs._audio_loudness
        hs._audio_loudness = _stub_loudness(loud)
        try:
            out = hs._apply_balance(d, apply=True)
        finally:
            hs._audio_loudness = orig
        assert out["nChanged"] == 1 and "error" not in out
        planned = json.load(open(os.path.join(d, "scenario.json")))["rooms"][0]["plannedHotspots"]
        sting = planned[0]["solveSfx"]                       # bare string promoted to {src, volume}
        assert sting["src"] == "audio/loudsting.mp3" and abs(sting["volume"] - 0.199) < 0.002
        assert planned[1]["solveSfx"]["volume"] == 0.2       # already under the music → untouched
    _with_rooms_root(body)


# --- seam repair menu: the retired options stay retired -------------------------------------------
# Lucas cut "crop & rescale" and "re-render whole scene" on 2026-08-07: crop paid ~2% of the scene to
# HIDE the seam rather than fix it, and the whole-frame re-render made an AI image of an AI image AND
# pushed a fresh seam to the far meridian — trading one seam for another. Both were removed from the
# UI *and* from the server dispatch, so a stale browser tab (or a hand-rolled POST) can't reach them
# either. The failure this guards: someone re-adds "crop"/"full" to a dispatch set and the two options
# quietly come back to life with no UI card explaining them.
def test_retired_seam_modes_are_not_dispatchable():
    assert "crop" not in hs._SEAM_LOCAL_OPS, "crop & rescale was retired — do not re-add"
    assert "full" not in hs._SEAM_AI_MODES, "whole-scene re-render was retired — do not re-add"
    assert hs._SEAM_LOCAL_OPS == {"gradient", "roll"}
    assert hs._SEAM_AI_MODES == {"patch", "occluder"}
    # _seam_local must not silently accept a retired op either (seam_ops still HAS crop as a library fn).
    for retired in ("crop", "full"):
        assert retired not in hs._SEAM_LOCAL_OPS and retired not in hs._SEAM_AI_MODES


# --- test-play mixer: "needs replacement" sound flags ----------------------------------------------
# 2026-08-07 (Lucas): balancing a sound and JUDGING it are different jobs — some clips are simply wrong
# for the room at any volume. The mixer's ⚑ marks a file for re-sourcing; it persists as
# `needsReplacement` on the sound entry and rides the same Save as the volumes. Flags key on `src`, so a
# file used in several rooms is flagged in all of them (a bad recording is bad everywhere). The failure
# this guards: a flag that doesn't survive a reload, or an unflag that never clears.
def test_audio_flags_round_trip_across_layers_and_stings():
    def body(_tmp):
        d = _write_scenario("data_vis", "flags", {"rooms": [
            {"key": "r1", "built": True,
             "sfx": [{"src": "audio/bed.mp3", "volume": 0.4}, {"src": "audio/gull.mp3", "volume": 0.3}],
             "hotspots": [{"id": "h1", "type": "puzzle", "solveSfx": "audio/sting.mp3"}]},
            {"key": "r2", "built": True, "sfx": [{"src": "audio/bed.mp3", "volume": 0.5}]},
        ]})
        assert hs._audio_flags(d) == {}, "nothing flagged to begin with"

        # flag a shared bed + a bare-string sting -> the sting is promoted to {src,...} to hold the flag
        n = hs._apply_audio_flags(d, {"audio/bed.mp3": True, "audio/sting.mp3": True})
        assert n == 3, f"two bed entries + one sting = 3 touched, got {n}"
        assert hs._audio_flags(d) == {"audio/bed.mp3": True, "audio/sting.mp3": True}
        doc = json.load(open(os.path.join(d, "scenario.json")))
        sting = doc["rooms"][0]["hotspots"][0]["solveSfx"]
        assert sting["src"] == "audio/sting.mp3" and sting["needsReplacement"] is True
        assert doc["rooms"][1]["sfx"][0]["needsReplacement"] is True, "flagged in EVERY room that uses it"
        assert "needsReplacement" not in doc["rooms"][0]["sfx"][1], "an unflagged sibling is untouched"

        # …and unflagging clears it everywhere, leaving no stray key behind
        n = hs._apply_audio_flags(d, {"audio/bed.mp3": False})
        assert n == 2 and hs._audio_flags(d) == {"audio/sting.mp3": True}
        doc = json.load(open(os.path.join(d, "scenario.json")))
        assert "needsReplacement" not in doc["rooms"][1]["sfx"][0]
        assert doc["rooms"][1]["sfx"][0]["volume"] == 0.5, "clearing a flag must not disturb the volume"
    _with_rooms_root(body)


# --- planned content must attach when the BOXES are placed, not only at commit ----------------------
# 2026-08-07: every hotspot in Egypt came back EMPTY after "Place all hotspots". `_attach_planned_content`
# only ran at commit, but the real workflow commits the art FIRST and places boxes later — so at commit
# there were no boxes to attach to, and at place-time nothing re-ran the attach. All 22 authored puzzles
# and clues sat unused on plannedHotspots while the placed boxes rendered blank.
def test_attach_planned_content_fills_placed_boxes():
    placed = [{"id": "obj_1", "type": "clue", "label": "The count-board", "box": [0, 0, 1, 1]},
              {"id": "obj_2", "type": "puzzle", "label": "The desk", "box": [0, 0, 1, 1]},
              {"id": "obj_3", "type": "door", "label": "The hatch", "to": "hold", "direction": "open"}]
    planned = [{"type": "clue", "label": "The count-board", "body": "three notches"},
               {"type": "puzzle", "label": "The desk", "question": "which type?", "answer": 1}]
    out = hs._attach_planned_content(json.loads(json.dumps(placed)), planned)
    assert out[0]["body"] == "three notches"
    assert out[1]["question"] == "which type?" and out[1]["answer"] == 1
    assert out[0]["box"] == [0, 0, 1, 1] and out[0]["id"] == "obj_1", "placement is preserved"
    assert out[2]["to"] == "hold", "a hotspot with no planned twin is left alone"


# --- a DIAL's one-shot `sfx` is an authored sound like any other -----------------------------------
# 2026-08-07: the Pharos lamp-dial lever throw and the deck cast-off live on `sfx`, not `solveSfx`, so
# they fell outside solveSounds() (no mixer row → unbalanceable, unflaggable) AND outside _apply_balance.
# A sound the author can neither hear-test, level, nor flag is effectively unmaintainable. Room-level
# `sfx` is the ambience LIST and must stay out of the one-shot path — only a HOTSPOT's `sfx` is a sting.
def test_dial_one_shot_sfx_is_flaggable_and_balanceable():
    def body(_tmp):
        d = _write_scenario("data_vis", "dialsfx", {"rooms": [
            {"key": "r1", "built": True,
             "sfx": [{"src": "audio/bed.mp3", "volume": 0.4}],          # ambience list — NOT a one-shot
             "hotspots": [{"id": "d1", "type": "dial", "label": "The lever",
                           "sfx": {"src": "audio/lever.mp3", "volume": 0.8}},
                          {"id": "d2", "type": "dial", "label": "Bare", "sfx": "audio/bare.mp3"}]}]})
        srcs = {src for _rk, _k, src, _s, _g in hs._iter_sound_slots(json.load(open(os.path.join(d, "scenario.json"))))}
        assert "audio/lever.mp3" in srcs and "audio/bare.mp3" in srcs, srcs
        assert "audio/bed.mp3" in srcs, "the room's ambience layer is still reachable"

        assert hs._apply_audio_flags(d, {"audio/lever.mp3": True, "audio/bare.mp3": True}) == 2
        assert hs._audio_flags(d) == {"audio/lever.mp3": True, "audio/bare.mp3": True}
        doc = json.load(open(os.path.join(d, "scenario.json")))
        hots = doc["rooms"][0]["hotspots"]
        assert hots[0]["sfx"]["volume"] == 0.8, "flagging must not disturb the volume"
        assert hots[1]["sfx"] == {"src": "audio/bare.mp3", "needsReplacement": True}, "bare string promoted"
        assert isinstance(doc["rooms"][0]["sfx"], list), "the ambience list must not be rewritten as a one-shot"
    _with_rooms_root(body)

def test_pano_uncommitted_compares_bytes_not_names():
    """Pending art is decided by BYTES, never by `builtFrom`.

    Single-candidate generation always writes `l1_<room>_1.png`, so a regeneration overwrites the very
    file the room was built from. A name-based test would then call the new art "already committed" and
    hide it — which is the one image that needs looking at. Three of canyon's nine rooms were in exactly
    that state on 2026-08-31, which is why this is a test and not a comment."""
    with tempfile.TemporaryDirectory() as base:
        scratch = os.path.join(base, "_scratch")
        os.makedirs(scratch)
        os.makedirs(os.path.join(base, "r1"))
        scene = os.path.join(base, "r1", "scene.png")
        open(scene, "wb").write(b"committed-art-bytes")

        same = os.path.join(scratch, "l1_r1_1.png")      # byte-identical to scene.png
        open(same, "wb").write(b"committed-art-bytes")
        diff = os.path.join(scratch, "l1_r1_2.png")      # same LENGTH, different bytes — size alone can't tell
        open(diff, "wb").write(b"regenerated-art!!!!")
        assert os.path.getsize(same) == os.path.getsize(diff) == os.path.getsize(scene)

        cands = ["l1_r1_1.png", "l1_r1_2.png"]
        assert hs._pano_uncommitted(base, "r1", cands) == ["l1_r1_2.png"]

        # the regen case: the built-from filename now holds different art -> it IS pending
        open(same, "wb").write(b"regenerated-art-NEW")
        assert hs._pano_uncommitted(base, "r1", cands) == cands

        # no committed art at all -> everything is pending
        os.remove(scene)
        assert hs._pano_uncommitted(base, "r1", cands) == cands

        # a candidate that vanished mid-listing is skipped, not raised
        assert hs._pano_uncommitted(base, "r1", ["gone.png"]) == ["gone.png"]




def test_room_clips_ignores_intermediates():
    """`cine_<state>.mp4` is a state; its `_raw`/`_src` siblings are not.

    Both live beside the clip under the same `cine_` prefix — the pre-bake render and the un-patched
    render — and both are gitignored working files the player never fetches. Globbing `cine_*.mp4`
    picked them up as world states called "base_raw" and "base_src", which showed every baked room
    twice and then three times in the gallery. Caught by eye both times (2026-08-31); this is the
    check that means there is no third time."""
    with tempfile.TemporaryDirectory() as base:
        d = os.path.join(base, "r1")
        os.makedirs(d)
        for name in ("cine_base.mp4", "cine_base_raw.mp4", "cine_base_src.mp4", "cine_night.mp4"):
            open(os.path.join(d, name), "wb").write(b"\0")
        states = [c["state"] for c in hs._room_clips(base, "r1")]
        assert states == ["base", "night"], states
        # base first, then variants — the order a gallery reads down the page
        assert hs._room_clips(base, "r1")[0]["file"] == "r1/cine_base.mp4"


def test_room_clips_carries_the_committed_mask():
    """The gallery's sliders open on the COMMITTED choice, so the clip payload must carry it.

    They previously always opened at "no mask · all video", which is a lie about any clip baked with a
    mask — and every one of them was, since the composite went into the bake. A reviewer then read the
    off position as the shipped state and re-litigated a decision that had already been made."""
    with tempfile.TemporaryDirectory() as base:
        d = os.path.join(base, "r1")
        os.makedirs(d)
        open(os.path.join(d, "cine_base.mp4"), "wb").write(b"\0")
        open(os.path.join(d, "cine_night.mp4"), "wb").write(b"\0")
        json.dump({"pct": 88.0, "region": 250.0, "enabled": True},
                  open(os.path.join(d, "cine_base.mask.json"), "w"))
        clips = {c["state"]: c for c in hs._room_clips(base, "r1")}
        assert clips["base"]["mask"]["pct"] == 88.0
        assert clips["base"]["mask"]["region"] == 250.0
        assert clips["night"]["mask"] == {}          # no sidecar -> no claim, not a fabricated default


def test_state_still_is_the_state_s_own_art():
    """A variant clip sits over the VARIANT's panorama, never over the room's `scene.png`.

    `scene.png` was hardcoded on both the bake side and the gallery side, so a night clip was
    composited onto — and reviewed against — the DAY panorama: every pixel the mask held still showed
    the wrong world state. Same rule that stopped a daytime panorama shipping as the "night deck"
    (2026-08-29): resolve through `scene_states`, never guess from the room node."""
    doc = {"rooms": [{"key": "r1", "panorama": "r1/scene.png", "built": True,
                      "hotspots": [{"id": "h", "box": [0, 0, 1, 1],
                                    "variants": [{"state": "night", "panorama": "r1/scene_night.png"}]}]}]}
    with tempfile.TemporaryDirectory() as base:
        os.makedirs(os.path.join(base, "r1"))
        for f in ("scene.png", "scene_night.png"):
            open(os.path.join(base, "r1", f), "wb").write(b"\0")
        assert hs._state_still_rel(base, "r1", "base", doc) == "r1/scene.png"
        assert hs._state_still_rel(base, "r1", "night", doc) == "r1/scene_night.png"
        # an unknown state falls back to the base still rather than raising or serving nothing —
        # the scene-spec pipeline files per-object clips (cine_lantern.mp4) that are not world states
        assert hs._state_still_rel(base, "r1", "lantern", doc) == "r1/scene.png"


def test_mask_grid_shape_and_monotonicity():
    """The (threshold x region) surface behind the gallery's plane.

    Two properties it must have, because the pad is unreadable if either fails: coverage falls as the
    THRESHOLD rises (fewer pixels clear the bar) and falls as the REGION CUT rises (whole components go).
    Neither may ever increase — a surface that dips and rises reads as noise, and the reviewer would be
    navigating a picture of a bug."""
    import numpy as np
    rng = np.random.default_rng(0)
    t = (rng.random((256, 512)) * 2).astype(np.float32)
    t[80:160, 150:330] += 18                      # one large coherent mover
    for _ in range(400):                          # and a scatter of one-off hot pixels
        y, x = int(rng.integers(3, 250)), int(rng.integers(3, 500))
        t[y:y + 2, x:x + 2] += 22
    g = hs._mask_grid(t, scale=2)
    assert len(g["cov"]) == len(g["regionPos"])
    assert all(len(row) == len(g["pcts"]) for row in g["cov"])
    assert g["regionPpm"][0] == 0.0                                  # row 0 is "no cut"
    for row in g["cov"]:                                             # along the threshold axis
        assert row == sorted(row, reverse=True), row
    for j in range(len(g["pcts"])):                                  # and along the region axis
        col = [row[j] for row in g["cov"]]
        assert col == sorted(col, reverse=True), col
    # and the cut must actually do something somewhere, or the axis is decorative
    assert g["cov"][0][len(g["pcts"]) // 2] > g["cov"][-1][len(g["pcts"]) // 2]


def test_grid_ppm_matches_the_ui_mapping():
    """`_grid_ppm` and the UI's `regPpm` are the same curve. If they drift, the pad's axes label
    positions the sliders do not actually reach, and every point read off it is off by a step."""
    assert hs._grid_ppm(0) == 0.0
    for pos, want in ((25, 10.0), (50, 100.0), (75, 1000.0), (100, 10000.0)):
        assert abs(hs._grid_ppm(pos) - want) < 1e-6, (pos, hs._grid_ppm(pos))


# ---- serving a room's BAKED clips in play --------------------------------------------------------
# FAILURE MODE UNDER TEST — a clip that is baked, reviewed, and never played. `_room_clips` is
# filesystem-derived by design ("not wired into scenario.json until someone has looked at it"), but
# nothing implemented the step after the look: canyon carried nine baked full-scene clips that no hotspot
# referenced, so test play served the stills and nothing said why (2026-09-01).


def _clipdir(base, room, names):
    os.makedirs(os.path.join(base, room), exist_ok=True)
    for n in names:
        open(os.path.join(base, room, n), "wb").write(b"x")


def test_serve_clips_wires_carriers_and_leaves_base_stateless():
    """The base clip must carry NO `state` key. `pickCinemagraphs` matches the base backdrop as state
    ABSENT, so writing `state: "base"` matches nothing and silently plays the still — the exact bug this
    whole path exists to end, reintroduced one field deeper."""
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": [{"key": "r1", "hotspots": [
            {"id": "table", "type": "puzzle", "label": "Table", "box": [0.1, 0.1, 0.2, 0.2]}]}]})
        _clipdir(d, "r1", ["cine_base.mp4", "cine_night.mp4",
                           "cine_base_raw.mp4", "cine_base_src.mp4"])   # intermediates must be ignored
        wired, unchanged = hs._serve_room_clips("r1", d)
        assert wired == ["base", "night"] and unchanged == [], (wired, unchanged)
        hsl = json.load(open(os.path.join(d, "scenario.json")))["rooms"][0]["hotspots"]
        by = {h["id"]: h for h in hsl}
        assert by["clip_base"]["cinemagraph"] == {"box": [0, 0, 1, 1], "video": "r1/cine_base.mp4"}
        assert by["clip_night"]["cinemagraph"] == {"box": [0, 0, 1, 1], "video": "r1/cine_night.mp4",
                                                   "state": "night"}
        # carriers are marker-less and click-through, and the room's real hotspot is untouched
        assert by["clip_base"]["type"] == "ambient" and by["clip_base"]["box"] == [0, 0, 1, 1]
        assert "cinemagraph" not in by["table"]
    _with_rooms_root(body)


def test_serve_clips_is_idempotent_and_refreshes_a_rebake():
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": [{"key": "r1", "hotspots": []}]})
        _clipdir(d, "r1", ["cine_base.mp4"])
        hs._serve_room_clips("r1", d)
        path = os.path.join(d, "scenario.json")
        snap = open(path, "rb").read()
        assert hs._serve_room_clips("r1", d) == ([], ["base"])
        assert open(path, "rb").read() == snap            # no write, no duplicate carrier
        # a re-bake that renamed the file must be picked back up, not left pointing at the old one
        doc = json.load(open(path))
        doc["rooms"][0]["hotspots"][0]["cinemagraph"]["video"] = "r1/cine_stale.mp4"
        json.dump(doc, open(path, "w"))
        wired, _ = hs._serve_room_clips("r1", d)
        assert wired == ["base"], wired
        carriers = [h for h in json.load(open(path))["rooms"][0]["hotspots"]
                    if h["id"].startswith("clip_")]
        assert len(carriers) == 1, carriers
    _with_rooms_root(body)


def test_room_clips_served_flag_needs_no_doc_from_the_caller():
    """`served` was read off `doc or {}`, so calling _room_clips WITHOUT a doc reported every clip as
    unserved — a silent wrong answer from the very field added to make unserved clips visible."""
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": [{"key": "r1", "hotspots": []}]})
        _clipdir(d, "r1", ["cine_base.mp4"])
        assert [c["served"] for c in hs._room_clips(d, "r1")] == [False]
        hs._serve_room_clips("r1", d)
        assert [c["served"] for c in hs._room_clips(d, "r1")] == [True]          # no doc passed
        doc = json.load(open(os.path.join(d, "scenario.json")))
        assert [c["served"] for c in hs._room_clips(d, "r1", doc)] == [True]     # doc passed
        doc["rooms"][0]["hotspots"][0]["cinemagraph"]["video"] = "r1/cine_gone.mp4"
        assert [c["served"] for c in hs._room_clips(d, "r1", doc)] == [False]    # stale reference
    _with_rooms_root(body)


def test_serve_clips_rejects_a_room_with_no_clips():
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": [{"key": "r1", "hotspots": []}]})
        for bad in ("r1", "nope"):
            try:
                hs._serve_room_clips(bad, d)
                raise AssertionError("should reject %r" % bad)
            except ValueError:
                pass
    _with_rooms_root(body)


# ---- promoting plannedHotspots into the live array (gallery tab 4) -------------------------------
# FAILURE MODE UNDER TEST — a scenario whose hotspots are authored but never promoted reads as EMPTY.
# canyon carried 34 authored, boxed hotspots on `plannedHotspots` and nothing in `hotspots`; every
# harness view reads the latter, so nine built rooms showed zero hotspots and the work looked lost
# (2026-09-01). `_commit_planned_hotspots` is the promotion, and the thing it must never do is reach for
# `scene_spec.approx_boxes` the way "Place all hotspots" does — 16 of canyon's 34 boxes were hand-
# corrected, and a rough re-guess would have silently thrown that placement away.


def _canyonish():
    """A room mid-pipeline: content + a reviewed box on plannedHotspots, nothing committed yet."""
    return {"rooms": [{"key": "r1", "hotspots": [], "plannedHotspots": [
        {"type": "clue", "label": "The engraved panel", "box": [0.4, 0.3, 0.6, 0.6],
         "boxSource": "review:agent", "body": "<p>the calibration matrix</p>", "note": "design only"},
        {"type": "puzzle", "label": "The high weir", "box": [0.1, 0.2, 0.2, 0.4],
         "question": "which?", "starterCode": "data", "id": "weir"},
        {"type": "ambient", "label": "No box here yet"},
    ]}]}


def test_commit_planned_keeps_the_planned_box_and_attaches_content():
    def body(tmp):
        d = _write_scenario("hierarchical_clustering", "canyon", _canyonish())
        created, already, boxless = hs._commit_planned_hotspots("r1", d)
        assert created == ["The engraved panel", "The high weir"], created
        assert already == [] and boxless == ["No box here yet"], (already, boxless)
        placed = json.load(open(os.path.join(d, "scenario.json")))["rooms"][0]["hotspots"]
        by = {h["label"]: h for h in placed}
        # THE box, not a re-guess.
        assert by["The engraved panel"]["box"] == [0.4, 0.3, 0.6, 0.6]
        assert by["The high weir"]["box"] == [0.1, 0.2, 0.2, 0.4]
        # authored content came across; `note` is design-only and must not (see _PLANNED_SKIP)
        assert by["The engraved panel"]["body"] == "<p>the calibration matrix</p>"
        assert "note" not in by["The engraved panel"]
        assert by["The high weir"]["question"] == "which?"
        # an entry with no box is reported and skipped, never invented one
        assert "No box here yet" not in by
        # ids: the planned id wins, else the label slug
        assert by["The high weir"]["id"] == "weir"
        assert by["The engraved panel"]["id"] == "the_engraved_panel"
    _with_rooms_root(body)


def test_commit_planned_is_idempotent_and_never_rewrites_a_live_box():
    """Re-committing must promote nothing and leave the file byte-identical — and a box already tuned in
    the flat editor must survive, because the committed array is the live truth, not the planned one."""
    def body(tmp):
        d = _write_scenario("hierarchical_clustering", "canyon", _canyonish())
        hs._commit_planned_hotspots("r1", d)
        path = os.path.join(d, "scenario.json")
        # simulate a later hand-tune of the committed box
        doc = json.load(open(path))
        doc["rooms"][0]["hotspots"][0]["box"] = [0.41, 0.31, 0.61, 0.61]
        json.dump(doc, open(path, "w"), indent=2, ensure_ascii=False)
        snap = open(path, "rb").read()
        created, already, _ = hs._commit_planned_hotspots("r1", d)
        assert created == [], created                     # nothing new to promote
        assert len(already) == 2, already
        assert open(path, "rb").read() == snap            # and the tuned box was NOT reverted
    _with_rooms_root(body)


def test_commit_planned_keeps_hotspot_ids_unique():
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": [{"key": "r1",
            "hotspots": [{"id": "the_lever", "type": "door", "label": "Other thing",
                          "box": [0, 0, 0.1, 0.1]}],
            "plannedHotspots": [{"type": "puzzle", "label": "The lever", "box": [0.5, 0.5, 0.6, 0.6]}]}]})
        hs._commit_planned_hotspots("r1", d)
        placed = json.load(open(os.path.join(d, "scenario.json")))["rooms"][0]["hotspots"]
        ids = [h["id"] for h in placed]
        assert len(ids) == len(set(ids)), ids             # slug collided with a live id -> suffixed
        assert "the_lever_2" in ids, ids
    _with_rooms_root(body)


def test_commit_planned_rejects_a_room_with_nothing_planned():
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": [{"key": "r1", "hotspots": []}]})
        for bad in ("r1", "nope"):
            try:
                hs._commit_planned_hotspots(bad, d)
                raise AssertionError("should reject %r" % bad)
            except ValueError:
                pass
    _with_rooms_root(body)


# ---- which _scratch candidates are NOT the committed art -----------------------------------------
# FAILURE MODE UNDER TEST — the committed image shown TWICE: once at the top of its card as the
# committed one, and again in the row below as something still to choose. Every commit here is a COPY
# to a stable name (scene.png / cover.png / _world/plate.png) that records no back-pointer, and the
# generators reuse candidate filenames, so only the BYTES can answer "is this one already committed".


def test_scratch_uncommitted_matches_on_bytes_not_names():
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": []})
        scratch = os.path.join(d, "_scratch"); os.makedirs(scratch)
        open(os.path.join(scratch, "a.png"), "wb").write(b"AAAA")
        open(os.path.join(scratch, "b.png"), "wb").write(b"BBBB")
        open(os.path.join(scratch, "c.png"), "wb").write(b"AAAAA")     # same prefix, different length
        committed = os.path.join(d, "cover.png")
        open(committed, "wb").write(b"AAAA")
        assert hs._scratch_uncommitted(d, ["a.png", "b.png", "c.png"], committed) == ["b.png", "c.png"]
        # nothing committed yet -> every candidate is pending
        assert hs._scratch_uncommitted(d, ["a.png"], os.path.join(d, "gone.png")) == ["a.png"]
        assert hs._scratch_uncommitted(d, ["a.png"], None) == ["a.png"]
        # a candidate that vanished mid-listing is skipped, not raised
        assert hs._scratch_uncommitted(d, ["a.png", "ghost.png"], committed) == []
    _with_rooms_root(body)


def test_cover_candidates_excludes_derived_files():
    """`_open`/`_x2` are an upscale and a variant, not fresh candidates — offering them means committing
    a derived file as if it were an original."""
    def body(tmp):
        d = _write_scenario("c", "s", {"rooms": []})
        scratch = os.path.join(d, "_scratch"); os.makedirs(scratch)
        for n in ("gpt_cover_1.png", "gpt_cover_2.png", "gpt_cover_2_x2.png",
                  "gpt_cover_3_open.png", "l1_room_1.png"):
            open(os.path.join(scratch, n), "wb").write(b"x")
        assert sorted(hs._cover_candidates(d)) == ["gpt_cover_1.png", "gpt_cover_2.png"]
    _with_rooms_root(body)


def test_cinemagraph_queue_keys_on_room_and_hotspot():
    """A hotspot id is unique only WITHIN a room, but the cinemagraph queue spans the whole scenario.
    Keyed on the id alone, the first room to queue `valley_view` made every OTHER room's `valley_view`
    look already-queued and it was dropped in SILENCE — beacons declared 20 cinemagraphs across 12 rooms
    and exactly 8 reached the queue, one per distinct id (2026-09-02). Exercises the real _apply_spec."""
    def body(tmp):
        base = os.path.join(hs.ROOMS_ROOT, "ch", "sc")
        spec = lambda rk: {"room": rk, "interior": False, "seam": "open sky",
                           "elements": [{"id": "valley_view", "at": "dead ahead in the centre",
                                         "desc": "the valley below",
                                         "animate": {"motion": "the channels sliding", "loop": "crossfade"}}]}
        doc = {"id": 99, "rooms": [{"key": rk, "built": True, "hotspots": [],
                                    "authoring": {"sceneSpec": spec(rk)}} for rk in ("alpha", "beta")]}
        for rk in ("alpha", "beta"):
            os.makedirs(os.path.join(base, rk), exist_ok=True)
        os.makedirs(os.path.join(base, "_scratch"), exist_ok=True)
        with open(os.path.join(base, "scenario.json"), "w", encoding="utf-8") as f:
            json.dump(doc, f)
        for rk in ("alpha", "beta"):
            hs._apply_spec(base, rk)
        # BOX CINEMAGRAPHS RETIRED 2026-09-02: an `animate` element now yields NO hotspot and NO queued
        # job — motion is baked whole-scene from `motionSpec`. Both halves are asserted here because the
        # (room, hotspot) queue key this test was written for is still the rule for VARIANT jobs, and a
        # future re-introduction of per-object jobs must not silently reinstate the id-only collision.
        q = hs._batch_read_queue(base)
        assert [j for j in q if j["type"] == "cinemagraph"] == [], q
        node = next(r for r in json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))["rooms"]
                    if r["key"] == "alpha")
        assert [h for h in node["hotspots"] if h.get("type") == "ambient"] == [], node["hotspots"]
        vkeys = {(j.get("roomKey"), j.get("hotspotId"), j.get("state"))
                 for j in [{"type": "variant", "roomKey": "alpha", "hotspotId": "d", "state": "open"}]
                 if j.get("type") == "variant"}
        assert ("beta", "d", "open") not in vkeys, "variant dedupe must stay keyed on the room too"
    _with_rooms_root(body)

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"all tests passed ({len(tests)})")


# ---------------------------------------------------------------------------------------------
# PRE-ART GATE (2026-09-03). The art phase used to sit between two skills gated by nothing, which
# is how twelve unchecked seams shipped, and how heist nearly generated a blown vault door for a
# crew whose entire signature is that they were let in. `preflight.py` stamps a HASH of
# scenario.json + datasets, so passing once is not enough — editing either re-arms the gate.
def test_preflight_stamp_goes_stale_when_the_scenario_changes(tmp_path):
    import json as _json, sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import preflight

    base = tmp_path / "sc"; (base / "data").mkdir(parents=True)
    (base / "scenario.json").write_text(_json.dumps({"rooms": [{"key": "a", "built": False}]}))
    (base / "data" / "d.csv").write_text("job\nx\n")

    ok, why = preflight.stamp_is_fresh(str(base))
    assert not ok and "no preflight stamp" in why, "an ungated scenario must be blocked"

    (base / ".preflight_ok").write_text(_json.dumps({"hash": preflight._hash(str(base))}))
    assert preflight.stamp_is_fresh(str(base))[0], "a fresh stamp must unlock"

    (base / "scenario.json").write_text(_json.dumps({"rooms": [{"key": "a", "built": False}], "x": 1}))
    ok, why = preflight.stamp_is_fresh(str(base))
    assert not ok and "STALE" in why, "editing scenario.json must re-arm the gate"


def test_preflight_grandfathers_a_scenario_that_already_has_art(tmp_path):
    """Locking every existing scenario out of a re-generation would be a nasty surprise, and is not
    the failure mode the gate protects. A scenario past its first generation is never blocked."""
    import json as _json, sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import preflight
    base = tmp_path / "built"; base.mkdir()
    (base / "scenario.json").write_text(_json.dumps({"rooms": [{"key": "a", "built": True}]}))
    ok, why = preflight.stamp_is_fresh(str(base))
    assert ok and "grandfathered" in why, "a scenario with committed art must not be blocked"
