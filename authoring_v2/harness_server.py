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
import math
import shutil
import time
import threading
import subprocess
import scene_spec   # the scene-spec model: render_prompt / cinemagraph_jobs / to_hotspots (art-pipeline P1)
import localizer    # vision box-finder for spec elements (art-pipeline P2); reuses OPENAI_API_KEY
import http.server
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ESCAPE_ROOT = os.path.abspath(os.path.join(HERE, ".."))  # escape_rooms/ (commit targets live under here)
ROOT = os.path.join(HERE, "ui")  # served web root: the authoring pages (harness_gpt/view360/reproject_test)
ROOMS_ROOT = os.path.join(ESCAPE_ROOT, "rooms")          # rooms/<chapter>/<scenario>/
GEN = os.path.join(HERE, "generate_scene.py")
MAX_PANO_CANDIDATES = 3    # build-world level 1: up to this many candidate panos per room in _scratch (l1_<room>_<n>.png)
# V2 harness (authoring_v2/) runs on :8752 so it can sit alongside the production :8751 harness while
# the image-pipeline V2 upgrades are built (see notes/image_pipeline_v2.md). Both share the same rooms/
# tree (ESCAPE_ROOT/..), so run only one at a time when authoring the SAME scenario.
PORT = 8752
# Cinemagraph generation runs as a DETACHED script (long ~5 min GPU job that pauses lm_server) — the
# harness fires it off and the editor polls a status file. See ~/ComfyUI/cinemagraph_gen.py.
CINE_VENV = os.path.expanduser("~/ComfyUI/.venv/bin/python")
CINE_GEN = os.path.expanduser("~/ComfyUI/cinemagraph_gen.py")
# Batch runner: runs a queue of cinemagraph/door/variant jobs back-to-back, bouncing lm_server ONCE (the
# walk-away flow). Launched DETACHED like CINE_GEN; writes a status file the editor polls. See that script.
BATCH_GEN = os.path.expanduser("~/ComfyUI/cinemagraph_batch.py")
# Batched cinemagraphs render this many candidates per hotspot (different random seeds) for the editor to
# pick from — the motion analogue of generating multiple art scenes. The immediate single "Generate" stays 1.
# Local model → no API cost, so we generate a generous spread to pick from (walk-away batch; just slower).
CINE_CANDIDATES = 5

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


def _find_hotspot(base, room_key, hotspot_id):
    """(doc, node, hotspot) for a committed room's hotspot, or raise ValueError. Caller holds SAVE_LOCK."""
    doc = _load_scenario(base)
    rooms = doc.get("rooms")
    if not isinstance(rooms, list):
        raise ValueError("scenario has no rooms[]")
    node = next((r for r in rooms if r.get("key") == room_key), None)
    if node is None:
        raise ValueError("no room with key %r" % room_key)
    hs = node.get("hotspots")
    if not isinstance(hs, list):
        raise ValueError("room %r has no hotspots (commit it first)" % room_key)
    spot = next((h for h in hs if h.get("id") == hotspot_id), None)
    if spot is None:
        raise ValueError("no hotspot %r in room %r" % (hotspot_id, room_key))
    return doc, node, spot


def _add_variant(room_key, hotspot_id, variant, base=None):
    """Add/replace a per-hotspot state VARIANT (Phase 3) on hotspot `hotspot_id`, keyed by `state`:
    regenerating the same state replaces its entry (idempotent), else it's appended. Writes nested
    into hotspots[].variants[] (the shallow _room_patch can't reach that depth)."""
    if not isinstance(variant, dict) or not variant.get("state"):
        raise ValueError("variant needs a state")
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        variants = spot.get("variants")
        if not isinstance(variants, list):
            variants = []
            spot["variants"] = variants
        for i, v in enumerate(variants):
            if v.get("state") == variant["state"]:
                variants[i] = variant
                break
        else:
            variants.append(variant)
        _save_scenario(doc, base)
    return spot


def _remove_variant(room_key, hotspot_id, state, base=None):
    """Drop the variant with the given `state` from a hotspot (leaves the PNG on disk, like _scratch)."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        spot["variants"] = [v for v in (spot.get("variants") or []) if v.get("state") != state]
        _save_scenario(doc, base)
    return spot


def _update_variant(room_key, hotspot_id, state, fields, base=None):
    """Merge `fields` (e.g. `when`, `prompt`, `box`) into the existing variant with `state`, WITHOUT
    regenerating its image — so the trigger can be tuned without a new gpt call. Raises if absent."""
    if not isinstance(fields, dict):
        raise ValueError("fields must be an object")
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        target = next((v for v in (spot.get("variants") or []) if v.get("state") == state), None)
        if target is None:
            raise ValueError("no variant %r on hotspot %r" % (state, hotspot_id))
        target.update(fields)
        _save_scenario(doc, base)
    return target


def _cine_status_path(base, room_key, hotspot_id):
    """Where the detached cinemagraph generator writes its progress JSON (per hotspot), for the editor to poll."""
    d = os.path.join(base, "_scratch"); os.makedirs(d, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", "%s_%s" % (room_key, hotspot_id)).strip("_") or "hs"
    return os.path.join(d, "cine_status_%s.json" % safe)


def _launch_cinemagraph(base, room_key, hotspot_id, box, prompt, loop="boomerang"):
    """Fire off cinemagraph_gen.py DETACHED (start_new_session) to animate the hotspot's box on the
    committed scene. It owns the GPU handoff + guaranteed lm_server restart, and writes the node's
    `cinemagraph` field on success. Returns (status_path, video_rel)."""
    scene = os.path.join(base, room_key, "scene.png")
    fname = "cine_%s.mp4" % (re.sub(r"[^A-Za-z0-9_]+", "_", hotspot_id).strip("_") or "hs")
    out = os.path.join(base, room_key, fname)
    vrel = "%s/%s" % (room_key, fname)
    status_path = _cine_status_path(base, room_key, hotspot_id)
    with open(status_path, "w") as f:
        json.dump({"state": "running", "step": "starting"}, f)
    logf = open(os.path.join(base, "_scratch", "cine_gen.log"), "a")
    subprocess.Popen(
        [CINE_VENV, CINE_GEN, "--scene", scene, "--box", ",".join(str(x) for x in box),
         "--prompt", prompt, "--out", out, "--scenario", os.path.join(base, "scenario.json"),
         "--room", room_key, "--hotspot", hotspot_id, "--video-rel", vrel, "--status", status_path,
         "--loop", (loop if loop in ("boomerang", "crossfade") else "boomerang")],
        stdout=logf, stderr=logf, start_new_session=True)
    return status_path, vrel


def _remove_cinemagraph(room_key, hotspot_id, base=None):
    """Drop a hotspot's `cinemagraph` (leaves the mp4 on disk, like a _scratch orphan)."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        spot.pop("cinemagraph", None)
        _save_scenario(doc, base)
    return spot


def _pick_cinemagraph(room_key, hotspot_id, index, base=None):
    """Promote candidate `index` (from a batch's `cinemagraphCandidates`) to the hotspot's `cinemagraph`,
    then clear the candidate list. The unused candidate mp4s stay on disk (harmless orphans). Returns the
    chosen cinemagraph."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        cands = spot.get("cinemagraphCandidates") or []
        if not (0 <= index < len(cands)):
            raise ValueError("no candidate %s (have %d)" % (index, len(cands)))
        c = cands[index]
        spot["cinemagraph"] = {"box": c.get("box"), "video": c["video"], "prompt": c.get("prompt", ""),
                               "loop": c.get("loop", "boomerang"), "seed": c.get("seed")}
        spot.pop("cinemagraphCandidates", None)
        _save_scenario(doc, base)
    return spot["cinemagraph"]


# --- Batch cinemagraph/door/variant queue (walk-away flow) -------------------------------------------------
# A per-scenario queue of scene-baked gen jobs. Any wrap tab appends via /api/batch-add; /api/batch-run
# expands the queue to a run file and launches cinemagraph_batch.py DETACHED, which stops lm_server ONCE
# (only if the queue holds cinemagraph jobs), runs every job, restarts lm ONCE, and writes a status file the
# editor polls. Minimal jobs are stored (re-expanded at run time, so a late commit/rename resolves fresh).
BATCH_LOCK = threading.Lock()


def _batch_dir(base):
    d = os.path.join(base, "_scratch"); os.makedirs(d, exist_ok=True); return d


def _batch_queue_path(base):  return os.path.join(_batch_dir(base), "cine_batch.json")
def _batch_run_path(base):    return os.path.join(_batch_dir(base), "cine_batch_run.json")
def _batch_status_path(base): return os.path.join(_batch_dir(base), "cine_batch_status.json")


def _batch_read_queue(base):
    p = _batch_queue_path(base)
    if not os.path.isfile(p):
        return []
    try:
        return json.load(open(p, encoding="utf-8")).get("jobs", [])
    except Exception:  # noqa: BLE001
        return []


def _batch_write_queue(base, jobs):
    p = _batch_queue_path(base); tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"jobs": jobs}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)


def _batch_status(base):
    p = _batch_status_path(base)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _batch_running(base):
    s = _batch_status(base)
    return bool(s and s.get("state") == "running")


def _batch_safe(s):
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(s or "")).strip("_")


def _expand_job(base, job, cur_boxes=None):
    """Turn a minimal queued job (type/roomKey/hotspotId/box/prompt/…) into a fully-resolved job with
    scene/out/rel paths, using the SAME filename conventions as the single-shot _launch_cinemagraph /
    _run_dooropen_room / _run_variant, so batched output lands exactly where the one-shot path puts it.
    Raises ValueError on a bad job (so batch-add can reject it, and batch-run reports before launching).

    `cur_boxes` {(room,hotspotId): box}: when given (at batch-RUN time), the hotspot's CURRENT box on the
    node overrides the box captured when the job was queued — so nudging a box (or redrawing it as a
    seam-wrap box, x0>x1) AFTER apply-spec but before Run all actually takes effect. This is the whole point
    of the human box-review step; without it the batch crops from the stale approx box."""
    typ = job.get("type")
    rk = re.sub(r"[^A-Za-z0-9_]", "", str(job.get("roomKey") or ""))
    hid = str(job.get("hotspotId") or "").strip()
    box = job.get("box")
    if cur_boxes and (rk, hid) in cur_boxes:
        box = cur_boxes[(rk, hid)]   # freshest box from the node wins at run time
    prompt = (job.get("prompt") or "").strip()
    if typ not in ("cinemagraph", "door", "variant"):
        raise ValueError("bad job type %r" % typ)
    if not rk or not hid:
        raise ValueError("job needs roomKey + hotspotId")
    if not isinstance(box, list) or len(box) != 4:
        raise ValueError("job needs box[4]")
    if not prompt:
        raise ValueError("job needs a prompt")
    scene = os.path.join(base, rk, "scene.png")
    if not os.path.isfile(scene):
        raise ValueError("room %s has no committed scene.png (commit the room first)" % rk)
    out = {"type": typ, "room": rk, "hotspot": hid, "box": box, "prompt": prompt, "scene": scene}
    if typ == "cinemagraph":
        fname = "cine_%s.mp4" % (_batch_safe(hid) or "hs")
        out.update(out=os.path.join(base, rk, fname), video_rel="%s/%s" % (rk, fname),
                   loop=(job.get("loop") if job.get("loop") in ("boomerang", "crossfade") else "boomerang"),
                   candidates=max(1, int(job.get("candidates", CINE_CANDIDATES) or CINE_CANDIDATES)))
    elif typ == "door":
        fname = "door_%s_open.png" % (_batch_safe(hid) or "hs")
        out.update(out=os.path.join(base, rk, fname), rel="%s/%s" % (rk, fname))
    else:  # variant
        state = (job.get("state") or "").strip()
        if not state:
            raise ValueError("variant job needs a state")
        fname = "var_%s_%s.png" % (_batch_safe(hid) or "obj", _batch_safe(state) or "state")
        out.update(out=os.path.join(base, rk, fname), rel="%s/%s" % (rk, fname), state=state)
        if job.get("when") is not None:
            out["when"] = job["when"]
    return out


def _launch_batch(base):
    """Expand the queue → run file, seed the status file (so a poll right after launch shows 'running' and
    the single-shot guard trips at once), consume the queue, and launch cinemagraph_batch.py DETACHED.
    Returns the resolved job count. Raises ValueError if any queued job fails to expand."""
    doc = _load_scenario(base)   # snapshot each hotspot's CURRENT box so run-time uses the latest (post-nudge) box
    cur_boxes = {(r.get("key"), h["id"]): h["box"]
                 for r in doc.get("rooms", []) for h in (r.get("hotspots") or [])
                 if h.get("id") and isinstance(h.get("box"), list) and len(h["box"]) == 4}
    resolved = [_expand_job(base, j, cur_boxes) for j in _batch_read_queue(base)]
    with open(_batch_run_path(base), "w", encoding="utf-8") as f:
        json.dump({"jobs": resolved}, f, indent=2, ensure_ascii=False)
    with open(_batch_status_path(base), "w", encoding="utf-8") as f:
        json.dump({"state": "running", "total": len(resolved), "done": 0, "current": None, "results": [],
                   "started": time.strftime("%H:%M:%S"), "finished": None}, f)
    logf = open(os.path.join(_batch_dir(base), "cine_batch.log"), "a")
    subprocess.Popen(
        [CINE_VENV, BATCH_GEN, "--run", _batch_run_path(base),
         "--scenario", os.path.join(base, "scenario.json"), "--gen", GEN,
         "--status", _batch_status_path(base)],
        stdout=logf, stderr=logf, start_new_session=True)
    _batch_write_queue(base, [])   # queue consumed into the run
    return len(resolved)


# --- Scene spec (automated art pipeline, Phase 1) ----------------------------------------------------------
# One structured spec per room -> the gpt-image prompt + the cinemagraph batch jobs + the hotspot stubs all
# derive from it (see authoring_v2/scene_spec.py + notes/art_pipeline.md). These endpoints expose the
# derivations so BOTH the harness UI and a future "build world" orchestrator call the same code.

def _spec_derivations(spec):
    return {"prompt": scene_spec.render_prompt(spec),
            "cinemagraphs": scene_spec.cinemagraph_jobs(spec),
            "hotspots": scene_spec.to_hotspots(spec)}


def _save_scene_spec(base, room_key, spec):
    """Store the scene spec on the node's `authoring`, and render its prompt into `authoring.scenePrompt`
    (which the generator already reads) — so the manual prompt field stays the single source gen uses; the
    spec just fills it. Returns the rendered prompt."""
    prompt = scene_spec.render_prompt(spec)
    with SAVE_LOCK:
        doc = _load_scenario(base)
        node = next((r for r in doc.get("rooms", []) if r.get("key") == room_key), None)
        if not node:
            raise ValueError("no room %s" % room_key)
        auth = node.setdefault("authoring", {})
        auth["sceneSpec"] = spec
        auth["scenePrompt"] = prompt
        _save_scenario(doc, base)
    return prompt


def _save_scene_specs(base, specs):
    """Bulk store many rooms' scene specs + render each prompt in ONE load-modify-save. `specs` is
    {roomKey: spec}. The spec-author (Claude) drafts a whole scenario at once; this loads them all. Returns
    {roomKey: {prompt, cinemagraphs} | {error}}."""
    out = {}
    with SAVE_LOCK:
        doc = _load_scenario(base)
        nodes = {r.get("key"): r for r in doc.get("rooms", [])}
        for rk, spec in (specs or {}).items():
            if rk == "worldPlate":   # scenario-level world-plate prompt lives in the spec bundle (single source), not a room
                if isinstance(spec, str) and spec.strip():
                    doc["worldPlatePrompt"] = spec; out[rk] = {"prompt": spec}
                else:
                    out[rk] = {"error": "worldPlate must be a non-empty prompt string"}
                continue
            if rk == "cover":        # scenario-level cover + landing: {prompt, title, subtitle, ambient} -> scenario.json
                if isinstance(spec, dict):
                    if "prompt" in spec:   doc["coverPrompt"] = spec.get("prompt") or ""
                    if "title" in spec:    doc["title"] = spec.get("title") or ""
                    if "subtitle" in spec: doc["subtitle"] = spec.get("subtitle") or ""
                    if "ambient" in spec:  doc["ambient"] = spec.get("ambient") or ""
                    out[rk] = {"ok": True}
                else:
                    out[rk] = {"error": "cover must be an object {prompt, title, subtitle, ambient}"}
                continue
            if rk == "story":        # scenario narrative: opening + enter button + per-room entry cards + finishes
                if isinstance(spec, dict):
                    if "opening" in spec:    doc["story"] = spec.get("opening") or ""
                    if "enterLabel" in spec: doc["enterLabel"] = spec.get("enterLabel") or ""
                    af = spec.get("analysisFinish")
                    if isinstance(af, dict): doc["done"] = {"title": af.get("title", ""), "body": af.get("body", "")}
                    ef = spec.get("escapeFinish")
                    if isinstance(ef, dict): doc["escapeDone"] = {"title": ef.get("title", ""), "body": ef.get("body", "")}
                    for erk, card in (spec.get("entries") or {}).items():
                        enode = nodes.get(re.sub(r"[^A-Za-z0-9_]", "", str(erk or "")))
                        if enode is not None and isinstance(card, dict):
                            enode["entry"] = {"title": card.get("title", ""), "text": card.get("text", "")}
                    out[rk] = {"ok": True}
                else:
                    out[rk] = {"error": "story must be an object"}
                continue
            node = nodes.get(re.sub(r"[^A-Za-z0-9_]", "", str(rk or "")))
            if not node or not isinstance(spec, dict):
                out[rk] = {"error": "no room %s or spec not an object" % rk}; continue
            try:
                prompt = scene_spec.render_prompt(spec)
            except Exception as e:  # noqa: BLE001
                out[rk] = {"error": "bad spec: %s" % e}; continue
            auth = node.setdefault("authoring", {})
            auth["sceneSpec"] = spec
            auth["scenePrompt"] = prompt
            out[rk] = {"prompt": prompt, "cinemagraphs": scene_spec.cinemagraph_jobs(spec)}
        _save_scenario(doc, base)
    return out


def _apply_spec_all(base):
    """Run _apply_spec for every room that has a stored sceneSpec (materialize hotspots + queue cinemagraphs
    across the whole scenario). Returns {roomKey: result | {error}}."""
    rooms = [r.get("key") for r in _load_scenario(base).get("rooms", [])
             if (r.get("authoring") or {}).get("sceneSpec")]
    res = {}
    for rk in rooms:
        try:
            res[rk] = _apply_spec(base, rk)
        except ValueError as e:
            res[rk] = {"error": str(e)}
    return res


_REVIEW_FLAGS = {"hotspotsReviewed", "cinemagraphsVerified"}


def _set_review_flag(base, room_key, field, value):
    """Set a per-room review flag on the node's `authoring` — `hotspotsReviewed` (placements fine-tuned) or
    `cinemagraphsVerified` (cinemagraphs looked over). Drives the build-world Rooms table's ✓ columns so you
    can see which rooms you've been through. Whitelisted field only."""
    if field not in _REVIEW_FLAGS:
        raise ValueError("unknown review flag %r" % field)
    with SAVE_LOCK:
        doc = _load_scenario(base)
        node = next((r for r in doc.get("rooms", []) if r.get("key") == room_key), None)
        if not node:
            raise ValueError("no room %s" % room_key)
        node.setdefault("authoring", {})[field] = bool(value)
        _save_scenario(doc, base)
    return {"room": room_key, "field": field, "value": bool(value)}


def _scenario_state(base):
    """Per-room pipeline status for the build-world console: spec loaded? art built? hotspots placed?
    cinemagraphs done vs candidates awaiting a pick? Plus the batch status + queue depth."""
    doc = _load_scenario(base)
    rooms = []
    for r in doc.get("rooms", []):
        auth = r.get("authoring") or {}
        spec = auth.get("sceneSpec")
        hs = r.get("hotspots") or []
        planned = scene_spec.to_hotspots(spec) if spec else []   # {id,type,label,direction?,to?} from the spec
        boxes = scene_spec.approx_boxes(spec) if spec else {}     # for the minimap: each element's 360 x-position
        def _xc(pid):
            b = boxes.get(pid)
            return round((b[0] + b[2]) / 2, 4) if b else None    # panorama x-centre (0..1) -> ring angle in the console
        rooms.append({
            "key": r.get("key"), "title": r.get("title", ""),
            "hasSpec": bool(spec),
            "scenePrompt": auth.get("scenePrompt", ""),   # for the console's view/edit-prompt button
            "animateCount": len(scene_spec.cinemagraph_jobs(spec)) if spec else 0,
            "doorViewCount": len(scene_spec.dooropen_jobs(spec)) if spec else 0,
            "built": bool(r.get("built") or r.get("panorama")),
            "panoCandidates": _pano_candidates(base, r.get("key")),   # level-1 candidates in _scratch (up to MAX)
            "builtFrom": r.get("builtFrom"),                          # which candidate was committed (flag it live)
            "hotspots": len(hs),
            "entry": r.get("entry") or None,                             # per-room entry card {title,text} (spec story.entries)
            "hotspotsReviewed": bool(auth.get("hotspotsReviewed")),      # you fine-tuned the placements (auto on Save & close; toggleable)
            "cinemagraphsVerified": bool(auth.get("cinemagraphsVerified")),  # you reviewed the cinemagraphs (manual toggle)
            "cinemagraphs": sum(1 for h in hs if h.get("cinemagraph")),
            "doorViews": sum(len(h.get("variants") or []) for h in hs if h.get("type") == "door"),
            "candidatesPending": sum(1 for h in hs if h.get("cinemagraphCandidates")),
            "planned": [{"id": p["id"], "type": p.get("type"), "label": p.get("label"), "x": _xc(p["id"])}
                        for p in planned],
            "doors": [{"to": p.get("to"), "direction": p.get("direction", "forward"),
                       "views": len(p.get("opensOnto") or []),   # >1 = a multi-view door (e.g. monorail switch)
                       "x": _xc(p["id"])}                          # where on the ring this door's port sits
                      for p in planned if p.get("type") == "door"],
        })
    return {"rooms": rooms, "batch": _batch_status(base), "queued": len(_batch_read_queue(base)),
            "worldPlate": bool(_world_plate_abs(base)),          # the shared continuity reference, generated first in step 2
            "worldPlatePrompt": doc.get("worldPlatePrompt", ""),
            "coverPrompt": doc.get("coverPrompt", ""),           # scenario cover + landing (authored in the spec bundle's `cover`)
            "cover": doc.get("cover", ""), "title": doc.get("title", ""),
            "subtitle": doc.get("subtitle", ""), "ambient": doc.get("ambient", ""),
            "openingStory": doc.get("story", ""), "enterLabel": doc.get("enterLabel", ""),   # scenario narrative (spec `story`)
            "analysisFinish": doc.get("done") or None, "escapeFinish": doc.get("escapeDone") or None,
            "status": doc.get("status", "in_development"),       # finish & publish step
            "audited": bool(doc.get("audited")), "published": bool(doc.get("published"))}


def _scene_specs(base):
    """{roomKey: sceneSpec} for every room that has one stored — lets the build-world console repopulate its
    specs textarea from disk after a harness restart (or after an agent edits scenario.json), so the specs
    never have to be re-pasted / re-found."""
    doc = _load_scenario(base)
    out = {r.get("key"): (r.get("authoring") or {}).get("sceneSpec")
           for r in doc.get("rooms", [])
           if (r.get("authoring") or {}).get("sceneSpec")}
    story = {}                        # scenario narrative rides in the bundle so the whole thing is spec-authored
    if doc.get("story"):       story["opening"] = doc["story"]
    if doc.get("enterLabel"):  story["enterLabel"] = doc["enterLabel"]
    if isinstance(doc.get("done"), dict):       story["analysisFinish"] = doc["done"]
    if isinstance(doc.get("escapeDone"), dict): story["escapeFinish"] = doc["escapeDone"]
    entries = {r.get("key"): r["entry"] for r in doc.get("rooms", []) if r.get("entry")}
    if entries: story["entries"] = entries
    if story:
        out = {"story": story, **out}
    cover = {}                        # scenario-level cover + landing ride in the same bundle
    if doc.get("coverPrompt"): cover["prompt"] = doc["coverPrompt"]
    if doc.get("title"):       cover["title"] = doc["title"]
    if doc.get("subtitle"):    cover["subtitle"] = doc["subtitle"]
    if doc.get("ambient"):     cover["ambient"] = doc["ambient"]
    if cover:
        out = {"cover": cover, **out}
    if doc.get("worldPlatePrompt"):   # the world-plate prompt rides in the same bundle (edited in stage 1, single source)
        out = {"worldPlate": doc["worldPlatePrompt"], **out}
    return out


def _apply_spec(base, room_key):
    """Materialize the room's stored sceneSpec: create any MISSING hotspots (ambient/door/puzzle) with
    APPROXIMATE boxes from the layout, and queue a cinemagraph batch job for each animated element that
    doesn't already have a clip. Non-destructive — existing hotspots keep their (possibly hand-tuned) boxes
    and wiring. Returns {created, queued, skipped}. The player nudges the rough boxes in the flat editor,
    then hits Run all. (Auto-localization proved unreliable on stylised panoramas; this is the ROI-honest
    path for low-stakes ambience — the spec still auto-writes the prompt + every motion prompt.)"""
    with SAVE_LOCK:
        doc = _load_scenario(base)
        node = next((r for r in doc.get("rooms", []) if r.get("key") == room_key), None)
        if not node:
            raise ValueError("no room %s" % room_key)
        spec = (node.get("authoring", {}) or {}).get("sceneSpec")
        if not spec:
            raise ValueError("room %s has no scene spec — render one first" % room_key)
        boxes = scene_spec.approx_boxes(spec)
        existing = {h.get("id"): h for h in node.setdefault("hotspots", [])}
        created = []
        for st in scene_spec.to_hotspots(spec):
            hid = st["id"]
            if hid in existing:
                if not (isinstance(existing[hid].get("box"), list) and len(existing[hid]["box"]) == 4) and hid in boxes:
                    existing[hid]["box"] = boxes[hid]   # backfill a box if it somehow has none; keep everything else
                continue
            hs = {"id": hid, "type": st.get("type", "ambient"), "label": st.get("label", hid)}
            if hid in boxes:
                hs["box"] = boxes[hid]
            for k in ("direction", "to"):
                if k in st:
                    hs[k] = st[k]
            node["hotspots"].append(hs); existing[hid] = hs; created.append(hid)
        _save_scenario(doc, base)
        spec_for_queue = spec
    # queue cinemagraphs (separate lock; skip elements that already have a clip or are already queued).
    # Prefer the hotspot's ACTUAL box on the node (a hand-tuned one, or the approx we just wrote) over a
    # freshly-recomputed approx, so an existing well-placed hotspot crops from its real box.
    node2 = next((r for r in _load_scenario(base).get("rooms", []) if r.get("key") == room_key), None)
    have_cine = {h.get("id") for h in node2.get("hotspots", []) if h.get("cinemagraph")}
    node_boxes = {h["id"]: h["box"] for h in node2.get("hotspots", [])
                  if h.get("id") and isinstance(h.get("box"), list) and len(h["box"]) == 4}
    # a door that DECLARES multiple open-views (a monorail car whose world-state switch picks which station
    # it looks out on) needs one masked door-open gen per view, all produced in this art step; each is a
    # state-tagged variant on the door hotspot (box = the door's own box; runtime pick-by-state is later
    # wiring). Skip a view already generated (on the node's variants[]) or already queued.
    have_var = {h.get("id"): {v.get("state") for v in (h.get("variants") or [])}
                for h in node2.get("hotspots", []) if h.get("variants")}
    queued, skipped = [], []
    with BATCH_LOCK:
        jobs = _batch_read_queue(base)
        queued_ids = {j.get("hotspotId") for j in jobs if j.get("type") == "cinemagraph"}
        for j in scene_spec.cinemagraph_jobs(spec_for_queue):
            hid = j["hotspotId"]
            box = node_boxes.get(hid)
            if hid in have_cine or hid in queued_ids or not box:
                skipped.append(hid); continue
            jobs.append({"type": "cinemagraph", "roomKey": room_key, "hotspotId": hid,
                         "box": box, "prompt": j["prompt"], "loop": j.get("loop", "boomerang")})
            queued.append(hid)
        queued_var = {(j.get("hotspotId"), j.get("state")) for j in jobs if j.get("type") == "variant"}
        for j in scene_spec.dooropen_jobs(spec_for_queue):
            hid, state = j["hotspotId"], j["state"]
            box = node_boxes.get(hid)
            if not box or state in have_var.get(hid, set()) or (hid, state) in queued_var:
                skipped.append("%s:%s" % (hid, state)); continue
            vj = {"type": "variant", "roomKey": room_key, "hotspotId": hid,
                  "box": box, "prompt": j["prompt"], "state": state}
            if j.get("when") is not None:
                vj["when"] = j["when"]
            jobs.append(vj); queued.append("%s:%s" % (hid, state))
        _batch_write_queue(base, jobs)
    return {"created": created, "queued": queued, "skipped": skipped}


def _rebuild_inventory():
    """Regenerate rooms/scenario_inventory.json from every scenario.json (scenario_inventory.build_inventory).
    Called by the finish step's 'mark complete in inventory' so a status change shows up in the inventory."""
    import scenario_inventory
    out, dupes = scenario_inventory.build_inventory()
    scenario_inventory.OUT.write_text(json.dumps(out, indent=2))
    return {"scenarios": len(out.get("scenarios", [])), "duplicateIds": dupes, "nextFreeId": out.get("next_free_id")}


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


def _apply_mix(music_volume, room_vols, base=None, solve_vols=None):
    """Volume-ONLY writeback for the test-play sound mixer. `music_volume` (or None) sets the
    scenario-level `musicVolume`; `room_vols` is {roomKey: {src: volume}} setting each matching sfx
    layer's `volume` in place; `solve_vols` is {roomKey: {src: volume}} setting the volume of each
    matching solve / door-open sting (authored as `solveSfx` on a gate hotspot, the room, or the
    scenario, as a bare path string or a {src, volume} object). Deliberately surgical — it reloads
    scenario.json FRESH and touches only the volume field of items matched by src, so it can never
    clobber a layer the harness added/edited between test-play start and save (unlike sending a whole
    stale sfx array back). Every other field (mode/delay/duck/gap/crossfade) and every unmatched
    layer is preserved. A bare-string solveSfx matched by src is promoted to {src, volume}."""
    room_vols = room_vols or {}
    solve_vols = solve_vols or {}
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

        # solve / door stings: match by src within the room's scope (its gate hotspots + the room
        # itself) plus the scenario level — the same resolution order the player uses — and set the
        # volume in place. Only holders that ACTUALLY define that src are touched, so a gate that
        # merely inherits the room/scenario sting is never given a spurious own copy.
        n_solves = 0

        def _set_solve_vol(holder, src, vol):
            nonlocal n_solves
            if not isinstance(holder, dict):
                return
            ss = holder.get("solveSfx")
            cur_src = ss if isinstance(ss, str) else (ss.get("src") if isinstance(ss, dict) else None)
            if not cur_src or cur_src != src:
                return
            if isinstance(ss, dict):
                ss["volume"] = _clamp01(vol)
            else:                                   # promote bare string → {src, volume}
                holder["solveSfx"] = {"src": src, "volume": _clamp01(vol)}
            n_solves += 1

        for key, vols in solve_vols.items():
            if not isinstance(vols, dict):
                continue
            room = rooms.get(key)
            holders = []
            if isinstance(room, dict):
                holders.extend(h for h in (room.get("hotspots") or []) if isinstance(h, dict))
                holders.append(room)
            holders.append(doc)                     # scenario-level fallback sting
            for src, vol in vols.items():
                for h in holders:
                    _set_solve_vol(h, src, vol)

        if touched_music or n_layers or n_solves:
            _save_scenario(doc, base)
    return {"music": touched_music, "layers": n_layers, "solves": n_solves}


# ---- perceived-loudness auto-balance (EBU R128 / LUFS via ffmpeg) --------------------------------
# The LAST sfx step: "make nothing play louder than the music." We measure PERCEIVED loudness (not
# peak) of the music and every effect with ffmpeg's ebur128 scanner — integrated LUFS — then lower any
# effect whose PLAYED loudness would exceed the music's PLAYED loudness. Playing at volume v scales
# amplitude by v, i.e. shifts loudness by 20·log10(v) dB, so for effect E under music M the cap is:
#     v_E ≤ v_music · 10**((LUFS_music − LUFS_E)/20)      (clamped to [0,1], reduce-only — never raised).
# ffmpeg runs as a subprocess (no python audio deps). Integrated LUFS is unreliable on very short
# stings (<~0.4s gating blocks), so those fall back to RMS mean (volumedetect). Both are dBFS-referenced
# so the same volume math applies; the small LUFS-vs-RMS offset is well within what Lucas fine-tunes by
# ear afterwards. Results cached by (path, size, mtime). Used by the CLI (auto_balance.py) and the
# /api/auto-balance endpoint (the test-play mixer's Auto-balance button).

_LOUDNESS_CACHE = {}   # abspath -> (size, mtime, lufs_or_None, rms_or_None)


def _ffmpeg_loudness(path):
    """(integrated LUFS, RMS mean dBFS) for an audio file, each a negative float or None. Cached by
    stat so a re-run (or repeated src) never re-decodes. Returns (None, None) if the file is missing."""
    try:
        st = os.stat(path)
    except OSError:
        return (None, None)
    key = os.path.abspath(path)
    hit = _LOUDNESS_CACHE.get(key)
    if hit and hit[0] == st.st_size and hit[1] == st.st_mtime:
        return (hit[2], hit[3])
    lufs = rms = None
    try:
        # loudnorm's analysis pass prints a JSON block whose `input_i` is the integrated loudness
        # (LUFS). Works cleanly on both long beds and short stings (unlike ebur128's summary, which
        # this ffmpeg build zeroes out on very short input).
        out = subprocess.run(
            ["ffmpeg", "-nostats", "-hide_banner", "-i", path,
             "-af", "loudnorm=print_format=json", "-f", "null", "-"],
            capture_output=True, text=True, timeout=300).stderr
        m = re.search(r'"input_i"\s*:\s*"(-?\d+(?:\.\d+)?|-?inf)"', out)
        if m and m.group(1) not in ("inf", "-inf"):
            v = float(m.group(1))
            if v > -70:                         # near-silent → unmeasurable as LUFS
                lufs = v
    except (subprocess.SubprocessError, OSError, ValueError):
        lufs = None
    if lufs is None:                            # short/quiet file: fall back to RMS mean
        try:
            out = subprocess.run(
                ["ffmpeg", "-nostats", "-hide_banner", "-i", path,
                 "-af", "volumedetect", "-f", "null", "-"],
                capture_output=True, text=True, timeout=120).stderr
            m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", out)
            if m:
                v = float(m.group(1))
                if v > -90:
                    rms = v
        except (subprocess.SubprocessError, OSError, ValueError):
            rms = None
    _LOUDNESS_CACHE[key] = (st.st_size, st.st_mtime, lufs, rms)
    return (lufs, rms)


def _audio_loudness(base, src):
    """Perceived loudness (dB) + which metric, for a scenario-relative audio `src` under `base`.
    Prefers integrated LUFS, falls back to RMS mean; (None, None) if nothing measurable."""
    if not src:
        return (None, None)
    path = os.path.normpath(os.path.join(base or COMMIT_BASE, src))
    lufs, rms = _ffmpeg_loudness(path)
    if lufs is not None:
        return (lufs, "lufs")
    if rms is not None:
        return (rms, "rms")
    return (None, None)


# player defaults when an authored volume is absent (mirror pano-player.js)
_SFX_DEFAULT_VOL = 1.0        # a room sfx layer with no `volume`
_SOLVE_DEFAULT_VOL = 0.9      # playOneShot's fallback for a solve/door sting
_MUSIC_DEFAULT_VOL = 0.1      # SCENARIO.musicVolume default


def _solve_src_vol(holder):
    """(src, current volume) of a holder's `solveSfx` (string | {src, volume}), or (None, None)."""
    ss = holder.get("solveSfx") if isinstance(holder, dict) else None
    if not ss:
        return (None, None)
    if isinstance(ss, str):
        return (ss, _SOLVE_DEFAULT_VOL)
    if isinstance(ss, dict):
        v = ss.get("volume")
        return (ss.get("src"), _clamp01(v) if v is not None else _SOLVE_DEFAULT_VOL)
    return (None, None)


def _apply_balance(base=None, apply=True):
    """Perceived-loudness auto-balance for one scenario. Reads FRESH, measures the music + every
    effect (room `sfx` layers and every `solveSfx` at hotspot/room/scenario level), and lowers each
    effect whose played loudness would exceed the music's played loudness. Reduce-only; a bare-string
    solveSfx that gets lowered is promoted to {src, volume}. `apply=False` computes the plan without
    writing (the mixer's dry-run). Returns a dict with `changes` (lowered), `skipped` (unmeasurable),
    and the music reference; on no measurable music returns `{... "error": ...}` and changes nothing."""
    with SAVE_LOCK:
        doc = _load_scenario(base)
        music_src = doc.get("music")
        mv = doc.get("musicVolume")
        music_vol = _clamp01(mv) if mv is not None else _MUSIC_DEFAULT_VOL
        music_loud, music_metric = _audio_loudness(base, music_src) if music_src else (None, None)
        res = {"music": music_src, "musicVolume": round(music_vol, 3),
               "musicLoudness": round(music_loud, 1) if music_loud is not None else None,
               "musicMetric": music_metric, "applied": bool(apply),
               "changes": [], "skipped": []}
        if not music_src or music_loud is None:
            res["error"] = "no measurable background music to balance against"
            res["nChanged"] = 0
            return res

        music_played = music_loud + 20.0 * math.log10(music_vol) if music_vol > 0 else music_loud - 120.0
        changed = False

        def consider(kind, room_key, src, cur_vol, setter):
            nonlocal changed
            loud, metric = _audio_loudness(base, src)
            if loud is None:
                res["skipped"].append({"kind": kind, "room": room_key, "src": src, "reason": "unmeasurable"})
                return
            # v such that (loud + 20log10 v) ≤ music_played → v ≤ v_music · 10**((L_music − L_E)/20)
            max_v = music_vol * (10.0 ** ((music_loud - loud) / 20.0))
            new_v = max(0.0, min(cur_vol, max_v, 1.0))
            if new_v < cur_vol - 1e-4:
                if apply:
                    setter(new_v)
                changed = True
                res["changes"].append({
                    "kind": kind, "room": room_key, "src": src, "metric": metric,
                    "loudness": round(loud, 1), "oldVolume": round(cur_vol, 3),
                    "newVolume": round(new_v, 3)})

        def solve_setter(holder):
            def setter(v):
                ss = holder.get("solveSfx")
                if isinstance(ss, dict):
                    ss["volume"] = _clamp01(v)
                else:                                   # promote bare string → {src, volume}
                    holder["solveSfx"] = {"src": ss, "volume": _clamp01(v)}
            return setter

        def layer_setter(layer):
            return lambda v: layer.__setitem__("volume", _clamp01(v))

        rooms = [r for r in doc.get("rooms", []) if isinstance(r, dict)]
        for room in rooms:
            rk = room.get("key")
            sfx = room.get("sfx")
            layers = sfx if isinstance(sfx, list) else ([sfx] if isinstance(sfx, dict) else [])
            for layer in layers:
                if not isinstance(layer, dict) or not layer.get("src"):
                    continue
                v = layer.get("volume")
                cur = _clamp01(v) if v is not None else _SFX_DEFAULT_VOL
                consider("layer", rk, layer["src"], cur, layer_setter(layer))
            # solve/door stings that this room (its gate hotspots or the room itself) DEFINES
            for holder in [h for h in (room.get("hotspots") or []) if isinstance(h, dict)] + [room]:
                src, cur = _solve_src_vol(holder)
                if src:
                    consider("solve", rk, src, cur, solve_setter(holder))
        # scenario-level fallback sting
        s_src, s_cur = _solve_src_vol(doc)
        if s_src:
            consider("solve", None, s_src, s_cur, solve_setter(doc))

        if apply and changed:
            _save_scenario(doc, base)
    res["nChanged"] = len(res["changes"])
    return res


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


def _valid_size(size):
    """Validate a WxH string against gpt-image-2 limits (Phase 1 native higher-res).
    Returns (ok, message). Limits: each edge a multiple of 16 and ≤3840, total pixels in
    [655360, 8294400], aspect ratio ≤3:1 either way. Mirrors the UI-side guard in harness_gpt.html."""
    try:
        w, h = (int(x) for x in str(size).lower().split("x"))
    except Exception:
        return False, f"bad size {size!r} (want WxH, e.g. 3072x1024)"
    if w % 16 or h % 16:
        return False, f"{w}x{h}: each edge must be a multiple of 16"
    if w > 3840 or h > 3840:
        return False, f"{w}x{h}: each edge must be ≤3840"
    px = w * h
    if px > 8294400 or px < 655360:
        return False, f"{w}x{h}: total pixels {px} outside 655360–8294400"
    if max(w, h) > 3 * min(w, h):
        return False, f"{w}x{h}: aspect ratio must be ≤3:1"
    return True, ""


def _run_generate(slot, tag, prompt, n, quality, size, ref=None, input_fidelity=None):
    os.makedirs(SCENE, exist_ok=True)
    prefix = f"gpt_{tag}_"
    ptmp = os.path.join(SCENE, f".prompt_{slot}.txt")
    with open(ptmp, "w", encoding="utf-8") as f:
        f.write(prompt)
    # Phase 2 world-plate: when a reference plate is set, gen routes through /images/edits so the
    # scene inherits the plate's backdrop/style (see generate_scene.py cmd_gen --ref).
    ref_args = []
    if ref:
        ref_args += ["--ref", ref]
        if input_fidelity:
            ref_args += ["--input-fidelity", input_fidelity]
    start = _reserve(prefix, n)
    for i in range(n):
        out = os.path.join(SCENE, f"{prefix}{start + i}.png")
        try:
            subprocess.run(["python3", GEN, "gen", "--prompt-file", ptmp,
                            "--out", out, "--quality", quality, "--size", size, *ref_args],
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


def _pano_re(room_key):
    """Matches a level-1 candidate pano basename for a room: l1_<room>.png (legacy, single) or
    l1_<room>_<n>.png (indexed candidate). Excludes _preseam/_seamtmp sibling files."""
    return re.compile(r"^l1_%s(?:_(\d+))?\.png$" % re.escape(room_key))


def _pano_candidates(base, room_key):
    """The room's level-1 candidate panos in _scratch, ordered: indexed l1_<room>_<n>.png by n, then a
    legacy l1_<room>.png (no index) if present. A legacy pano (from before the multi-candidate model) is
    kept visible so an in-flight build isn't orphaned."""
    scratch = os.path.join(base, "_scratch")
    pat = _pano_re(room_key)
    indexed, legacy = [], []
    for p in glob.glob(os.path.join(scratch, "l1_%s*.png" % room_key)):
        name = os.path.basename(p)
        m = pat.match(name)
        if not m:
            continue
        if m.group(1) is None:
            legacy.append(name)
        else:
            indexed.append((int(m.group(1)), name))
    return [n for _i, n in sorted(indexed)] + sorted(legacy)


def _next_pano_idx(base, room_key):
    """Lowest free candidate index in 1..MAX for a room (fills a gap left by a delete), or None if full."""
    scratch = os.path.join(base, "_scratch")
    pat = _pano_re(room_key)
    used = set()
    for p in glob.glob(os.path.join(scratch, "l1_%s_*.png" % room_key)):
        m = pat.match(os.path.basename(p))
        if m and m.group(1):
            used.add(int(m.group(1)))
    for i in range(1, MAX_PANO_CANDIDATES + 1):
        if i not in used:
            return i
    return None


def _run_gen_room_pano(slot, base, room_key, prompt, size, quality, idx):
    """Build-world LEVEL 1: ONE hi-res gpt-image-2 pano candidate for a room, into
    base/_scratch/l1_<room>_<idx>.png (idx = 1..MAX; a room keeps up to MAX candidates to pick between).
    Keyed off an explicit base, so it never touches the server-global active scenario."""
    scratch = os.path.join(base, "_scratch")
    os.makedirs(scratch, exist_ok=True)
    out = os.path.join(scratch, "l1_%s_%d.png" % (room_key, idx))
    ptmp = os.path.join(scratch, ".l1prompt_%s.txt" % room_key)
    with open(ptmp, "w", encoding="utf-8") as f:
        f.write(prompt)
    ref = _world_plate_abs(base)   # world plate = shared continuity reference (via /images/edits). NOTE: gpt-image-2
    ref_args = ["--ref", ref] if ref else []   # rejects `input_fidelity` (gpt-image-1 only) — omit it; the ref rides at the model's default
    try:
        subprocess.run(["python3", GEN, "gen", "--prompt-file", ptmp, "--out", out,
                        "--quality", quality, "--size", size, *ref_args], check=True, capture_output=True, text=True)
        with LOCK:
            JOBS[slot]["outputs"].append(os.path.basename(out)); JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_gen_world_plate(slot, base, prompt, size, quality):
    """Build-world: generate the scenario's WORLD PLATE — one establishing panorama packing the key world
    elements + palette, generated FIRST in step 2. Auto-promoted to <scenario>/_world/plate.png (the canonical
    reference), so every subsequent room Generate carries it (at LOW fidelity — world/palette, not lighting, so
    each room keeps its own time of day). Regenerating replaces the plate."""
    scratch = os.path.join(base, "_scratch")
    os.makedirs(scratch, exist_ok=True)
    out = os.path.join(scratch, "world_plate.png")
    ptmp = os.path.join(scratch, ".worldplate.txt")
    with open(ptmp, "w", encoding="utf-8") as f:
        f.write(prompt)
    try:
        subprocess.run(["python3", GEN, "gen", "--prompt-file", ptmp, "--out", out,
                        "--quality", quality, "--size", size], check=True, capture_output=True, text=True)
        _set_world_plate("world_plate.png", base)   # -> _world/plate.png + records scenario.worldPlate
        with LOCK:
            JOBS[slot]["outputs"].append("world_plate.png"); JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _save_room_pano(base, room_key, image):
    """Build-world LEVEL 1 quick-commit: copy a chosen candidate pano (base/_scratch/l1_<room>[_n].png) to
    the room's committed scene.png and mark the node built with a default full-360 wrap (records `builtFrom`
    so the console can flag which candidate is live). No wrap/hotspot tuning — that's the level-2 hub's
    Commit. Mirrors /api/commit-room minus the draft machinery."""
    img = os.path.basename(str(image or ""))
    if not _pano_re(room_key).match(img):
        raise ValueError("not a candidate pano for %s" % room_key)
    scratch = os.path.join(base, "_scratch")
    if not os.path.isfile(os.path.join(scratch, img)):
        raise ValueError("no such candidate %s — Generate one first" % img)
    room_dir = os.path.relpath(os.path.join(base, room_key), ESCAPE_ROOT)
    written, _rd, seed_wrap = _commit_room(img, room_dir, scene=scratch)
    _commit_node(room_key, written, seed_wrap, base, draft={}, image=img)
    return {"written": written, "builtFrom": img}


def _delete_room_pano(base, room_key, image):
    """Build-world LEVEL 1: delete a candidate pano and its seam siblings (the whole _undoN stack, plus any
    legacy _preseam/_seamtmp) from base/_scratch. Path-confined by the strict candidate-name match."""
    img = os.path.basename(str(image or ""))
    if not _pano_re(room_key).match(img):
        raise ValueError("not a candidate pano for %s" % room_key)
    scratch = os.path.join(base, "_scratch")
    stem = img[:-4]
    removed = []
    for name in [img, stem + "_preseam.png", stem + "_seamtmp.png"] + _seam_snaps(scratch, stem):
        p = os.path.join(scratch, name)
        if os.path.isfile(p):
            os.remove(p)
            removed.append(name)
    return {"removed": removed}


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


def _seamfix_argv(inp, out, left=None, right=None, feather=None, full=False, pos=None):
    """Build the seamfix argv, appending --left/--right (band extent each side of the seam), --feather
    (composite blend radius), --full (use the whole model output, no composite), and --pos (seam location as
    a fraction of width; 1.0 = wrap edge) only when the caller supplied them. Absent, generate_scene falls
    back to a symmetric --width + auto feather + composite mode at the wrap edge. These come from the wrap
    tester's seam band (position + extents), feather slider, and 'blend whole image' toggle."""
    argv = ["python3", GEN, "seamfix", "--input", inp, "--out", out]
    if left:
        argv += ["--left", str(left)]
    if right:
        argv += ["--right", str(right)]
    if feather is not None:                     # 0.0 is meaningful (feather OFF) — pass it, don't treat as falsy
        argv += ["--feather", str(feather)]
    if full:
        argv += ["--full"]
    if pos is not None:
        argv += ["--pos", str(pos)]
    return argv


def _seam_bounds(req):
    """Parse optional seam params (left, right, feather, full) from a request body. left/right/feather are
    fractions of image width. left/right (band extent each side of the seam) clamp to (0, 0.45]; a missing/≤0
    side returns None (fall back to symmetric --width). feather (edge blend radius) clamps to [0, 0.1] and —
    unlike the sides — keeps an EXPLICIT 0 (feather OFF / hard edge); only an absent, unparseable, or negative
    feather returns None (auto = strip/8). full is a bool: use the model's whole output (no composite). pos
    is the seam location as a fraction of width (1.0 = wrap edge; None → default). Returns
    (left, right, feather, full, pos). Guards against a bad drag or a hand-crafted request."""
    def side(k):
        try:
            v = float(req.get(k))
        except (TypeError, ValueError):
            return None
        return max(0.001, min(0.45, v)) if v > 0 else None

    def feather(k):
        v = req.get(k)
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        return None if v < 0 else min(0.1, v)   # ≥0 kept (0 = OFF); <0 → auto

    def posf(k):                            # seam location as a fraction of width; None → default (wrap edge)
        v = req.get(k)
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, v))

    return side("left"), side("right"), feather("feather"), bool(req.get("full")), posf("pos")


_UNDO_RE = re.compile(r"_undo(\d+)\.png$")


def _seam_snaps(dir_, stem):
    """This stem's undo-snapshot filenames in dir_, sorted by index (oldest first). Each snapshot is the
    image state BEFORE one seam-fix stage — the undo STACK that replaced the single _preseam backup, so a
    two-stage fix can undo stage 2 back to the stage-1 result without losing everything."""
    if not os.path.isdir(dir_):
        return []
    pref = stem + "_undo"
    hits = []
    for n in os.listdir(dir_):
        if n.startswith(pref):
            m = _UNDO_RE.search(n)
            if m:
                hits.append((int(m.group(1)), n))
    return [n for _, n in sorted(hits)]


def _seam_push(dir_, stem, img):
    """Snapshot the current image as the next undo slot (called BEFORE a fix overwrites it). Returns depth."""
    d = len(_seam_snaps(dir_, stem))
    shutil.copyfile(img, os.path.join(dir_, "%s_undo%d.png" % (stem, d)))
    return d + 1


def _seam_pop(dir_, stem, img):
    """Undo ONE stage: restore the top snapshot over img and delete it. Raises if empty. Returns new depth."""
    snaps = _seam_snaps(dir_, stem)
    if not snaps:
        raise ValueError("nothing to undo")
    shutil.move(os.path.join(dir_, snaps[-1]), img)
    return len(snaps) - 1


def _seam_depth(dir_, stem):
    return len(_seam_snaps(dir_, stem))


def _run_seamfix(slot, image, left=None, right=None, feather=None, full=False, pos=None):
    """Seam-safe 360 wrap for a _scratch candidate: produces a new <stem>_seam.png candidate whose L/R
    edges meet cleanly (generate_scene.py seamfix). Non-destructive — the original stays; the fixed
    version appears in the grid to pick + commit, exactly like the door-open candidate flow."""
    inp = os.path.join(SCENE, os.path.basename(image))
    stem = os.path.splitext(os.path.basename(image))[0]
    out = os.path.join(SCENE, stem + "_seam.png")
    try:
        subprocess.run(_seamfix_argv(inp, out, left, right, feather, full, pos),
                       check=True, capture_output=True, text=True)
        with LOCK:
            JOBS[slot]["outputs"].append(os.path.basename(out))
            JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_seamfix_scratch(slot, base, image, left=None, right=None, feather=None, full=False, pos=None):
    """Seam-fix a build-world LEVEL-1 pano IN PLACE in <base>/_scratch (generate_scene.py seamfix), pushing the
    pre-fix state onto the <stem>_undoN stack first (per-stage undo). Keyed off an EXPLICIT base — unlike `_run_seamfix`, which
    reads the server-global active scenario (SCENE) — so the console fixes the seam on the scenario it loaded,
    and BEFORE commit ('get the seam right, then commit')."""
    scratch = os.path.join(base, "_scratch")
    img = os.path.join(scratch, os.path.basename(image))
    stem = os.path.splitext(os.path.basename(image))[0]
    tmp = os.path.join(scratch, stem + "_seamtmp.png")
    try:
        if not os.path.isfile(img):
            raise RuntimeError("no scratch pano %s — Generate first" % os.path.basename(image))
        subprocess.run(_seamfix_argv(img, tmp, left, right, feather, full, pos),
                       check=True, capture_output=True, text=True)
        _seam_push(scratch, stem, img)   # push the pre-fix state onto the undo stack (one snapshot per stage)
        shutil.move(tmp, img)
        with LOCK:
            JOBS[slot]["outputs"].append(os.path.basename(img)); JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _undo_seam_scratch(base, image):
    """Undo the most recent scratch seam-fix STAGE: pop the top undo snapshot back over the candidate. Each
    stage pushed one snapshot, so repeated undos step back stage-by-stage (stage 2 → stage-1 result → … →
    original), not all the way at once. Confined to <base>/_scratch; refuses an _undo snapshot as input."""
    scratch = os.path.join(base, "_scratch")
    name = os.path.basename(str(image or ""))
    if not name.endswith(".png"):
        raise ValueError("need image (a _scratch .png)")
    if _UNDO_RE.search(name):
        raise ValueError("that's a snapshot, not a candidate")
    stem = os.path.splitext(name)[0]
    depth = _seam_pop(scratch, stem, os.path.join(scratch, name))
    return {"image": name, "depth": depth}


def _undo_seam_room(base, room_key):
    """Undo the most recent committed-room seam-fix STAGE: pop the top undo snapshot back over scene.png.
    Note: cinemagraph/variant/open-door baked AFTER a fix still reflect the fixed pixels — undo is a scene
    step, best used before those exist."""
    d = os.path.join(base, room_key)
    depth = _seam_pop(d, "scene", os.path.join(d, "scene.png"))
    return {"room": room_key, "depth": depth}


def _run_seamfix_room(slot, base, room_key, left=None, right=None, feather=None, full=False, pos=None):
    """Seam-fix a COMMITTED room IN PLACE: seam-safe the L/R wrap edges of scene.png (generate_scene.py
    seamfix), replacing scene.png (pushes the pre-fix scene onto the `scene_undoN` stack first — per-stage undo).
    The per-candidate `_run_seamfix` makes a new candidate; this is the post-commit repair for the committed scene.
    Interior hotspots (fractional boxes) are unaffected — the seam is at the ±180° edges; regenerate any
    cinemagraph/variant/open-door whose box sits near the seam, so do this BEFORE those scene-baked assets."""
    scene = os.path.join(base, room_key, "scene.png")
    tmp = os.path.join(base, room_key, "scene_seam.png")
    try:
        subprocess.run(_seamfix_argv(scene, tmp, left, right, feather, full, pos),
                       check=True, capture_output=True, text=True)
        _seam_push(os.path.join(base, room_key), "scene", scene)   # push pre-fix scene onto the undo stack
        shutil.move(tmp, scene)
        with LOCK:
            JOBS[slot]["outputs"].append("scene.png (seam-fixed)")
            JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_dooropen_room(slot, base, room_key, box, prompt, hotspot_id=None):
    """Door-open for a COMMITTED room: masked gpt edit of the door box on rooms/<ch>/<sc>/<key>/scene.png.
    PER-DOOR (hotspot_id given): writes `door_<id>_open.png` and sets that door hotspot's `openImage`, so the
    door composites (like a variant) when its own gate is solved — multiple doors can each have their own open
    art. LEGACY (no hotspot_id): writes `scene_open.png` and sets the node's room-level `panoramaOpen`."""
    inp = os.path.join(base, room_key, "scene.png")
    per_door = re.sub(r"[^A-Za-z0-9_]+", "_", str(hotspot_id or "")).strip("_") if hotspot_id else None
    fname = ("door_%s_open.png" % per_door) if per_door else "scene_open.png"
    out = os.path.join(base, room_key, fname)
    rel = "%s/%s" % (room_key, fname)
    boxstr = ",".join(str(x) for x in box)
    try:
        subprocess.run(["python3", GEN, "dooropen", "--input", inp, "--box", boxstr,
                        "--prompt", prompt, "--out", out],
                       check=True, capture_output=True, text=True)
        if per_door:
            with SAVE_LOCK:
                doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
                spot["openImage"] = rel
                _save_scenario(doc, base)
        else:
            _room_patch(room_key, {"panoramaOpen": rel}, base)
        with LOCK:
            JOBS[slot]["outputs"].append(fname)
            JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_variant(slot, base, room_key, hotspot_id, state, box, prompt, when=None):
    """State VARIANT for a COMMITTED room's hotspot (Phase 3 / Option 2): masked gpt edit of the
    hotspot's box on rooms/<ch>/<sc>/<key>/scene.png -> var_<id>_<state>.png, then record it on the
    hotspot's variants[]. Reuses the door-open masked-edit primitive (generate_scene.py dooropen),
    which is already box+prompt-agnostic — only the output filename and the field written differ."""
    inp = os.path.join(base, room_key, "scene.png")
    safe_state = re.sub(r"[^A-Za-z0-9_]+", "_", str(state or "")).strip("_") or "state"
    safe_id = re.sub(r"[^A-Za-z0-9_]+", "_", str(hotspot_id or "")).strip("_") or "obj"
    fname = "var_%s_%s.png" % (safe_id, safe_state)
    out = os.path.join(base, room_key, fname)
    boxstr = ",".join(str(x) for x in box)
    try:
        if not os.path.isfile(inp):
            raise RuntimeError("no committed scene.png for room %s (commit the room first)" % room_key)
        subprocess.run(["python3", GEN, "dooropen", "--input", inp, "--box", boxstr,
                        "--prompt", prompt, "--out", out],
                       check=True, capture_output=True, text=True)
        rel = "%s/%s" % (room_key, fname)
        variant = {"state": safe_state, "box": box, "prompt": prompt, "panorama": rel}
        if when is not None:
            variant["when"] = when
        _add_variant(room_key, hotspot_id, variant, base)
        with LOCK:
            JOBS[slot]["outputs"].append(rel)
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


def _world_plate_abs(base):
    """Absolute path to a scenario's committed world plate (Phase 2), or None if not set/missing.
    The plate is one canonical backdrop image referenced by every room's gen for cross-room
    continuity; it lives at <scenario>/_world/plate.png and is recorded as scenario.worldPlate."""
    p = os.path.join(base, "_world", "plate.png")
    return p if os.path.isfile(p) else None


def _set_world_plate(image, base):
    """Copy a chosen _scratch candidate to <scenario>/_world/plate.png (a stable, pushable name)
    and point `scenario.worldPlate` at it. Mirrors _set_cover: churny candidates stay in
    gitignored _scratch, only the committed plate is a pushable asset. Returns the relative path."""
    name = os.path.basename(str(image or ""))
    if not name:
        raise ValueError("need image")
    src = os.path.join(base, "_scratch", name)
    if not os.path.isfile(src):
        raise ValueError("no such candidate: %s" % name)
    dst_dir = os.path.join(base, "_world")
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copyfile(src, os.path.join(dst_dir, "plate.png"))
    _scenario_patch({"worldPlate": "_world/plate.png"}, base)
    return "_world/plate.png"


def _room_ref_crop(base, room_key):
    """Per-room CONTEXT reference: a crop of the region where THIS room is seen from the room that enters
    it, so a generated interior matches its exterior appearance + scale (the bridge-looks-tiny-outside,
    huge-inside problem). Source box = the room node's `refFrom` {room, box} override if set, else the box
    of the incoming DOOR (a `door` hotspot in another room whose `to == room_key`). Cropped from that source
    room's committed scene.png to _scratch/refcrop_<room>.png; returned as an abs path (used as gen --ref,
    INSTEAD of the world plate). Returns None on any miss → the caller falls back."""
    try:
        from PIL import Image
        doc = _load_scenario(base)
        rooms = doc.get("rooms") or []
        node = next((r for r in rooms if r.get("key") == room_key), None)
        if not node:
            return None
        src_key = box = None
        rf = node.get("refFrom")
        if isinstance(rf, dict) and rf.get("room") and isinstance(rf.get("box"), list) and len(rf["box"]) == 4:
            src_key, box = rf["room"], rf["box"]
        else:
            for r in rooms:                                   # the incoming door: another room's door → here
                for h in (r.get("hotspots") or []):
                    if h.get("type") == "door" and h.get("to") == room_key and isinstance(h.get("box"), list) and len(h["box"]) == 4:
                        src_key, box = r.get("key"), h["box"]
                        break
                if src_key:
                    break
        if not src_key:
            return None
        scene = os.path.join(base, src_key, "scene.png")
        if not os.path.isfile(scene):
            return None
        im = Image.open(scene).convert("RGB"); W, H = im.size
        x0, y0, x1, y1 = box
        crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        os.makedirs(os.path.join(base, "_scratch"), exist_ok=True)
        out = os.path.join(base, "_scratch", "refcrop_%s.png" % re.sub(r"[^A-Za-z0-9_]+", "_", room_key))
        crop.save(out)
        return out
    except Exception:
        return None


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

    def end_headers(self):
        # Dev harness: never let the browser cache the authoring pages/JS/CSS, so edits to
        # harness_gpt.html / puzzle_cards.js / etc. always show on a plain reload (the harness page
        # itself has no ?v cache-buster). `no-cache` still allows a Last-Modified 304 revalidation, so
        # it stays cheap. Applies to every response (static + JSON), which is correct for a dev tool.
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

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
                ok_size, size_err = _valid_size(size)
                if not ok_size:
                    return self._json({"ok": False, "error": size_err}, 400)
                slot = str(req.get("slot", "0"))
                tag = _sanitize_tag(req.get("tag"))
                infid = req.get("inputFidelity") or None
                if infid not in (None, "low", "high"):
                    return self._json({"ok": False, "error": "inputFidelity must be 'low' or 'high'"}, 400)
                ref = None
                if req.get("roomRef"):           # per-room context crop (incoming-door box / marked refFrom) — instead of the plate
                    ref = _room_ref_crop(COMMIT_BASE, slot)
                    if not ref:
                        return self._json({"ok": False, "error": "no room reference — this room needs an incoming door (or a marked refFrom) whose source room has a committed scene"}, 400)
                elif req.get("worldPlate"):        # Phase 2: reference the scenario's world plate
                    ref = _world_plate_abs(COMMIT_BASE)
                    if not ref:
                        return self._json({"ok": False, "error": "no world plate set for this scenario — set one first"}, 400)
                if not _start(slot, "generate",
                              lambda: _run_generate(slot, tag, prompt, n, q, size, ref=ref, input_fidelity=infid),
                              n, tag=tag):
                    return self._json({"ok": False, "error": "this column is already running"}, 409)
                return self._json({"ok": True, "total": n, "slot": slot, "tag": tag, "worldPlate": bool(ref)})
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
            if route == "/api/seamfix":
                req = self._body()
                img = req.get("image")
                if not img:
                    return self._json({"ok": False, "error": "need image"}, 400)
                lf, rf, ff, full, pos = _seam_bounds(req)
                if not _start("seam", "seamfix", lambda: _run_seamfix("seam", img, lf, rf, ff, full, pos), 1):
                    return self._json({"ok": False, "error": "a seamfix job is already running"}, 409)
                return self._json({"ok": True, "slot": "seam"})
            if route == "/api/seamfix-room":        # seam-fix a COMMITTED room's scene.png in place (post-commit)
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                if not os.path.isfile(os.path.join(base, rk, "scene.png")):
                    return self._json({"ok": False, "error": "room %s has no committed scene.png" % rk}, 400)
                lf, rf, ff, full, pos = _seam_bounds(req)
                if not _start("seam", "seamfix", lambda: _run_seamfix_room("seam", base, rk, lf, rf, ff, full, pos), 1):
                    return self._json({"ok": False, "error": "a seamfix job is already running"}, 409)
                return self._json({"ok": True, "slot": "seam"})
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
            if route == "/api/rebuild-inventory":     # regenerate rooms/scenario_inventory.json (finish step)
                try:
                    return self._json({"ok": True, **_rebuild_inventory()})
                except Exception as e:  # noqa: BLE001
                    return self._json({"ok": False, "error": str(e)}, 500)
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
                                         req.get("rooms") or {}, base,
                                         solve_vols=req.get("solves") or {})
                except (ValueError, TypeError) as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **summary})
            if route == "/api/auto-balance":
                # perceived-loudness (LUFS) auto-balance: lower every effect that would play louder
                # than the music. apply=true writes scenario.json (the agent's wire-time pass);
                # apply=false returns the plan only (the mixer's dry-run → applied to sliders).
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    summary = _apply_balance(base, apply=bool(req.get("apply", False)))
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
                hid = str(req.get("hotspotId") or "").strip() or None   # per-door open image (else legacy panoramaOpen)
                if _batch_running(base):
                    return self._json({"ok": False, "error": "a batch is running — wait for it to finish before firing a single gen"}, 409)
                if not _start("door", "dooropen",
                              lambda: _run_dooropen_room("door", base, rk, box, prompt, hid), 1):
                    return self._json({"ok": False, "error": "a door-open job is already running"}, 409)
                return self._json({"ok": True})
            if route == "/api/gen-variant-room":
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                hid = str(req.get("hotspotId") or "").strip()
                state = (req.get("state") or "").strip()
                box = req.get("box")
                prompt = (req.get("prompt") or "").strip()
                if not rk or not hid or not state:
                    return self._json({"ok": False, "error": "need roomKey, hotspotId, state"}, 400)
                if not isinstance(box, list) or len(box) != 4:
                    return self._json({"ok": False, "error": "need box[4]"}, 400)
                if not prompt:
                    return self._json({"ok": False, "error": "empty variant prompt"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                if not os.path.isfile(os.path.join(base, rk, "scene.png")):
                    return self._json({"ok": False, "error": "room %s has no committed scene.png" % rk}, 400)
                when = req.get("when")   # optional trigger condition (condOK shape); stored on the variant
                if _batch_running(base):
                    return self._json({"ok": False, "error": "a batch is running — wait for it to finish before firing a single gen"}, 409)
                if not _start("variant", "variant",
                              lambda: _run_variant("variant", base, rk, hid, state, box, prompt, when), 1):
                    return self._json({"ok": False, "error": "a variant job is already running"}, 409)
                return self._json({"ok": True, "slot": "variant"})
            if route == "/api/patch-variant":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    _update_variant(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                    str(req.get("hotspotId") or "").strip(),
                                    (req.get("state") or "").strip(),
                                    req.get("fields") or {}, base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True})
            if route == "/api/delete-variant":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    _remove_variant(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                    str(req.get("hotspotId") or "").strip(),
                                    (req.get("state") or "").strip(), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True})
            if route == "/api/gen-cinemagraph":
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                hid = str(req.get("hotspotId") or "").strip()
                box = req.get("box")
                prompt = (req.get("prompt") or "").strip()
                if not rk or not hid:
                    return self._json({"ok": False, "error": "need roomKey, hotspotId"}, 400)
                if not isinstance(box, list) or len(box) != 4:
                    return self._json({"ok": False, "error": "need box[4]"}, 400)
                if not prompt:
                    return self._json({"ok": False, "error": "empty motion prompt"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                if not os.path.isfile(os.path.join(base, rk, "scene.png")):
                    return self._json({"ok": False, "error": "room %s has no committed scene.png" % rk}, 400)
                if not os.path.isfile(CINE_GEN):
                    return self._json({"ok": False, "error": "cinemagraph generator not installed (~/ComfyUI/cinemagraph_gen.py)"}, 400)
                if _batch_running(base):
                    return self._json({"ok": False, "error": "a batch is running — wait for it to finish before firing a single gen"}, 409)
                _status_path, vrel = _launch_cinemagraph(base, rk, hid, box, prompt, str(req.get("loop") or "boomerang"))
                return self._json({"ok": True, "state": "started", "video": vrel})
            if route == "/api/cinemagraph-status":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                hid = str(req.get("hotspotId") or "").strip()
                sp = _cine_status_path(base, rk, hid)
                if not os.path.isfile(sp):
                    return self._json({"ok": True, "status": None})
                try:
                    return self._json({"ok": True, "status": json.load(open(sp))})
                except Exception:  # noqa: BLE001
                    return self._json({"ok": True, "status": {"state": "unknown"}})
            if route == "/api/delete-cinemagraph":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    _remove_cinemagraph(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                        str(req.get("hotspotId") or "").strip(), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True})
            if route == "/api/batch-add":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                job = req.get("job") or {}
                try:
                    _expand_job(base, job)   # validate now (type/box/prompt/committed scene) — reject bad jobs at add time
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                minimal = {k: job.get(k) for k in ("type", "roomKey", "hotspotId", "box", "prompt", "loop", "state", "when")
                           if job.get(k) is not None}
                with BATCH_LOCK:
                    jobs = _batch_read_queue(base); jobs.append(minimal); _batch_write_queue(base, jobs)
                    n = len(jobs)
                return self._json({"ok": True, "count": n})
            if route == "/api/batch-list":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "jobs": _batch_read_queue(base),
                                   "running": _batch_running(base), "status": _batch_status(base)})
            if route == "/api/batch-remove":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                idx = req.get("index")
                with BATCH_LOCK:
                    jobs = _batch_read_queue(base)
                    if isinstance(idx, int) and 0 <= idx < len(jobs):
                        jobs.pop(idx)
                    _batch_write_queue(base, jobs); n = len(jobs)
                return self._json({"ok": True, "count": n})
            if route == "/api/batch-clear":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                with BATCH_LOCK:
                    _batch_write_queue(base, [])
                return self._json({"ok": True, "count": 0})
            if route == "/api/batch-run":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                if _batch_running(base):
                    return self._json({"ok": False, "error": "a batch is already running"}, 409)
                if not os.path.isfile(BATCH_GEN):
                    return self._json({"ok": False, "error": "batch runner not installed (~/ComfyUI/cinemagraph_batch.py)"}, 400)
                with BATCH_LOCK:
                    if not _batch_read_queue(base):
                        return self._json({"ok": False, "error": "the batch queue is empty"}, 400)
                    try:
                        total = _launch_batch(base)
                    except ValueError as ve:
                        return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "total": total})
            if route == "/api/batch-status":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "status": _batch_status(base), "running": _batch_running(base)})
            if route == "/api/render-scene-prompt":
                req = self._body()
                spec = req.get("spec")
                if not isinstance(spec, dict):
                    return self._json({"ok": False, "error": "need a spec object"}, 400)
                try:
                    return self._json({"ok": True, **_spec_derivations(spec)})
                except Exception as e:  # noqa: BLE001
                    return self._json({"ok": False, "error": "bad spec: %s" % e}, 400)
            if route == "/api/save-scene-spec":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                spec = req.get("spec")
                if not rk or not isinstance(spec, dict):
                    return self._json({"ok": False, "error": "need roomKey + spec object"}, 400)
                try:
                    prompt = _save_scene_spec(base, rk, spec)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                except Exception as e:  # noqa: BLE001
                    return self._json({"ok": False, "error": "bad spec: %s" % e}, 400)
                return self._json({"ok": True, "prompt": prompt,
                                   "cinemagraphs": scene_spec.cinemagraph_jobs(spec),
                                   "hotspots": scene_spec.to_hotspots(spec)})
            if route == "/api/scenario-state":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **_scenario_state(base)})
            if route == "/api/set-review-flag":       # per-room review checkmark (hotspotsReviewed / cinemagraphsVerified)
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    return self._json({"ok": True, **_set_review_flag(base, rk, req.get("field"), req.get("value"))})
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
            if route == "/api/scene-specs":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "specs": _scene_specs(base)})
            if route == "/api/gen-world-plate":      # build-world: the scenario's shared continuity reference (first in step 2)
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                prompt = (_load_scenario(base).get("worldPlatePrompt") or "").strip()
                if not prompt:
                    return self._json({"ok": False, "error": "no worldPlatePrompt in the spec — add one first"}, 400)
                size = req.get("size", "3072x1024")
                ok_size, size_err = _valid_size(size)
                if not ok_size:
                    return self._json({"ok": False, "error": size_err}, 400)
                if not _start("worldplate", "genplate", lambda: _run_gen_world_plate("worldplate", base, prompt, size, "high"), 1):
                    return self._json({"ok": False, "error": "already generating the world plate"}, 409)
                return self._json({"ok": True, "slot": "worldplate"})
            if route == "/api/gen-room-pano":        # build-world level 1: one hi-res pano for a room
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                node = next((r for r in _load_scenario(base).get("rooms", []) if r.get("key") == rk), None)
                prompt = (((node or {}).get("authoring") or {}).get("scenePrompt") or "").strip()
                if not prompt:
                    return self._json({"ok": False, "error": "room %s has no scenePrompt — render its spec first" % rk}, 400)
                size = req.get("size", "3072x1024")
                ok_size, size_err = _valid_size(size)
                if not ok_size:
                    return self._json({"ok": False, "error": size_err}, 400)
                if len(_pano_candidates(base, rk)) >= MAX_PANO_CANDIDATES:
                    return self._json({"ok": False, "error": "%s already has %d candidate panos — delete one before generating another"
                                       % (rk, MAX_PANO_CANDIDATES)}, 409)
                idx = _next_pano_idx(base, rk)
                if idx is None:
                    return self._json({"ok": False, "error": "%s already has %d candidate panos — delete one first" % (rk, MAX_PANO_CANDIDATES)}, 409)
                slot = "l1_%s_%d" % (rk, idx)
                if not _start(slot, "genpano", lambda: _run_gen_room_pano(slot, base, rk, prompt, size, "high", idx), 1):
                    return self._json({"ok": False, "error": "already generating %s candidate %d" % (rk, idx)}, 409)
                return self._json({"ok": True, "slot": slot, "idx": idx, "image": "l1_%s_%d.png" % (rk, idx)})
            if route == "/api/seamfix-scratch":      # build-world level 1: seam-fix a _scratch pano IN PLACE (pre-commit)
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                image = os.path.basename(str(req.get("image") or ""))
                if not image.endswith(".png"):
                    return self._json({"ok": False, "error": "need image (a _scratch .png)"}, 400)
                lf, rf, ff, full, pos = _seam_bounds(req)
                if not _start("seam", "seamfix", lambda: _run_seamfix_scratch("seam", base, image, lf, rf, ff, full, pos), 1):
                    return self._json({"ok": False, "error": "a seamfix job is already running"}, 409)
                return self._json({"ok": True, "slot": "seam"})
            if route == "/api/seam-undo-scratch":     # build-world level 1: undo the most recent scratch seam-fix STAGE
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    return self._json({"ok": True, **_undo_seam_scratch(base, req.get("image"))})
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
            if route == "/api/seam-undo-room":         # undo the most recent committed-room seam-fix STAGE
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    return self._json({"ok": True, **_undo_seam_room(base, rk)})
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
            if route == "/api/seam-status":            # undo-stack DEPTH for this candidate / committed room (drives per-stage Undo)
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                name = os.path.basename(str(req.get("image") or ""))
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if name.endswith(".png") and not _UNDO_RE.search(name):
                    depth = _seam_depth(os.path.join(base, "_scratch"), os.path.splitext(name)[0])
                elif rk:
                    depth = _seam_depth(os.path.join(base, rk), "scene")
                else:
                    depth = 0
                return self._json({"ok": True, "undoDepth": depth})
            if route == "/api/save-room-pano":       # build-world level 1: quick-commit a chosen candidate pano to the room
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                try:
                    return self._json({"ok": True, **_save_room_pano(base, rk, req.get("image"))})
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
            if route == "/api/delete-room-pano":     # build-world level 1: discard a candidate pano (+ seam siblings)
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                try:
                    return self._json({"ok": True, **_delete_room_pano(base, rk, req.get("image"))})
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
            if route == "/api/save-scene-specs":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                specs = req.get("specs")
                if not isinstance(specs, dict) or not specs:
                    return self._json({"ok": False, "error": "need a {roomKey: spec} object"}, 400)
                return self._json({"ok": True, "rooms": _save_scene_specs(base, specs)})
            if route == "/api/apply-spec-all":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "rooms": _apply_spec_all(base)})
            if route == "/api/apply-spec":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                try:
                    res = _apply_spec(base, rk)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **res})
            if route == "/api/localize-room":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                scene = os.path.join(base, rk, "scene.png")
                if not rk or not os.path.isfile(scene):
                    return self._json({"ok": False, "error": "room %s has no committed scene.png" % rk}, 400)
                node = next((r for r in _load_scenario(base).get("rooms", []) if r.get("key") == rk), None)
                if not node:
                    return self._json({"ok": False, "error": "no room %s" % rk}, 400)
                auth = node.get("authoring", {}) or {}
                spec = auth.get("sceneSpec")
                if spec:   # locate the spec's elements, using its rendered prompt for spatial context
                    targets = [{"id": e["id"], "desc": e.get("desc", e["id"]), "at": e.get("at")}
                               for e in spec.get("elements", []) if e.get("id")]
                    prompt = scene_spec.render_prompt(spec)
                else:      # fall back to the room's existing hotspots + stored prompt
                    targets = [{"id": h["id"], "desc": h.get("label", h["id"]), "at": None}
                               for h in node.get("hotspots", []) if h.get("id")]
                    prompt = auth.get("scenePrompt", "")
                if not targets:
                    return self._json({"ok": False, "error": "no scene spec or hotspots to localize"}, 400)
                try:
                    boxes = localizer.localize(scene, targets, prompt,
                                               engine=str(req.get("engine") or "gdino"))
                except Exception as e:  # noqa: BLE001
                    return self._json({"ok": False, "error": "localize failed: %s" % e}, 502)
                return self._json({"ok": True, "boxes": boxes})
            if route == "/api/pick-cinemagraph":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    cine = _pick_cinemagraph(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                             str(req.get("hotspotId") or "").strip(),
                                             int(req.get("index")), base)
                except (ValueError, TypeError) as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "cinemagraph": cine})
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
            if route == "/api/set-world-plate":
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    plate = _set_world_plate(req.get("image"), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "worldPlate": plate})
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
