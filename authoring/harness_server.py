#!/usr/bin/env python3
"""
harness_server.py — in-repo authoring server for the gpt-image-2 escape-room scenes.

Replaces the retired DiT360 harness (was ~/dit360_bench/harness_server.py). We
committed to the gpt-image-2 pseudo-360 wrap (2026-07-15), so this server carries
NONE of the old GPU machinery: no run.sh, no GPU eviction, no conda-for-generation.
gpt-image-2 is a cloud API and Real-ESRGAN is light — the server just shells out to
the authoring scripts and reports progress.

Serves the authoring UI (authoring/ui/) on :8751 and adds (scene/* requests are
mapped to the active scenario's _scratch pool by the /scene/ route):
  GET  /api/status[?slot=N]        -> job state for one slot, or all slots if omitted
  GET  /api/scenes                 -> list of scene/*.png (base candidates)
  POST /api/generate {prompt,n,quality,size,slot,tag}
                                   -> gpt-image-2 -> scene/gpt_<tag>_NNN.png (N candidates;
                                      size e.g. 1536x576 for a native wide panorama).
                                      Four columns author a whole room series in one go:
                                      each column is a `slot` with its own `tag`, and slots
                                      run concurrently (distinct tag = distinct filename
                                      prefix, so parallel jobs never collide on the index).
  POST /api/save-wrap {image,haov,vaov,hfov,vOffset,pitch}
                                   -> writes scene/wrap.json (frozen viewer defaults)
  POST /api/save-hotspots {image,haov,vaov,vOffset,hotspots:[...]}
                                   -> writes scene/hotspots.json (viewer reads it)
  POST /api/dooropen {image,box,prompt}
                                   -> masked gpt-image-2 edit of the box region ->
                                      scene/<image>_open.png (door-swap target)
  POST /api/commit-room {image,roomDir}
                                   -> copy the chosen base + its _open partner into
                                      <escape_rooms>/<roomDir>/ under STABLE names
                                      (scene.png / scene_open.png), + that image's wrap
                                      + hotspots re-keyed. Keeps the door pair together
                                      and makes a self-contained, playable room dir.
  GET  /api/audio-candidates       -> list candidate sfx loops in <scenario>/_scratch/audio/
                                      (the audition pool for step 6 "Sounds").
  POST /api/commit-sound {file}    -> materialise a chosen _scratch/audio/ candidate into the committed
                                      <scenario>/audio/ (same name) and return its src; the client
                                      appends it as an sfx LAYER and saves the array via /api/room-patch
                                      (a room can hold several layered loop/interval sounds).

Keys come from the environment (OPENAI_API_KEY for gpt, AAPI for Claude); launch
through a login shell so ~/.bashrc is sourced:
  bash -lic 'python3 <this>/harness_server.py'
"""
import os
import re
import copy
import json
import glob
import shutil
import threading
import subprocess
import http.server
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ESCAPE_ROOT = os.path.abspath(os.path.join(HERE, ".."))  # escape_rooms/ (commit targets live under here)
ROOT = os.path.join(HERE, "ui")  # served web root: the authoring pages (harness_gpt/view360/reproject_test)
ROOMS_ROOT = os.path.join(ESCAPE_ROOT, "rooms")          # rooms/<chapter>/<scenario>/
GEN = os.path.join(HERE, "generate_scene.py")
PORT = 8751

# Active scenario (Phase 3): which rooms/<chapter>/<scenario>/ the harness authors into.
# SCENE (the candidate `_scratch` pool the pages read/write via the /scene/ route) and
# COMMIT_BASE (the "Send to room" target root) both DERIVE from it. Changed at runtime via
# POST /api/select-scenario; defaults to the data_vis/alaska scenario.
ACTIVE = {"chapter": "data_vis", "scenario": "alaska"}
SCENE = None        # rooms/<ch>/<sc>/_scratch — set by _apply_active()
COMMIT_BASE = None  # rooms/<ch>/<sc>       — set by _apply_active()


def _scenario_dir(chapter, scenario):
    """Absolute rooms/<chapter>/<scenario> dir, confined to the rooms/ tree."""
    d = os.path.abspath(os.path.join(ROOMS_ROOT, chapter, scenario))
    if d != ROOMS_ROOT and not d.startswith(os.path.abspath(ROOMS_ROOT) + os.sep):
        raise ValueError("scenario path escapes rooms/")
    return d


def _apply_active():
    """Recompute SCENE + COMMIT_BASE from ACTIVE and ensure the scratch dir exists."""
    global SCENE, COMMIT_BASE
    COMMIT_BASE = _scenario_dir(ACTIVE["chapter"], ACTIVE["scenario"])
    SCENE = os.path.join(COMMIT_BASE, "_scratch")
    os.makedirs(SCENE, exist_ok=True)


def _list_scenarios():
    """Every rooms/<chapter>/<scenario>/scenario.json on disk, with its title."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOMS_ROOT, "*", "*", "scenario.json"))):
        parts = os.path.relpath(p, ROOMS_ROOT).split(os.sep)
        if len(parts) != 3:
            continue
        title = ""
        try:
            title = json.load(open(p)).get("title", "")
        except Exception:
            pass
        out.append({"chapter": parts[0], "scenario": parts[1], "title": title})
    return out


def _scenario_config():
    """Per-room authoring seed (key/tag/scenePrompt/doorPrompt) derived from scenario.json's
    `rooms[]` nodes (Phase 7 — each room node carries its own `authoring`). The IDE UI reads the
    full doc via /api/scenario; this stays for any lightweight column-seed use."""
    series = []
    try:
        for r in _load_scenario().get("rooms", []):
            a = r.get("authoring") or {}
            series.append({"key": r.get("key"), "tag": a.get("tag") or r.get("key"),
                           "scenePrompt": a.get("scenePrompt", ""), "doorPrompt": a.get("doorPrompt", "")})
    except Exception:
        pass
    return {"chapter": ACTIVE["chapter"], "scenario": ACTIVE["scenario"], "series": series}


def _select_scenario(chapter, scenario):
    """Point the harness at rooms/<chapter>/<scenario>/ (must have a scenario.json)."""
    d = _scenario_dir(chapter, scenario)
    if not os.path.isfile(os.path.join(d, "scenario.json")):
        raise ValueError("no scenario.json for %s/%s" % (chapter, scenario))
    ACTIVE["chapter"], ACTIVE["scenario"] = chapter, scenario
    _apply_active()


def _room_dir_for_key(room_key):
    """Map a bare room key (e.g. "room1") to an escape_rooms-relative dir under the active
    scenario: rooms/<ch>/<sc>/<key>. Sanitised to a single path segment (no traversal)."""
    key = re.sub(r"[^A-Za-z0-9_]", "", str(room_key or ""))
    if not key:
        raise ValueError("empty roomKey")
    return os.path.relpath(os.path.join(COMMIT_BASE, key), ESCAPE_ROOT)


# ---- scenario.json read/write (Phase 6: the scenario IDE's source of truth) ----
# scenario.json is now precious (the harness reads AND writes it), so every write makes a
# rolling `.bak` and is atomic. All edits are TARGETED shallow merges (patch just the fields
# an editor owns) so the harness, the wrap tab, and the hotspots tab don't clobber each other.

def _scenario_base(chapter, scenario):
    """Resolve an EXPLICIT scenario dir from chapter+scenario (both required, must have a
    scenario.json), else fall back to the active COMMIT_BASE when neither is given. Editors pass
    their own chapter+scenario so a save always targets the scenario they LOADED — never whatever
    is ACTIVE at save time (which silently corrupted a sibling scenario that shared room keys)."""
    ch = re.sub(r"[^A-Za-z0-9_]", "", str(chapter or ""))
    sc = re.sub(r"[^A-Za-z0-9_]", "", str(scenario or ""))
    if not ch and not sc:
        return COMMIT_BASE
    d = _scenario_dir(ch, sc)
    if not os.path.isfile(os.path.join(d, "scenario.json")):
        raise ValueError("no scenario.json for %s/%s" % (ch, sc))
    return d


# One writer at a time for scenario.json. Every patch is a load-modify-write, and patches run
# concurrently (ThreadingHTTPServer handler threads + the door-open background thread's
# panoramaOpen patch). Without this, two interleaved patches both load, then last-writer-wins —
# silently dropping the other's fields (e.g. a hotspots save racing the door job finishing).
SAVE_LOCK = threading.Lock()


def _scenario_path(base=None):
    return os.path.join(base or COMMIT_BASE, "scenario.json")


def _load_scenario(base=None):
    with open(_scenario_path(base), encoding="utf-8") as f:
        return json.load(f)


def _save_scenario(doc, base=None):
    p = _scenario_path(base)
    if os.path.exists(p):
        shutil.copyfile(p, p + ".bak")          # rolling single backup before every write
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)                            # atomic swap


def _room_patch(room_key, fields, base=None):
    """Shallow-merge `fields` into the rooms[] node whose key == room_key, in the scenario at
    `base` (default the active one). Only the provided keys change; everything else on the node
    (wrap/hotspots/…) is preserved."""
    if not isinstance(fields, dict):
        raise ValueError("fields must be an object")
    with SAVE_LOCK:
        doc = _load_scenario(base)
        rooms = doc.get("rooms")
        if not isinstance(rooms, list):
            raise ValueError("scenario has no rooms[]")
        target = next((r for r in rooms if r.get("key") == room_key), None)
        if target is None:
            raise ValueError("no room with key %r" % room_key)
        target.update(fields)
        _save_scenario(doc, base)
    return target


def _scenario_patch(fields, base=None):
    """Shallow-merge `fields` into the top level of the scenario at `base` (title, story, music, …)."""
    if not isinstance(fields, dict):
        raise ValueError("fields must be an object")
    with SAVE_LOCK:
        doc = _load_scenario(base)
        doc.update(fields)
        _save_scenario(doc, base)
    return {k: doc[k] for k in fields}


def _clamp01(v):
    return max(0.0, min(1.0, float(v)))


def _apply_mix(music_volume, room_vols, base=None):
    """Volume-ONLY writeback for the test-play sound mixer. `music_volume` (or None) sets the
    scenario-level `musicVolume`; `room_vols` is {roomKey: {src: volume}} setting each matching sfx
    layer's `volume` in place. Deliberately surgical — it reloads scenario.json FRESH and touches
    only the volume field of layers matched by src, so it can never clobber a layer the harness
    added/edited between test-play start and save (unlike sending a whole stale sfx array back).
    Every other field (mode/delay/duck/gap/crossfade) and every unmatched layer is preserved."""
    room_vols = room_vols or {}
    with SAVE_LOCK:
        doc = _load_scenario(base)
        touched_music = False
        if music_volume is not None:
            doc["musicVolume"] = _clamp01(music_volume)
            touched_music = True
        rooms = {r.get("key"): r for r in doc.get("rooms", []) if isinstance(r, dict)}
        n_layers = 0
        for key, vols in room_vols.items():
            room = rooms.get(key)
            if room is None or not isinstance(vols, dict):
                continue
            sfx = room.get("sfx")
            layers = sfx if isinstance(sfx, list) else ([sfx] if isinstance(sfx, dict) else [])
            for layer in layers:
                if isinstance(layer, dict) and layer.get("src") in vols:
                    layer["volume"] = _clamp01(vols[layer["src"]])
                    n_layers += 1
        if touched_music or n_layers:
            _save_scenario(doc, base)
    return {"music": touched_music, "layers": n_layers}


# ---- planned-content decoupling (author content BEFORE art) ----
# Puzzle/clue/lock CONTENT can be authored on a room's `plannedHotspots` entries before any scene
# exists (the editors write it there for an unbuilt room). Box PLACEMENT still happens on the
# generated art. At commit, `_attach_planned_content` copies each planned entry's authored content
# onto the matching placed box, so a box lands fully wired and no content-fill step waits on art.
# Match is on (type, slug(label)) — the SAME slug rule the hotspots editor uses to tick a planned
# item off (`planPlaced` in hotspots_edit.html). Keep the two in lockstep if either changes.

# fields that describe the box/design manifest, never the authored content — never copied onto a
# placed hotspot (box+id are placement; type/label are the placed box's own; note is design-only).
_PLANNED_SKIP = {"box", "id", "type", "label", "note"}


def _slug(s):
    """Lowercase label → underscore slug. MUST mirror hotspots_edit.html's `slug` exactly."""
    s = re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")
    return s or "obj"


def _attach_planned_content(placed, planned):
    """Copy authored content from each `plannedHotspots` entry onto the matching placed hotspot,
    matched by (type, slug(label)). Placement (box, id) and the placed box's own type/label are
    preserved; planned content fields overwrite (the placed box arrives with only empty skeletons
    from box-marking, so planned content is the authored source of truth — a re-commit re-applies
    it). Backward-compatible: a planned entry carrying no content beyond {type,label,note} changes
    nothing, so scenarios authored the old way (content filled post-commit) are unaffected."""
    if not isinstance(placed, list) or not planned:
        return placed
    idx = {}
    for p in planned:
        if isinstance(p, dict):
            idx[(p.get("type"), _slug(p.get("label")))] = p
    for h in placed:
        if not isinstance(h, dict):
            continue
        p = idx.get((h.get("type"), _slug(h.get("label"))))
        if not p:
            continue
        for k, v in p.items():
            if k in _PLANNED_SKIP or k.startswith("_"):
                continue
            h[k] = copy.deepcopy(v)
        # a puzzle is graded by EITHER `check` or `question`, never both — let the shape planned
        # authored win, dropping the placed box's leftover empty skeleton of the other kind.
        if "question" in p and "check" not in p:
            h.pop("check", None)
        if "check" in p and "question" not in p:
            h.pop("question", None)
    return placed


def _commit_node(room_key, written, seed_wrap=None, base=None, draft=None, image=None):
    """After 'Send to room' copies scene.png(+_open) into rooms/<ch>/<sc>/<key>/, point the room
    node at them (`panorama`/`panoramaOpen`), mark it built, record which candidate it was built
    from (`builtFrom`, so the harness can colour that candidate's Save chip), and PROMOTE that
    candidate's `draft` wrap + hotspots onto the node. The committed candidate is `image` (else the
    draft's current `image`); its per-candidate entry (`draft["imgs"][image]`) wins, then legacy
    top-level draft, then `seed_wrap`, then a sane default (never a wrapless built room — Finding 1
    belt). `hotspots`: the candidate's authored boxes+content win; else leave the node's."""
    draft = draft or {}
    img = image or draft.get("image")
    per = ((draft.get("imgs") or {}).get(img) if img else None) or {}
    d_wrap = per.get("wrap") if per.get("wrap") is not None else draft.get("wrap")
    d_hotspots = per.get("hotspots") if per.get("hotspots") is not None else draft.get("hotspots")
    fields = {"panorama": "%s/scene.png" % room_key, "built": True}
    if img:
        fields["builtFrom"] = os.path.basename(img)
    if "scene_open.png" in written:
        fields["panoramaOpen"] = "%s/scene_open.png" % room_key
    node = next((r for r in _load_scenario(base).get("rooms", []) if r.get("key") == room_key), None)
    if d_wrap:
        fields["wrap"] = d_wrap
    elif node is not None and not node.get("wrap"):
        fields["wrap"] = seed_wrap or {"haov": 360, "vaov": 90, "hfov": 110, "vOffset": 0, "pitch": 0}
    if d_hotspots is not None:
        # attach any content authored on the node's plannedHotspots onto the freshly-placed boxes,
        # so content authored BEFORE art lands at commit (deepcopy: don't mutate the draft blob)
        planned = (node or {}).get("plannedHotspots") or []
        fields["hotspots"] = _attach_planned_content(copy.deepcopy(d_hotspots), planned)
    return _room_patch(room_key, fields, base)


def _add_room(room_key, title="", technique="", base=None):
    """Append a stub room node to the scenario at `base` (built:false, authoring skeleton, linear
    unlock on the previous room). Returns the new node."""
    key = re.sub(r"[^A-Za-z0-9_]", "", str(room_key or ""))
    if not key:
        raise ValueError("room key must be letters/digits/underscore")
    with SAVE_LOCK:
        doc = _load_scenario(base)
        rooms = doc.setdefault("rooms", [])
        if any(r.get("key") == key for r in rooms):
            raise ValueError("room %r already exists" % key)
        prev = rooms[-1]["key"] if rooms else None
        node = {
            "key": key, "title": title or key, "technique": technique or "",
            "puzzleType": 1, "built": False,
            "authoring": {"tag": key, "scenePrompt": "", "doorPrompt": ""},
            "unlockedWhen": ({"solved": prev} if prev else True),
            "onSolve": [{"set": key + "_solved"}, {"inc": "rooms_solved"}],
            "designNote": "New room — art + puzzle not built yet.",
        }
        rooms.append(node)
        _save_scenario(doc, base)
    return node


def _new_scenario(chapter, scenario, title=""):
    """Scaffold rooms/<chapter>/<scenario>/scenario.json (one stub room + _scratch) with a fresh id.
    Returns {chapter, scenario, id}."""
    ch = re.sub(r"[^A-Za-z0-9_]", "", str(chapter or ""))
    sc = re.sub(r"[^A-Za-z0-9_]", "", str(scenario or ""))
    if not ch or not sc:
        raise ValueError("need chapter + scenario (letters/digits/underscore)")
    d = _scenario_dir(ch, sc)
    p = os.path.join(d, "scenario.json")
    if os.path.exists(p):
        raise ValueError("%s/%s already exists" % (ch, sc))
    # fresh scenario id: beyond existing on-disk ids AND the archived 1–5 decoder keys
    ids = []
    for sp in glob.glob(os.path.join(ROOMS_ROOT, "*", "*", "scenario.json")):
        try:
            ids.append(int(json.load(open(sp)).get("id", 0)))
        except Exception:
            pass
    new_id = max(ids + [5]) + 1
    doc = {
        "chapter": ch, "scenario": sc, "id": new_id,
        "title": title or sc, "subtitle": "", "story": "", "enterLabel": "Enter →",
        "done": {"title": "Complete", "body": "Nice work — you've finished this scenario."},
        "packages": [], "datasets": [], "setup": "",
        "state": {"rooms_solved": 0},
        "rooms": [{
            "key": "room1", "title": "Room 1", "technique": "", "puzzleType": 1, "built": False,
            "authoring": {"tag": "room1", "scenePrompt": "", "doorPrompt": ""},
            "unlockedWhen": True,
            "onSolve": [{"set": "room1_solved"}, {"inc": "rooms_solved"}],
            "designNote": "New scenario's first room.",
        }],
    }
    os.makedirs(os.path.join(d, "_scratch"), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)
    return {"chapter": ch, "scenario": sc, "id": new_id}


# ---- per-room DRAFT (draft-in-scratch) ----
# Wrap / hotspots / puzzle content authored against a picked candidate are saved to
# _scratch/draft.json keyed by room; "Send to room" promotes them onto the node. Keeps
# scenario.json clean until you commit and lets you draft several rooms before deciding.

def _draft_path(base=None):
    return os.path.join(base or COMMIT_BASE, "_scratch", "draft.json")


def _load_draft(base=None):
    try:
        with open(_draft_path(base), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_draft(doc, base=None):
    p = _draft_path(base)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)


def _draft_room_merge(room_key, fields, base=None):
    """Merge {image?, wrap?, hotspots?} into the draft entry for room_key. `image` records the
    currently-picked candidate. wrap/hotspots are stored PER CANDIDATE — under entry["imgs"][image]
    — so several candidate images can each carry their own wrap/hotspots progress instead of one
    shared room-level blob (which mismatched when wrap was framed on one candidate and hotspots
    marked on another). The editors always send `image` alongside wrap/hotspots; a wrap/hotspots
    save with no image (shouldn't happen) falls back to legacy top-level so nothing is lost."""
    key = re.sub(r"[^A-Za-z0-9_]", "", str(room_key or ""))
    if not key:
        raise ValueError("empty roomKey")
    if not isinstance(fields, dict):
        raise ValueError("fields must be an object")
    d = _load_draft(base)
    entry = d.get(key, {})
    img = fields.get("image")
    if img is not None:
        entry["image"] = img                        # the currently-picked candidate
    if img and ("wrap" in fields or "hotspots" in fields):
        per = entry.setdefault("imgs", {}).setdefault(img, {})
        if "wrap" in fields:
            per["wrap"] = fields["wrap"]
        if "hotspots" in fields:
            per["hotspots"] = fields["hotspots"]
    elif "wrap" in fields or "hotspots" in fields:  # no image → legacy top-level (defensive)
        for k in ("wrap", "hotspots"):
            if k in fields:
                entry[k] = fields[k]
    d[key] = entry
    _save_draft(d, base)
    return entry


def _draft_clear(room_key, base=None):
    d = _load_draft(base)
    if d.pop(room_key, None) is not None:
        _save_draft(d, base)


_apply_active()

# In-process job state, one entry per slot (the four generate columns each own a
# slot; door-open uses its own "door" slot). Guarded by LOCK. Slots run
# concurrently, so filenames are namespaced by tag and indices are reserved
# atomically to keep parallel jobs from colliding.
JOBS = {}          # slot(str) -> {active,kind,done,total,outputs,error,tag}
RESERVED = {}      # filename prefix -> highest index handed out so far
LOCK = threading.Lock()

_IDLE = {"active": False, "kind": None, "done": 0, "total": 0,
         "outputs": [], "error": None, "tag": None}


def _sanitize_tag(tag):
    tag = re.sub(r"[^a-z0-9]+", "_", (tag or "").lower()).strip("_")
    return tag or "gen"


def _disk_next(prefix):
    n = 0
    for p in glob.glob(os.path.join(SCENE, prefix + "*.png")):
        m = re.search(re.escape(prefix) + r"(\d+)\.png$", os.path.basename(p))
        if m:
            n = max(n, int(m.group(1)))
    return n + 1


def _disk_next_in(d, prefix):
    """Next free index for `prefix` in an arbitrary dir (base-scoped clue-image gen, not global SCENE)."""
    n = 0
    for p in glob.glob(os.path.join(d, prefix + "*.png")):
        m = re.search(re.escape(prefix) + r"(\d+)\.png$", os.path.basename(p))
        if m:
            n = max(n, int(m.group(1)))
    return n + 1


def _clue_prefix(room_key, clue_id):
    """(sanitised roomKey, clueId, filename prefix) for a clue's candidate artwork in _scratch."""
    rk = re.sub(r"[^A-Za-z0-9_]", "", str(room_key or ""))
    ci = re.sub(r"[^A-Za-z0-9_]", "", str(clue_id or ""))
    if not rk or not ci:
        raise ValueError("need roomKey + clueId")
    return rk, ci, "clue_%s_%s_" % (rk, ci)


def _reserve(prefix, n):
    """Atomically hand out n consecutive indices for prefix (disk + in-flight)."""
    with LOCK:
        start = max(_disk_next(prefix), RESERVED.get(prefix, 0) + 1)
        RESERVED[prefix] = start + n - 1
        return start


def _run_generate(slot, tag, prompt, n, quality, size):
    os.makedirs(SCENE, exist_ok=True)
    prefix = f"gpt_{tag}_"
    ptmp = os.path.join(SCENE, f".prompt_{slot}.txt")
    with open(ptmp, "w", encoding="utf-8") as f:
        f.write(prompt)
    start = _reserve(prefix, n)
    for i in range(n):
        out = os.path.join(SCENE, f"{prefix}{start + i}.png")
        try:
            subprocess.run(["python3", GEN, "gen", "--prompt-file", ptmp,
                            "--out", out, "--quality", quality, "--size", size],
                           check=True, capture_output=True, text=True)
            with LOCK:
                JOBS[slot]["outputs"].append(os.path.basename(out))
                JOBS[slot]["done"] += 1
        except subprocess.CalledProcessError as e:
            with LOCK:
                JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
            break
    with LOCK:
        JOBS[slot]["active"] = False


def _run_gen_clue(slot, base, prefix, prompt, n, size):
    """Background gpt-image-2 gen of a CLUE artwork into <base>/_scratch/<prefix>NNN.png (N candidates).
    Same engine as scene gen but base-scoped + its own filename prefix, so a clue's images don't collide
    with room scenes. The picked candidate is copied into the room dir by /api/set-clue-image."""
    scratch = os.path.join(base, "_scratch")
    os.makedirs(scratch, exist_ok=True)
    ptmp = os.path.join(scratch, ".prompt_%s.txt" % slot)
    with open(ptmp, "w", encoding="utf-8") as f:
        f.write(prompt)
    start = _disk_next_in(scratch, prefix)
    for i in range(n):
        out = os.path.join(scratch, "%s%d.png" % (prefix, start + i))
        try:
            subprocess.run(["python3", GEN, "gen", "--prompt-file", ptmp,
                            "--out", out, "--quality", "high", "--size", size],
                           check=True, capture_output=True, text=True)
            with LOCK:
                JOBS[slot]["outputs"].append(os.path.basename(out))
                JOBS[slot]["done"] += 1
        except subprocess.CalledProcessError as e:
            with LOCK:
                JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
            break
    with LOCK:
        JOBS[slot]["active"] = False


def _run_dooropen(slot, image, box, prompt):
    inp = os.path.join(SCENE, os.path.basename(image))
    stem = os.path.splitext(os.path.basename(image))[0]
    out = os.path.join(SCENE, stem + "_open.png")
    boxstr = ",".join(str(x) for x in box)
    try:
        subprocess.run(["python3", GEN, "dooropen", "--input", inp, "--box", boxstr,
                        "--prompt", prompt, "--out", out],
                       check=True, capture_output=True, text=True)
        with LOCK:
            JOBS[slot]["outputs"].append(os.path.basename(out))
            JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_dooropen_room(slot, base, room_key, box, prompt):
    """Door-open for a COMMITTED room (Finding 3 — moved out of the retired inline editor): masked
    gpt edit of the door box on rooms/<ch>/<sc>/<key>/scene.png -> scene_open.png, then point the
    node's `panoramaOpen` at it. This is the per-room way to make the door-open panorama."""
    inp = os.path.join(base, room_key, "scene.png")
    out = os.path.join(base, room_key, "scene_open.png")
    boxstr = ",".join(str(x) for x in box)
    try:
        subprocess.run(["python3", GEN, "dooropen", "--input", inp, "--box", boxstr,
                        "--prompt", prompt, "--out", out],
                       check=True, capture_output=True, text=True)
        _room_patch(room_key, {"panoramaOpen": "%s/scene_open.png" % room_key}, base)
        with LOCK:
            JOBS[slot]["outputs"].append("scene_open.png")
            JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _start(slot, kind, target, total, tag=None):
    with LOCK:
        j = JOBS.get(slot)
        if j and j["active"]:
            return False
        JOBS[slot] = {"active": True, "kind": kind, "done": 0, "total": total,
                      "outputs": [], "error": None, "tag": tag}
    threading.Thread(target=target, daemon=True).start()
    return True


def _commit_room(image, room_dir, scene=None):
    """Copy a chosen closed base + its `_open` partner into a room directory under STABLE names
    (scene.png / scene_open.png), so the pair travels together. room_dir is relative to the
    escape_rooms/ tree; `scene` is the candidate pool to read from (default: the active
    scenario's _scratch — pass an explicit one so a commit targets the scenario the BOARD loaded,
    not whatever is ACTIVE at commit time). Returns (written_files, normalised_room_dir,
    seed_wrap) where seed_wrap is the candidate's tuned wrap, for the node to adopt.

    NOTE (Finding 3): the old roomN/wrap.json + roomN/hotspots.json sidecars are NO LONGER written
    — the room NODE in scenario.json holds wrap + hotspots now, and the player never read those
    files. The candidate's tuned wrap is returned (not written) so the node can seed from it."""
    scene = scene or SCENE
    room_dir = (room_dir or "").strip().strip("/").replace("\\", "/")
    if not room_dir:
        raise ValueError("roomDir is empty")
    dest = os.path.abspath(os.path.join(ESCAPE_ROOT, room_dir))
    if dest == ESCAPE_ROOT or not dest.startswith(ESCAPE_ROOT + os.sep):
        raise ValueError("roomDir must be a subdirectory inside the escape_rooms tree")
    src = os.path.join(scene, os.path.basename(image))
    if not os.path.exists(src):
        raise ValueError(f"image not found in scene/: {image}")
    os.makedirs(dest, exist_ok=True)
    written = []
    shutil.copyfile(src, os.path.join(dest, "scene.png"))
    written.append("scene.png")
    stem = os.path.splitext(os.path.basename(image))[0]
    openp = os.path.join(scene, stem + "_open.png")
    if os.path.exists(openp):
        shutil.copyfile(openp, os.path.join(dest, "scene_open.png"))
        written.append("scene_open.png")
    seed_wrap = None
    try:
        wrap = json.load(open(os.path.join(scene, "wrap.json")))
        wi = wrap.get(image) or (wrap if wrap.get("image") == image else None)
        if wi:
            seed_wrap = {k: wi[k] for k in ("haov", "vaov", "hfov", "vOffset", "pitch") if k in wi}
    except Exception:
        pass
    return written, room_dir, seed_wrap


def _set_cover(image, base):
    """Copy a chosen _scratch candidate to <scenario>/cover.png (a stable, pushable name) and point
    `scenario.cover` at it. Cover art is the scenario's poster for the book's exercises page; the
    churny `gpt_cover_*` candidates stay in gitignored _scratch, only cover.png is committed. Returns
    the relative cover path."""
    name = os.path.basename(str(image or ""))
    if not name:
        raise ValueError("need image")
    src = os.path.join(base, "_scratch", name)
    if not os.path.isfile(src):
        raise ValueError("no such candidate: %s" % name)
    shutil.copyfile(src, os.path.join(base, "cover.png"))
    _scenario_patch({"cover": "cover.png"}, base)
    return "cover.png"


def _delete_scene(base, fn):
    """Delete a _scratch candidate image the author no longer wants: remove <fn> AND its `_open`
    partner from <base>/_scratch, and forget its per-candidate state — the wrap.json entry, the
    draft `imgs` entry in every room, and any draft `image` selection that pointed at it. Confined
    to _scratch by basename (a committed room's scene.png, outside _scratch, is never touched).
    Returns the list of files actually removed."""
    fn = os.path.basename(str(fn or ""))
    if not fn.endswith(".png"):
        raise ValueError("need a .png candidate")
    scratch = os.path.abspath(os.path.join(base, "_scratch"))
    removed = []
    for name in (fn, os.path.splitext(fn)[0] + "_open.png"):
        p = os.path.abspath(os.path.join(scratch, name))
        if p.startswith(scratch + os.sep) and os.path.isfile(p):
            os.remove(p)
            removed.append(name)
    # forget the wrap.json entry (legacy per-image map)
    wp = os.path.join(scratch, "wrap.json")
    try:
        if os.path.isfile(wp):
            w = json.load(open(wp))
            if isinstance(w, dict) and fn in w:
                del w[fn]
                with open(wp, "w") as f:
                    json.dump(w, f, indent=2)
    except Exception:
        pass
    # forget the per-candidate draft state (imgs entry + any selection pointing at it)
    d = _load_draft(base)
    changed = False
    for entry in d.values():
        if not isinstance(entry, dict):
            continue
        imgs = entry.get("imgs")
        if isinstance(imgs, dict) and imgs.pop(fn, None) is not None:
            changed = True
        if entry.get("image") == fn:
            entry.pop("image", None)
            changed = True
    if changed:
        _save_draft(d, base)
    return removed


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass

    def _cors(self):
        """Permit cross-origin API calls from the playtest server (test_play.html on :8055 posts the
        sound-mixer volumes here to :8751). The server binds 127.0.0.1 only, so reflecting the origin
        is a localhost-dev convenience, not an exposure. Same-origin harness calls are unaffected."""
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def do_OPTIONS(self):
        # CORS preflight for the cross-origin mixer POST (JSON body → non-simple request).
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        route = self.path.split("?")[0]
        if route == "/api/status":
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            with LOCK:
                if "slot" in qs:
                    return self._json(dict(JOBS.get(qs["slot"][0], _IDLE)))
                return self._json({s: dict(j) for s, j in JOBS.items()})
        if route == "/api/scenes":
            files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SCENE, "*.png")))
            return self._json({"scenes": files})
        if route == "/api/audio-candidates":   # candidate sfx loops in <scenario>/_scratch/audio/
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            d = os.path.join(base, "_scratch", "audio")
            files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(d, "*.mp3")))
            return self._json({"files": files})
        if route == "/api/clue-candidates":   # generated artwork candidates for one clue hotspot
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            try:
                _, _, prefix = _clue_prefix(qs.get("roomKey", [""])[0], qs.get("clueId", [""])[0])
            except ValueError as ve:
                return self._json({"error": str(ve)}, 400)
            files = sorted(os.path.basename(p) for p in
                           glob.glob(os.path.join(base, "_scratch", prefix + "*.png")))
            return self._json({"files": files})
        if route == "/api/scenarios":
            return self._json({"scenarios": _list_scenarios(), "active": dict(ACTIVE)})
        if route == "/api/scenario-config":
            return self._json(_scenario_config())
        if route == "/api/scenario":         # ?chapter&scenario for a specific one, else active
            try:
                return self._json(_load_scenario(self._query_base()))
            except Exception as e:  # noqa: BLE001
                return self._json({"error": str(e)}, 500)
        if route == "/api/draft":            # ?chapter&scenario&roomKey — the room's _scratch draft
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            return self._json(_load_draft(base).get(qs.get("roomKey", [""])[0], {}))
        if route.startswith("/scene/"):     # candidate pool (active scenario's _scratch)
            return self._serve_file(SCENE, route[len("/scene/"):])
        if route.startswith("/sfile/"):      # a file under a scenario dir (?chapter&scenario, else active)
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            return self._serve_file(base, route[len("/sfile/"):])
        return super().do_GET()

    def _query_base(self):
        """Scenario dir from ?chapter&scenario in the URL (else active COMMIT_BASE). Lets an
        editor tab read/serve a scenario explicitly, decoupled from server-global ACTIVE."""
        qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
        return _scenario_base(qs.get("chapter", [""])[0], qs.get("scenario", [""])[0])

    def _serve_file(self, base, rel):
        """Serve a file from under `base` (SCENE or the scenario dir), which live outside the
        served ROOT. Path-confined to `base`."""
        rel = urllib.parse.unquote(rel).lstrip("/")
        p = os.path.abspath(os.path.join(base, rel))
        if not p.startswith(os.path.abspath(base) + os.sep) or not os.path.isfile(p):
            return self._json({"error": "not found"}, 404)
        ctype = ("image/png" if p.endswith(".png")
                 else "application/json" if p.endswith(".json")
                 else "audio/mpeg" if p.endswith(".mp3")
                 else "audio/wav" if p.endswith(".wav")
                 else "audio/ogg" if p.endswith((".ogg", ".oga"))
                 else "application/octet-stream")
        with open(p, "rb") as f:
            b = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        route = self.path.split("?")[0]
        try:
            if route == "/api/generate":
                req = self._body()
                prompt = (req.get("prompt") or "").strip()
                if not prompt:
                    return self._json({"ok": False, "error": "empty prompt"}, 400)
                n = max(1, min(int(req.get("n", 1)), 6))
                q = req.get("quality", "medium")
                size = req.get("size", "1536x1024")
                slot = str(req.get("slot", "0"))
                tag = _sanitize_tag(req.get("tag"))
                if not _start(slot, "generate",
                              lambda: _run_generate(slot, tag, prompt, n, q, size),
                              n, tag=tag):
                    return self._json({"ok": False, "error": "this column is already running"}, 409)
                return self._json({"ok": True, "total": n, "slot": slot, "tag": tag})
            if route == "/api/dooropen":
                req = self._body()
                img = req.get("image")
                box = req.get("box")
                prompt = (req.get("prompt") or "").strip()
                if not img or not isinstance(box, list) or len(box) != 4:
                    return self._json({"ok": False, "error": "need image + box[4]"}, 400)
                if not prompt:
                    return self._json({"ok": False, "error": "empty door prompt"}, 400)
                if not _start("door", "dooropen",
                              lambda: _run_dooropen("door", img, box, prompt), 1):
                    return self._json({"ok": False, "error": "a door-open job is already running"}, 409)
                return self._json({"ok": True})
            if route == "/api/select-scenario":
                req = self._body()
                try:
                    _select_scenario(str(req.get("chapter") or ""), str(req.get("scenario") or ""))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "active": dict(ACTIVE), "config": _scenario_config()})
            if route == "/api/room-patch":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    node = _room_patch(req.get("roomKey"), req.get("fields") or {}, base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "room": node})
            if route == "/api/scenario-patch":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    changed = _scenario_patch(req.get("fields") or {}, base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "changed": changed})
            if route == "/api/save-mix":
                # volume-only writeback from the test-play sound mixer (shared/sfx-mixer.js).
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    mv = req.get("musicVolume")
                    summary = _apply_mix(mv if mv is not None else None,
                                         req.get("rooms") or {}, base)
                except (ValueError, TypeError) as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **summary})
            if route == "/api/draft-save":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    fields = {k: req[k] for k in ("image", "wrap", "hotspots") if k in req}
                    entry = _draft_room_merge(req.get("roomKey"), fields, base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "draft": entry})
            if route == "/api/add-room":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    node = _add_room(req.get("roomKey"), req.get("title", ""), req.get("technique", ""), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "room": node})
            if route == "/api/dooropen-room":
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                box = req.get("box")
                prompt = (req.get("prompt") or "").strip()
                if not rk or not isinstance(box, list) or len(box) != 4:
                    return self._json({"ok": False, "error": "need roomKey + box[4]"}, 400)
                if not prompt:
                    return self._json({"ok": False, "error": "empty door prompt"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                if not os.path.isfile(os.path.join(base, rk, "scene.png")):
                    return self._json({"ok": False, "error": "room %s has no committed scene.png" % rk}, 400)
                if not _start("door", "dooropen",
                              lambda: _run_dooropen_room("door", base, rk, box, prompt), 1):
                    return self._json({"ok": False, "error": "a door-open job is already running"}, 409)
                return self._json({"ok": True})
            if route == "/api/new-scenario":
                req = self._body()
                try:
                    info = _new_scenario(req.get("chapter"), req.get("scenario"), req.get("title", ""))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **info})
            if route == "/api/commit-room":
                req = self._body()
                img = req.get("image")
                # roomKey (preferred) commits into rooms/<ch>/<sc>/<key> of the scenario the board
                # LOADED (explicit chapter+scenario in the body; blank falls back to active) —
                # never whatever happens to be ACTIVE at commit time (Finding 2, commit leg).
                # roomDir stays supported as an explicit escape_rooms-relative override.
                room_key = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")) or None
                room_dir = req.get("roomDir")
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                if room_key and not room_dir:
                    room_dir = os.path.relpath(os.path.join(base, room_key), ESCAPE_ROOT)
                # a room's _scratch draft supplies the image (if none passed) + the wrap/hotspots to promote
                draft = _load_draft(base).get(room_key, {}) if room_key else {}
                if not img:
                    img = draft.get("image")
                if not img or not room_dir:
                    return self._json({"ok": False, "error": "need image (or a draft with one) + roomKey or roomDir"}, 400)
                try:
                    written, rd, seed_wrap = _commit_room(img, room_dir, scene=os.path.join(base, "_scratch"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                node = None
                if room_key:   # point the node at the images + promote the draft (wrap/hotspots), then clear it
                    try:
                        node = _commit_node(room_key, written, seed_wrap, base, draft=draft, image=img)
                        _draft_clear(room_key, base)
                    except ValueError:
                        node = None   # roomKey isn't a node (e.g. an ad-hoc roomDir) — images still committed
                return self._json({"ok": True, "dest": rd, "written": written, "room": node})
            if route == "/api/set-cover":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    cover = _set_cover(req.get("image"), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "cover": cover})
            if route == "/api/delete-scene":
                # remove a _scratch candidate the author no longer wants (+ its _open partner + state)
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    removed = _delete_scene(base, req.get("file"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "removed": removed})
            if route == "/api/commit-sound":
                # audition -> add a layer: MATERIALISE a chosen _scratch/audio/ candidate into the
                # committed <scenario>/audio/ (same filename, a stable pushable name) and return its
                # play.html-relative src. The client appends it as an sfx layer and saves the whole
                # `sfx` array via /api/room-patch — so a room can hold several layered sounds. The
                # churny candidate pool stays in gitignored _scratch; only materialised picks ship.
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                fn = os.path.basename(str(req.get("file") or ""))
                if not fn:
                    return self._json({"ok": False, "error": "need file"}, 400)
                srcp = os.path.join(base, "_scratch", "audio", fn)
                if not os.path.isfile(srcp):
                    return self._json({"ok": False, "error": "no such candidate: %s" % fn}, 400)
                os.makedirs(os.path.join(base, "audio"), exist_ok=True)
                out = "audio/%s" % fn
                shutil.copyfile(srcp, os.path.join(base, out))
                return self._json({"ok": True, "src": out})
            if route == "/api/gen-clue-image":
                # generate CLUE artwork with gpt-image-2 (a clue can BE a generated image, not just text).
                # N candidates land in <scenario>/_scratch/clue_<rk>_<clueId>_NNN.png; the client polls
                # /api/status?slot=clue_<rk>_<clueId>, lists them via /api/clue-candidates, and picks one.
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    rk, ci, prefix = _clue_prefix(req.get("roomKey"), req.get("clueId"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                prompt = (req.get("prompt") or "").strip()
                if not prompt:
                    return self._json({"ok": False, "error": "empty prompt"}, 400)
                n = max(1, min(int(req.get("n", 2)), 4))
                size = req.get("size", "1024x1024")
                slot = "clue_%s_%s" % (rk, ci)
                if not _start(slot, "generate",
                              lambda: _run_gen_clue(slot, base, prefix, prompt, n, size), n):
                    return self._json({"ok": False, "error": "this clue is already generating"}, 409)
                return self._json({"ok": True, "slot": slot, "total": n})
            if route == "/api/set-clue-image":
                # pick a generated candidate: copy _scratch/<file> -> <scenario>/<rk>/clue_<clueId>.png
                # (committed, ships) and return its play.html-relative src; the client sets clue.image.
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    rk, ci, _ = _clue_prefix(req.get("roomKey"), req.get("clueId"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                fn = os.path.basename(str(req.get("file") or ""))
                if not fn:
                    return self._json({"ok": False, "error": "need file"}, 400)
                srcp = os.path.join(base, "_scratch", fn)
                if not os.path.isfile(srcp):
                    return self._json({"ok": False, "error": "no such candidate: %s" % fn}, 400)
                os.makedirs(os.path.join(base, rk), exist_ok=True)
                out = "%s/clue_%s.png" % (rk, ci)
                shutil.copyfile(srcp, os.path.join(base, out))
                return self._json({"ok": True, "src": out})
            if route == "/api/save-hotspots":
                req = self._body()
                if not req.get("image"):
                    return self._json({"ok": False, "error": "no image"}, 400)
                keep = {k: req[k] for k in ("image", "haov", "vaov", "vOffset",
                                            "hotspots") if k in req}
                keep.setdefault("hotspots", [])
                with open(os.path.join(SCENE, "hotspots.json"), "w") as f:
                    json.dump(keep, f, indent=2)
                return self._json({"ok": True, "count": len(keep["hotspots"])})
            if route == "/api/save-wrap":
                req = self._body()
                img = req.get("image")
                if not img:
                    return self._json({"ok": False, "error": "no image"}, 400)
                path = os.path.join(SCENE, "wrap.json")
                data = {}
                if os.path.exists(path):
                    try:
                        data = json.load(open(path))
                    except Exception:
                        data = {}
                # migrate a legacy flat {image, haov, ...} record into the per-image map
                if isinstance(data, dict) and "image" in data and "haov" in data:
                    old = data.pop("image")
                    data = {old: {k: v for k, v in data.items()}}
                if not isinstance(data, dict):
                    data = {}
                data[img] = {k: req[k] for k in ("haov", "vaov", "hfov",
                                                 "vOffset", "pitch") if k in req}
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
                return self._json({"ok": True, "image": img})
        except Exception as e:  # noqa: BLE001 — report to the UI
            return self._json({"ok": False, "error": str(e)}, 500)
        return self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"gpt harness -> http://127.0.0.1:{PORT}/harness_gpt.html", flush=True)
    httpd.serve_forever()
