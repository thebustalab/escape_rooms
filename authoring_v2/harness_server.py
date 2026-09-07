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
import datetime
import json
import glob
import math
import shutil
import sys
import time
import threading
import subprocess
import scene_spec   # the scene-spec model: render_prompt / cinemagraph_jobs / to_hotspots (art-pipeline P1)
import scene_states  # (room, state) -> panorama; the ONE resolver for which art a world state uses
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
MAX_PLATE_CANDIDATES = 8   # world-plate candidates per generate call (the plate fixes every room's look — worth choosing)
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
# Raised 5 -> 8 (2026-08-28). At the new ladder top (512) a clip renders in ~11 s, and seed-to-seed
# variation was measured as large as resolution's effect — live motion ran 8-27% across seeds at one
# resolution — so candidates, not pixels, are what buy a usable clip. Best-of-8 costs ~90 s.
CINE_CANDIDATES = 8

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
    """Add/MERGE a per-hotspot state VARIANT (Phase 3) on hotspot `hotspot_id`, keyed by `state`:
    regenerating the same state MERGES the new fields over the existing entry (idempotent for the art
    fields), else it's appended. Writes nested into hotspots[].variants[] (the shallow _room_patch can't
    reach that depth). MERGE, not replace, so a hand-wired SWITCH-DOOR nav variant (`{state, when, to,
    direction}` — the monorail mechanic, no art yet) KEEPS its `to`/`direction`/`when` when the art step
    later paints the door-open reveal in and adds `panorama`/`box`/`prompt` for the SAME state. Order-
    independent: wire nav then generate art, or the reverse (2026-08-05)."""
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
                variants[i] = {**v, **variant}      # merge: new fields overlay; existing nav fields survive
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
    """Hard-remove a hotspot's ACTIVE `cinemagraph` pointer (the ✕ on a standalone active tile). Leaves the
    mp4 on disk and does NOT fold it into the pool — use `_uncommit_cinemagraph` for the ✓-off toggle."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        spot.pop("cinemagraph", None)
        _save_scenario(doc, base)
    return spot


def _uncommit_cinemagraph(room_key, hotspot_id, base=None):
    """Un-DEPLOY the active cinemagraph (the ✓ toggled OFF): the clip stops playing in-game but stays STORED
    in the pool. If the active clip isn't already a pool candidate (a legacy single-committed clip, whose pool
    the old pick deleted, or a fresh single-shot gen), fold it into the pool FIRST — so un-checking never
    loses a clip (2026-08-06 bugfix: it used to vanish)."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        active = spot.get("cinemagraph")
        if isinstance(active, dict) and active.get("video"):
            cands = spot.setdefault("cinemagraphCandidates", [])
            if not any(c.get("video") == active.get("video") for c in cands):
                cands.append({"video": active["video"], "seed": active.get("seed"),
                              "prompt": active.get("prompt", ""), "loop": active.get("loop", "boomerang"),
                              "box": active.get("box")})
        spot.pop("cinemagraph", None)
        _save_scenario(doc, base)
    return spot


def _pick_cinemagraph(room_key, hotspot_id, index, base=None):
    """Mark candidate `index` (from `cinemagraphCandidates`) as the ACTIVE cinemagraph (a copy → the
    hotspot's `cinemagraph`, which is the only thing the player reads). KEEPS the candidate pool so the
    choice is a toggle — a stored clip can be made live or un-made live without losing the others
    (store-but-don't-deploy). Un-committing is `_remove_cinemagraph` (drops `cinemagraph`, keeps the pool).
    Returns the chosen cinemagraph."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        cands = spot.get("cinemagraphCandidates") or []
        if not (0 <= index < len(cands)):
            raise ValueError("no candidate %s (have %d)" % (index, len(cands)))
        c = cands[index]
        spot["cinemagraph"] = {"box": c.get("box"), "video": c["video"], "prompt": c.get("prompt", ""),
                               "loop": c.get("loop", "boomerang"), "seed": c.get("seed")}
        _save_scenario(doc, base)   # candidates KEPT (was cleared here pre-2026-08-06)
    return spot["cinemagraph"]


def _delete_cinemagraph_candidate(room_key, hotspot_id, index, base=None):
    """Delete candidate `index` from the pool (the ✕ on a tile). If it was the ACTIVE clip, also drop
    `cinemagraph` so nothing live points at a removed clip. Leaves the mp4 on disk (harmless orphan)."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        cands = spot.get("cinemagraphCandidates") or []
        if not (0 <= index < len(cands)):
            raise ValueError("no candidate %s (have %d)" % (index, len(cands)))
        vid = cands[index].get("video")
        del cands[index]
        if not cands:
            spot.pop("cinemagraphCandidates", None)
        if (spot.get("cinemagraph") or {}).get("video") == vid:
            spot.pop("cinemagraph", None)   # the deleted candidate was the active one
        _save_scenario(doc, base)
    return spot


def _reloop_video_file(base, video_rel, loop):
    """Re-apply the loop (boomerang↔crossfade) to a clip IN PLACE — re-run only the ffmpeg loop, no GPU/model.
    Prefer the kept raw clip (<stem>_raw.mp4, written by render_clip); else derive from the finished clip
    (works, a hair less pristine — the raw is kept for every NEW clip). Overwrites video_rel; the harness UI
    cache-busts video src with ?t so the new loop shows on refresh."""
    if loop not in ("boomerang", "crossfade"):
        raise ValueError("loop must be boomerang|crossfade")
    if not os.path.isfile(CINE_GEN):
        raise ValueError("cinemagraph generator not installed (~/ComfyUI/cinemagraph_gen.py)")
    fin = os.path.join(base, video_rel)
    if not os.path.isfile(fin):
        raise ValueError("clip file missing: %s" % video_rel)
    raw = os.path.splitext(fin)[0] + "_raw.mp4"
    src = raw if os.path.isfile(raw) else fin
    tmp = os.path.splitext(fin)[0] + ".reloop.mp4"
    subprocess.run(["python3", CINE_GEN, "reloop", src, tmp, loop], check=True, capture_output=True, text=True)
    os.replace(tmp, fin)


def _reloop_cinemagraph(room_key, hotspot_id, which, index, loop, base=None):
    """Switch a clip's loop after generation. `which` = "active" (the `cinemagraph`) | "candidate"
    (`cinemagraphCandidates[index]`). Re-loops the file, updates the clip's `loop`, and — when a re-looped
    candidate is also the active clip (same video) — syncs the active `loop` too. Returns {video, loop}."""
    with SAVE_LOCK:
        doc, _node, spot = _find_hotspot(base, room_key, hotspot_id)
        if which == "active":
            clip = spot.get("cinemagraph")
        else:
            cands = spot.get("cinemagraphCandidates") or []
            if not (0 <= index < len(cands)):
                raise ValueError("no candidate %s (have %d)" % (index, len(cands)))
            clip = cands[index]
        if not clip or not clip.get("video"):
            raise ValueError("no clip to re-loop")
        video_rel = clip["video"]
        _reloop_video_file(base, video_rel, loop)       # ffmpeg re-loop in place (single-user harness; brief)
        clip["loop"] = loop
        active = spot.get("cinemagraph")
        if isinstance(active, dict) and active.get("video") == video_rel:
            active["loop"] = loop                        # keep the active clip's loop field in step
        _save_scenario(doc, base)
    return {"video": video_rel, "loop": loop}


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


def _preflight_guard(base):
    """Refuse to spend a generation on a scenario that has not passed the pre-art gate.

    The gate is `authoring_v2/preflight.py`. It stamps `.preflight_ok` with a hash of scenario.json
    (which carries every room's sceneSpec) plus the datasets, so editing either re-arms it. This is
    deliberately a HARD block rather than a warning: the art phase used to sit between two skills
    gated by nothing, which is how twelve unchecked seams once shipped, and how heist nearly
    generated a blown vault door for a crew whose whole signature is that they were let in.

    Escape hatch: PREFLIGHT_OVERRIDE=1 in the server's environment. Overrides are recorded in the
    stamp, so they are never invisible.
    Returns None when clear, or an error string.
    """
    if os.environ.get("PREFLIGHT_OVERRIDE") == "1":
        return None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import preflight
        ok, why = preflight.stamp_is_fresh(base)
        if ok:
            return None
        return ("%s. Run:  python3 authoring_v2/preflight.py <chapter>/<scenario>" % why)
    except Exception as e:                      # never let the guard itself break the harness
        return None


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


def _accept_still(base, room_key, accepted, note="", state=None):
    """Set (or clear) the HUMAN accept on a room's still — `authoring.seam.accepted`.

    This is the one flag no automation may write. `seam_stage.py` records stage/band/ratio/delta/
    needsWork and explicitly refuses to set `accepted` ("a measurement cannot certify"), and
    `stills_iterate`'s verdict vocabulary has no accept value at all. `run_all_tests.py` gates the
    scenario on this field via `seam_check.py --require-accepted`, so it is a safety gate, not
    bookkeeping — and until 2026-09-05 it had NO writer but a text editor, which is why beacons
    carries a hand-typed acceptedBy string.

    Two rules the endpoint enforces rather than trusting the caller with:

    * ACCEPTING A FLAGGED SEAM REQUIRES A NOTE. Lucas's eye outranks the metric in both directions
      — the blur can drive the number to a perfect 0.0 while smearing the picture, and a huge ratio
      on a 2-level step in flat sky is invisible — so overriding `needsWork` is legitimate. But it
      is a judgement call, and the standing rule is to write the trade-off down so the choice is
      visible rather than buried.
    * THE ACCEPT IS STAMPED WITH THE IMAGE IT CERTIFIES. An accept certifies AN IMAGE, not a room.
      Ten of beacons' day scenes once carried a 09-02 accept for a 09-03 image. `at` is compared
      against the file's mtime by `seam_stage.stage_is_stale`, so writing it here makes a later
      regeneration invalidate the accept automatically instead of silently inheriting it.
    """
    fname = "scene.png" if not state else ("scene_%s.png" % re.sub(r"[^a-z0-9_]", "", str(state).lower()))
    img = os.path.join(base, room_key, fname)
    if not os.path.isfile(img):
        raise ValueError("no %s for room %s — nothing to accept" % (fname, room_key))

    with SAVE_LOCK:
        doc = _load_scenario(base)
        node = next((r for r in doc.get("rooms", []) if r.get("key") == room_key), None)
        if not node:
            raise ValueError("no room %s" % room_key)
        seam = node.setdefault("authoring", {}).setdefault("seam", {})
        rec = seam.setdefault("states", {}).setdefault(state, {}) if state else seam

        note = (note or "").strip()
        if accepted and rec.get("needsWork") and not note:
            raise ValueError(
                "%s is flagged needsWork by the seam stage. Accepting it anyway is a judgement "
                "call — pass a note saying why, so the trade-off is written down." % room_key)

        if accepted:
            rec["accepted"] = True
            rec["acceptedBy"] = "lucas %s" % datetime.date.today().isoformat()
            if note:
                rec["humanNote"] = note
        else:
            rec["accepted"] = False
            rec.pop("acceptedBy", None)
        rec["at"] = datetime.datetime.now().isoformat(timespec="seconds")
        _save_scenario(doc, base)

    return {"room": room_key, "state": state, "accepted": bool(accepted),
            "acceptedBy": rec.get("acceptedBy", ""), "humanNote": rec.get("humanNote", ""),
            "overrodeFlag": bool(accepted and rec.get("needsWork"))}


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


def _puzzle_prompt_loc(h):
    """Where a puzzle hotspot's single player-facing prompt lives, as (kind, container, field) — the live
    sub-dict of `h` plus the key holding the text — or (None, None, None) for a bare stub. Get and set both
    go through this so they stay in lockstep on whichever field the puzzle kind uses: MCQ → question.prompt;
    live-R check → check.prompt; pick-a-point / map → their own prompt (older data: instructions)."""
    if not isinstance(h, dict):
        return (None, None, None)
    q = h.get("question")
    if isinstance(q, dict) and isinstance(q.get("prompt"), str):
        return ("mcq", q, "prompt")
    c = h.get("check")
    if isinstance(c, dict) and isinstance(c.get("prompt"), str):
        return ("check", c, "prompt")
    for k in ("pick", "map"):
        o = h.get(k)
        if isinstance(o, dict):
            for fld in ("prompt", "instructions"):
                if isinstance(o.get(fld), str):
                    return (k, o, fld)
    if isinstance(h.get("instructions"), str):
        return ("instructions", h, "instructions")
    return (None, None, None)


def _puzzle_prompt_get(h):
    """(kind, text) of a puzzle hotspot's player-facing prompt, or (None, None) for a bare stub."""
    kind, cont, fld = _puzzle_prompt_loc(h)
    return (kind, cont[fld] if kind else None)


def _puzzle_prompt_set(spot, text):
    """Write `text` back into the exact field _puzzle_prompt_get read from (in-place). Raises for a stub."""
    kind, cont, fld = _puzzle_prompt_loc(spot)
    if kind is None:
        raise ValueError("hotspot has no editable prompt")
    cont[fld] = text if isinstance(text, str) else ""
    return kind


def _room_puzzle_prompts(room):
    """Every editable puzzle prompt in a room, in authoring order, for the story flow. Committed hotspots are
    the live truth; a plannedHotspot is only surfaced when no committed puzzle of the same label(slug) exists
    yet (an unbuilt room). Each item carries (source, index) so the editor can write it straight back."""
    slug = lambda s: re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")
    out, seen = [], set()
    for i, h in enumerate(room.get("hotspots") or []):
        if h.get("type") != "puzzle":
            continue
        kind, text = _puzzle_prompt_get(h)
        if kind is None:
            continue
        out.append({"source": "hotspots", "index": i, "id": h.get("id"),
                    "label": h.get("label") or h.get("id") or "puzzle", "kind": kind, "prompt": text})
        seen.add(slug(h.get("label")))
    for i, h in enumerate(room.get("plannedHotspots") or []):
        if h.get("type") != "puzzle" or slug(h.get("label")) in seen:
            continue
        kind, text = _puzzle_prompt_get(h)
        if kind is None:
            continue
        out.append({"source": "plannedHotspots", "index": i, "id": h.get("id"),
                    "label": h.get("label") or "puzzle", "kind": kind, "prompt": text, "planned": True})
    return out


def _set_puzzle_prompts(base, items):
    """Bulk-write player-facing puzzle prompts (the build-world story flow's Save). `items` is
    [{roomKey, source, index, prompt}] — one load-modify-save so a multi-prompt save is atomic. Returns
    {updated, errors:[{...,error}]}. Locates each hotspot by (source array, index), matching what
    _room_puzzle_prompts emitted."""
    updated, errors = 0, []
    with SAVE_LOCK:
        doc = _load_scenario(base)
        rooms = {r.get("key"): r for r in doc.get("rooms", [])}
        for it in (items or []):
            rk, src, idx = it.get("roomKey"), it.get("source"), it.get("index")
            try:
                if src not in ("hotspots", "plannedHotspots"):
                    raise ValueError("bad source %r" % src)
                node = rooms.get(rk)
                if node is None:
                    raise ValueError("no room %r" % rk)
                arr = node.get(src) or []
                if not isinstance(idx, int) or idx < 0 or idx >= len(arr):
                    raise ValueError("index %r out of range" % idx)
                _puzzle_prompt_set(arr[idx], it.get("prompt"))
                updated += 1
            except Exception as e:  # noqa: BLE001 — collect per-item, keep going
                errors.append({"roomKey": rk, "source": src, "index": idx, "error": str(e)})
        if updated:
            _save_scenario(doc, base)
    return {"updated": updated, "errors": errors}


def _room_locked_messages(room):
    """Every out-of-order / locked navigation message in a room, in authoring order, for the story flow.
    These are the `lockedBody` strings shown when the player clicks a GATED element (a puzzle/door/lock/grid
    carrying `availableWhen`) before its condition is met — e.g. the airship's "too queasy to climb the mast"
    or "the bearing-rings are frozen". Committed hotspots are the live truth; a plannedHotspot is surfaced
    only when no committed gate of the same (type, label-slug) exists yet. Each item carries (source, index)
    so the editor writes it straight back — mirrors _room_puzzle_prompts."""
    slug = lambda s: re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")
    GATED = ("puzzle", "door", "lock", "grid")
    out, seen = [], set()
    for i, h in enumerate(room.get("hotspots") or []):
        if h.get("type") not in GATED or h.get("availableWhen") is None:
            continue
        out.append({"source": "hotspots", "index": i, "id": h.get("id"),
                    "label": h.get("label") or h.get("id") or h.get("type"),
                    "type": h.get("type"), "lockedBody": h.get("lockedBody") or ""})
        seen.add((h.get("type"), slug(h.get("label"))))
    for i, h in enumerate(room.get("plannedHotspots") or []):
        if h.get("type") not in GATED or h.get("availableWhen") is None:
            continue
        if (h.get("type"), slug(h.get("label"))) in seen:
            continue
        out.append({"source": "plannedHotspots", "index": i, "id": h.get("id"),
                    "label": h.get("label") or h.get("type"), "type": h.get("type"),
                    "lockedBody": h.get("lockedBody") or "", "planned": True})
    return out


def _set_locked_messages(base, items):
    """Bulk-write the `lockedBody` navigation messages edited in the build-world story flow. `items` is
    [{roomKey, source, index, lockedBody}] — one load-modify-save so a multi-message save is atomic.
    Locates each hotspot by (source array, index), matching what _room_locked_messages emitted. Mirrors
    _set_puzzle_prompts."""
    updated, errors = 0, []
    with SAVE_LOCK:
        doc = _load_scenario(base)
        rooms = {r.get("key"): r for r in doc.get("rooms", [])}
        for it in (items or []):
            rk, src, idx = it.get("roomKey"), it.get("source"), it.get("index")
            try:
                if src not in ("hotspots", "plannedHotspots"):
                    raise ValueError("bad source %r" % src)
                node = rooms.get(rk)
                if node is None:
                    raise ValueError("no room %r" % rk)
                arr = node.get(src) or []
                if not isinstance(idx, int) or idx < 0 or idx >= len(arr):
                    raise ValueError("index %r out of range" % idx)
                arr[idx]["lockedBody"] = str(it.get("lockedBody") or "")
                updated += 1
            except Exception as e:  # noqa: BLE001 — collect per-item, keep going
                errors.append({"roomKey": rk, "source": src, "index": idx, "error": str(e)})
        if updated:
            _save_scenario(doc, base)
    return {"updated": updated, "errors": errors}


def _room_clues(room):
    """Every clue in a room, in authoring order, for the story flow. A clue hotspot's player-facing text is
    its `body` (HTML). Committed hotspots are the live truth; a plannedHotspot clue is surfaced only when no
    committed clue of the same label(slug) exists yet (an unbuilt room), so its authored body can be written
    on the planned stub and attaches at commit. Each item carries (source, index) so the editor writes it
    straight back — mirrors _room_puzzle_prompts. `note` is a design-only field and is never surfaced here."""
    slug = lambda s: re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")
    out, seen = [], set()
    for i, h in enumerate(room.get("hotspots") or []):
        if h.get("type") != "clue":
            continue
        out.append({"source": "hotspots", "index": i, "id": h.get("id"),
                    "label": h.get("label") or h.get("id") or "clue", "body": h.get("body") or ""})
        seen.add(slug(h.get("label")))
    for i, h in enumerate(room.get("plannedHotspots") or []):
        if h.get("type") != "clue" or slug(h.get("label")) in seen:
            continue
        out.append({"source": "plannedHotspots", "index": i, "id": h.get("id"),
                    "label": h.get("label") or "clue", "body": h.get("body") or "", "planned": True})
    return out


def _set_clues(base, items):
    """Bulk-write the player-facing clue `body` strings edited in the build-world story flow. `items` is
    [{roomKey, source, index, body}] — one load-modify-save so a multi-clue save is atomic. Locates each
    hotspot by (source array, index), matching what _room_clues emitted. Mirrors _set_puzzle_prompts."""
    updated, errors = 0, []
    with SAVE_LOCK:
        doc = _load_scenario(base)
        rooms = {r.get("key"): r for r in doc.get("rooms", [])}
        for it in (items or []):
            rk, src, idx = it.get("roomKey"), it.get("source"), it.get("index")
            try:
                if src not in ("hotspots", "plannedHotspots"):
                    raise ValueError("bad source %r" % src)
                node = rooms.get(rk)
                if node is None:
                    raise ValueError("no room %r" % rk)
                arr = node.get(src) or []
                if not isinstance(idx, int) or idx < 0 or idx >= len(arr):
                    raise ValueError("index %r out of range" % idx)
                if arr[idx].get("type") != "clue":
                    raise ValueError("hotspot %r is not a clue" % idx)
                arr[idx]["body"] = str(it.get("body") or "")
                updated += 1
            except Exception as e:  # noqa: BLE001 — collect per-item, keep going
                errors.append({"roomKey": rk, "source": src, "index": idx, "error": str(e)})
        if updated:
            _save_scenario(doc, base)
    return {"updated": updated, "errors": errors}


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
        _cands = _pano_candidates(base, r.get("key"))
        rooms.append({
            "key": r.get("key"), "title": r.get("title", ""),
            "hasSpec": bool(spec),
            "scenePrompt": auth.get("scenePrompt", ""),   # for the console's view/edit-prompt button
            "animateCount": len(scene_spec.cinemagraph_jobs(spec)) if spec else 0,
            "doorViewCount": len(scene_spec.dooropen_jobs(spec)) if spec else 0,
            "built": bool(r.get("built") or r.get("panorama")),
            "panoCandidates": _cands,                                 # level-1 candidates in _scratch (up to MAX)
            # ...and which of those are NOT the committed scene.png (a regen reuses the filename, so the
            # name alone can't tell you). The gallery shows these as pending art to accept or veto.
            "panoUncommitted": _pano_uncommitted(base, r.get("key"), _cands),
            "clips": _room_clips(base, r.get("key"), doc),            # baked cinemagraphs on disk
            "wrap": r.get("wrap"),                    # so a viewer can frame the room as the player sees it
            "sfx": r.get("sfx"),                      # ambience layers, so a 360 preview can sound like play
            "builtFrom": r.get("builtFrom"),                          # which candidate was committed (flag it live)
            "hotspots": len(hs),
            "entry": r.get("entry") or None,                             # per-room entry card {title,text} (spec story.entries)
            "puzzlePrompts": _room_puzzle_prompts(r),                     # editable puzzle prompts, in order, for the story flow
            "clues": _room_clues(r),                                      # editable clue bodies, in order, for the story flow
            "lockedMessages": _room_locked_messages(r),                   # editable out-of-order/locked nav messages (lockedBody) for the story flow
            "debrief": r.get("debrief") or "",                           # "how this world worked" paragraph for this room
            # The seam stage's verdict AND the human accept, so the stills tab can show both. Without
            # this the gallery could show a seam panel but not whether anyone had signed it off, and
            # `accepted` — which run_all_tests.py gates the whole scenario on — was invisible in every
            # UI and editable only in a text editor.
            "seam": (auth.get("seam") or {}),
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
            "debrief": doc.get("debrief") or None,               # "how this world worked": {title?, intro?} scenario-level
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
    and wiring. Returns {created, queuedCine, queuedVar, skipped} — cinemagraph vs door-open-variant jobs are
    counted separately, and an element that already has a cinemagraph clip OR unpicked candidates is NOT
    re-queued. The player nudges the rough boxes in the flat editor,
    then hits Run all. (These are the spec's LAYOUT guesses — the fallback for a room no localizer has
    run on. They are NOT evidence that localization fails: `localizer.py` + gpt-4o places boxes well
    (grid-on-image + the generation prompt for ordering); Grounding DINO was the engine that collapsed,
    and it was removed 2026-08-31. See AGENTS.md -> *Hotspot placement*. This is the ROI-honest
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
        # ATTACH THE PRE-ART CONTENT (2026-08-07). `_attach_planned_content` used to run only at commit —
        # but the real workflow commits the ART first and places boxes later, so at commit time there were
        # no boxes to attach to and nothing re-ran the attach afterwards. Result: every placed hotspot in
        # Egypt rendered blank while all 22 authored puzzles/clues sat unused on `plannedHotspots`. Running
        # it here too makes placement self-sufficient in either order. It is idempotent and preserves
        # placement (box/id), so re-running Place all hotspots never disturbs tuned boxes.
        node["hotspots"] = _attach_planned_content(node["hotspots"], node.get("plannedHotspots") or [])
        _save_scenario(doc, base)
        spec_for_queue = spec
    # queue cinemagraphs (separate lock; skip elements that already have a clip or are already queued).
    # Prefer the hotspot's ACTUAL box on the node (a hand-tuned one, or the approx we just wrote) over a
    # freshly-recomputed approx, so an existing well-placed hotspot crops from its real box.
    node2 = next((r for r in _load_scenario(base).get("rooms", []) if r.get("key") == room_key), None)
    # Skip an element that ALREADY has cinemagraph art — either an activated clip (`cinemagraph`) OR a pool of
    # candidates awaiting a pick (`cinemagraphCandidates`). A hotspot whose 5 candidates the author left all
    # unpicked (didn't like any) must NOT get a fresh batch — re-generating is a deliberate per-hotspot action
    # in the hub, not a side effect of re-running Place all hotspots.
    have_cine = {h.get("id") for h in node2.get("hotspots", [])
                 if h.get("cinemagraph") or (h.get("cinemagraphCandidates") or [])}
    node_boxes = {h["id"]: h["box"] for h in node2.get("hotspots", [])
                  if h.get("id") and isinstance(h.get("box"), list) and len(h["box"]) == 4}
    # a door that DECLARES multiple open-views (a monorail car whose world-state switch picks which station
    # it looks out on) needs one masked door-open gen per view, all produced in this art step; each is a
    # state-tagged variant on the door hotspot (box = the door's own box; runtime pick-by-state is later
    # wiring). Skip a view whose ART already exists (a variant carrying a `panorama`) or is already queued —
    # NOT merely one whose state is present: a hand-wired SWITCH-DOOR nav variant (`{state, when, to,
    # direction}`, no `panorama` yet) occupies the state but still NEEDS its door-open art generated, which
    # then MERGES onto it (see _add_variant). Filtering on `panorama` keeps it idempotent after generation.
    have_var = {h.get("id"): {v.get("state") for v in (h.get("variants") or []) if v.get("panorama")}
                for h in node2.get("hotspots", []) if h.get("variants")}
    # Cinemagraph jobs and door-open VARIANT jobs are counted separately so the caller can report each
    # accurately (a door-open reveal is a variant, not a cinemagraph — see the build-world status line).
    queued_cine, queued_var, skipped = [], [], []
    with BATCH_LOCK:
        jobs = _batch_read_queue(base)
        # KEY ON (room, hotspot) — the queue spans the WHOLE scenario, and a hotspot id is only unique
        # WITHIN a room. Keyed on the id alone, the first room to queue `valley_view` made every other
        # room's `valley_view` look already-queued, and it was dropped in silence: beacons declared 20
        # cinemagraphs across 12 rooms, and exactly 8 — one per DISTINCT id — reached the queue
        # (2026-09-02). Scenarios whose ids happen to be unique per room never saw it, which is why it
        # survived; a spec generator that reuses element ids across rooms (the natural thing to write,
        # since ids are namespaced by room everywhere else) hits it immediately.
        queued_ids = {(j.get("roomKey"), j.get("hotspotId")) for j in jobs if j.get("type") == "cinemagraph"}
        # BOX CINEMAGRAPHS ARE RETIRED (2026-09-02). Motion is baked over the WHOLE panorama per
        # (room, world-state) by cinemagraph_tools/cine_scenario.py from an authored `motionSpec`, so
        # placing a box job per animated object is work with no consumer. Nothing is queued here any
        # more; `cinemagraph_jobs(spec)` is still read elsewhere as the SOURCE of the motion text, and
        # already-baked clips on existing scenarios keep playing (the runtime reads hotspot.cinemagraph).
        # Door-open and state variants below are unaffected — those are boxed reveals, not motion.
        for j in scene_spec.cinemagraph_jobs(spec_for_queue):
            skipped.append(j["hotspotId"])
        # Same collision, same fix: the variant queue is scenario-wide, so its key needs the room too.
        queued_var_keys = {(j.get("roomKey"), j.get("hotspotId"), j.get("state"))
                           for j in jobs if j.get("type") == "variant"}
        # door open-views (`door.opensOnto`) PLUS any element's general state-variants (`variants:[…]`,
        # e.g. the Pharos lamp with its beam swung onto the ship) — both are state-tagged variant jobs.
        for j in scene_spec.dooropen_jobs(spec_for_queue) + scene_spec.variant_jobs(spec_for_queue):
            hid, state = j["hotspotId"], j["state"]
            box = node_boxes.get(hid)
            if not box or state in have_var.get(hid, set()) or (room_key, hid, state) in queued_var_keys:
                skipped.append("%s:%s" % (hid, state)); continue
            vj = {"type": "variant", "roomKey": room_key, "hotspotId": hid,
                  "box": box, "prompt": j["prompt"], "state": state}
            if j.get("when") is not None:
                vj["when"] = j["when"]
            jobs.append(vj); queued_var.append("%s:%s" % (hid, state))
        _batch_write_queue(base, jobs)
    return {"created": created, "queuedCine": queued_cine, "queuedVar": queued_var, "skipped": skipped}


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


def _iter_sound_slots(doc):
    """Yield (room_key, kind, src, set_flag, get_flag) for EVERY authored sound in a scenario — each room
    `sfx` layer, and every `solveSfx` at hotspot / plannedHotspot / room / scenario level (the same set
    `_apply_balance` measures, including the pre-art planned ones). Used by the test-play mixer's
    "needs replacement" flag, which marks a sound file as no good so it can be re-sourced at the Sounds
    step. Flags key on `src`, so flagging a file marks it EVERYWHERE it is used — a bad recording is bad
    in every room, and that is the behaviour an author expects."""
    def _one_shot_slot(holder, field, rk):
        """A one-shot sound held on `holder[field]` as either a bare src string or {src, volume, …}."""
        ss = holder.get(field)
        src = ss.get("src") if isinstance(ss, dict) else ss
        if not src or not isinstance(src, str):
            return None

        def set_flag(on):
            s = holder.get(field)
            if not isinstance(s, dict):
                s = {"src": s}                       # promote bare string → {src} so the flag has a home
                holder[field] = s
            if on:
                s["needsReplacement"] = True
            else:
                s.pop("needsReplacement", None)

        def get_flag():
            s = holder.get(field)
            return bool(isinstance(s, dict) and s.get("needsReplacement"))
        return (rk, "solve", src, set_flag, get_flag)

    def solve_slot(holder, rk):
        return _one_shot_slot(holder, "solveSfx", rk)

    for room in [r for r in doc.get("rooms", []) if isinstance(r, dict)]:
        rk = room.get("key")
        sfx = room.get("sfx")
        layers = sfx if isinstance(sfx, list) else ([sfx] if isinstance(sfx, dict) else [])
        for layer in layers:
            if not isinstance(layer, dict) or not layer.get("src"):
                continue
            yield (rk, "layer", layer["src"],
                   (lambda l: lambda on: (l.__setitem__("needsReplacement", True) if on
                                          else l.pop("needsReplacement", None)))(layer),
                   (lambda l: lambda: bool(l.get("needsReplacement")))(layer))
        for holder in ([h for h in (room.get("hotspots") or []) if isinstance(h, dict)]
                       + [h for h in (room.get("plannedHotspots") or []) if isinstance(h, dict)]
                       + [room]):
            slot = solve_slot(holder, rk)
            if slot:
                yield slot
            # a DIAL's one-shot lives on `sfx`, not `solveSfx` (the lamp-dial lever throw, the deck
            # cast-off) — an authored sound like any other, so it must be flaggable too. Room-level
            # `sfx` is a LIST of ambience layers and is handled above; only a hotspot's is a one-shot.
            if holder is not room and holder.get("type") == "dial" and holder.get("sfx"):
                slot = _one_shot_slot(holder, "sfx", rk)
                if slot:
                    yield slot
    slot = solve_slot(doc, None)
    if slot:
        yield slot


def _audio_flags(base=None):
    """Every sound currently flagged as needing replacement → {src: True}. Feeds the mixer on open so a
    flag set in an earlier session shows up already lit."""
    doc = _load_scenario(base)
    return {src: True for _rk, _k, src, _s, get in _iter_sound_slots(doc) if get()}


def _apply_audio_flags(base, flags):
    """Set/clear the `needsReplacement` marker on every sound entry whose `src` appears in `flags`
    ({src: bool}). Returns the number of ENTRIES touched (one file used in three rooms counts three)."""
    if not isinstance(flags, dict) or not flags:
        return 0
    n = 0
    with SAVE_LOCK:
        doc = _load_scenario(base)
        for _rk, _kind, src, set_flag, get_flag in _iter_sound_slots(doc):
            if src not in flags:
                continue
            want = bool(flags[src])
            if want != get_flag():
                set_flag(want)
                n += 1
        if n:
            _save_scenario(doc, base)
    return n


def _apply_mix(music_volume, room_vols, base=None, solve_vols=None):
    """Volume-ONLY writeback for the test-play sound mixer. `music_volume` (or None) sets the
    scenario-level `musicVolume`; `room_vols` is {roomKey: {src: volume}} setting each matching sfx
    layer's `volume` in place; `solve_vols` is {roomKey: {src: volume}} setting the volume of each
    matching solve / door-open sting (authored as `solveSfx` on a gate hotspot, the room, or the
    scenario, as a bare path string or a {src, volume} object — or as a dial hotspot's one-shot `sfx`,
    which the mixer lists in the same section). Deliberately surgical — it reloads
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

        def _set_solve_vol(holder, src, vol, allow_sfx=False):
            """Set the volume of whichever field on `holder` carries `src`. `allow_sfx` also considers a
            HOTSPOT's one-shot `sfx` — never a room's, whose `sfx` is the ambience-layer list handled
            above."""
            nonlocal n_solves
            if not isinstance(holder, dict):
                return
            for field in (("solveSfx", "sfx") if allow_sfx else ("solveSfx",)):
                ss = holder.get(field)
                cur_src = ss if isinstance(ss, str) else (ss.get("src") if isinstance(ss, dict) else None)
                if not cur_src or cur_src != src:
                    continue
                if isinstance(ss, dict):
                    ss["volume"] = _clamp01(vol)
                else:                               # promote bare string → {src, volume}
                    holder[field] = {"src": src, "volume": _clamp01(vol)}
                n_solves += 1
                return

        for key, vols in solve_vols.items():
            if not isinstance(vols, dict):
                continue
            room = rooms.get(key)
            # (holder, allow_sfx). A DIAL's one-shot throw lives on the hotspot's `sfx`, not `solveSfx`
            # — pano-player's solveSounds() lists it in the mixer's "Solve / door sounds" section
            # alongside the real stings, but this only ever looked at `solveSfx`, so moving that slider
            # and hitting Save reported "saved ✓ nothing changed" and wrote nothing (2026-08-27, Lucas:
            # Egypt's deck cast-off and Pharos lamp dial). Anything the mixer can SHOW it must be able
            # to SAVE.
            holders = []
            if isinstance(room, dict):
                holders.extend((h, True) for h in (room.get("hotspots") or []) if isinstance(h, dict))
                holders.append((room, False))
            holders.append((doc, False))            # scenario-level fallback sting
            for src, vol in vols.items():
                for h, allow_sfx in holders:
                    _set_solve_vol(h, src, vol, allow_sfx)

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


def _solve_src_vol(holder, field="solveSfx"):
    """(src, current volume) of a holder's one-shot sound (string | {src, volume}), or (None, None).
    `field` is "solveSfx" for a gate's sting, "sfx" for a DIAL's lever throw."""
    ss = holder.get(field) if isinstance(holder, dict) else None
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

        def solve_setter(holder, field="solveSfx"):
            def setter(v):
                ss = holder.get(field)
                if isinstance(ss, dict):
                    ss["volume"] = _clamp01(v)
                else:                                   # promote bare string → {src, volume}
                    holder[field] = {"src": ss, "volume": _clamp01(v)}
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
            # Solve/door stings this room DEFINES — on its committed gate hotspots, on its PRE-ART
            # `plannedHotspots` (content is authored there before any art exists and attaches at commit,
            # so a sting wired pre-art must be balanced too, not silently skipped), or on the room itself.
            for holder in ([h for h in (room.get("hotspots") or []) if isinstance(h, dict)]
                           + [h for h in (room.get("plannedHotspots") or []) if isinstance(h, dict)]
                           + [room]):
                src, cur = _solve_src_vol(holder)
                if src:
                    consider("solve", rk, src, cur, solve_setter(holder))
                # a DIAL's one-shot lives on `sfx` (lever throw, cast-off) — same kind of authored sting,
                # but it sat outside the balance pass entirely until 2026-08-07. Room-level `sfx` is the
                # ambience LIST handled above; only a hotspot's is a one-shot.
                if holder is not room and holder.get("type") == "dial":
                    d_src, d_cur = _solve_src_vol(holder, "sfx")
                    if d_src:
                        consider("solve", rk, d_src, d_cur, solve_setter(holder, "sfx"))
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


# The house wrap (root escape_rooms/AGENTS.md): ALL 57 rooms carrying a wrap use 360/90/120, and only
# vOffset/pitch vary — both -5. This is the fallback a freshly committed room adopts when its candidate
# carried no tuned wrap. It used to be `hfov 110, vOffset 0, pitch 0`, which is not any room's framing and
# had to be hand-patched across nine canyon rooms after a commit seeded it (2026-08-30).
HOUSE_WRAP = {"haov": 360, "vaov": 90, "hfov": 120, "vOffset": -5, "pitch": -5}


def _commit_planned_hotspots(room_key, base):
    """Promote a room's `plannedHotspots` into its live `hotspots`, keeping each planned BOX.

    The pre-existing promotion path is "Place all hotspots", which builds the placed list from the SCENE
    SPEC and gives each one `scene_spec.approx_boxes` — a rough guess. That is the right thing when the
    boxes have never been placed. It is the wrong thing for a scenario whose planned boxes are already
    better than a guess: canyon's 34 were drafted by the localizer and 16 of them hand-corrected, and
    routing them through approx_boxes would throw that placement away. So this promotes the planned
    entries THEMSELVES, box included.

    Content is copied by `_attach_planned_content`, the same function every other commit path uses, so a
    hotspot promoted here is assembled by exactly the same rules as one promoted anywhere else.

    Matching is on (type, slug(label)) — the harness's own planned->placed key, and unique within every
    room in the corpus. A planned entry whose key is ALREADY committed is left alone: the committed
    array is the live truth, and silently rewriting a box someone tuned in the flat editor would be a
    regression disguised as a promotion.

    Returns (created, already, boxless) — three lists of labels, so the caller can say what it did AND
    what it did not do. A boxless entry is never invented a box: it is reported and skipped."""
    with SAVE_LOCK:
        doc = _load_scenario(base)
        node = next((r for r in doc.get("rooms", []) if r.get("key") == room_key), None)
        if not node:
            raise ValueError("no room %s" % room_key)
        planned = [p for p in (node.get("plannedHotspots") or []) if isinstance(p, dict)]
        if not planned:
            raise ValueError("room %s has no plannedHotspots" % room_key)
        placed = node.setdefault("hotspots", [])
        have = {(h.get("type"), _slug(h.get("label"))) for h in placed if isinstance(h, dict)}
        used_ids = {h.get("id") for h in placed if isinstance(h, dict)}
        created, already, boxless = [], [], []
        for p in planned:
            key = (p.get("type"), _slug(p.get("label")))
            if key in have:
                already.append(p.get("label") or key[1]); continue
            box = p.get("box")
            if not (isinstance(box, list) and len(box) == 4):
                boxless.append(p.get("label") or key[1]); continue
            hid = p.get("id") or _slug(p.get("label"))
            base_id, n = hid, 2
            while hid in used_ids:                      # ids must stay unique within the room
                hid = "%s_%d" % (base_id, n); n += 1
            hs = {"id": hid, "type": p.get("type") or "ambient",
                  "label": p.get("label") or hid, "box": [float(v) for v in box]}
            placed.append(hs); used_ids.add(hid); have.add(key)
            created.append(hs["label"])
        # Re-run over the WHOLE array, not just the new entries: it is idempotent, and a re-commit is
        # how re-authored planned content reaches hotspots placed on an earlier pass.
        node["hotspots"] = _attach_planned_content(placed, planned)
        _save_scenario(doc, base)
    return created, already, boxless


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
        fields["wrap"] = seed_wrap or dict(HOUSE_WRAP)
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


def _same_bytes(a, b, chunk=1 << 20):
    """Do two files hold the same bytes? Read them — deliberately NOT `filecmp.cmp`, which caches its
    verdict against an (size, mtime) signature and so can answer "unchanged" for a file that was rewritten
    with same-size content. That is exactly the regeneration case this is used for."""
    with open(a, "rb") as fa, open(b, "rb") as fb:
        while True:
            ba, bb = fa.read(chunk), fb.read(chunk)
            if ba != bb:
                return False
            if not ba:
                return True


CLIP_INTERMEDIATE_SUFFIXES = ("_raw", "_src")   # see _room_clips: siblings, never states


MOTION_MAP_PCT = 99.5      # the percentile of a clip's own variation that is drawn as white
MOTION_MAP_FLOOR = 6.0     # ...but never stretch a nearly-static clip until its noise looks like motion


def _motion_tstd(clip, cache_dir):
    """The clip's per-pixel temporal std, cached as .npy against its mtime.

    Sampling and decoding 16 frames of a 3072x1024 clip is the expensive part; the mask itself is a
    couple of array ops. Caching the tstd is what lets a threshold slider be interactive while still
    running the REAL `mask_from_tstd` rather than a browser approximation of it."""
    import numpy as _np
    sys.path.insert(0, os.path.join(ESCAPE_ROOT, "cinemagraph_tools"))
    from motion_mask import sample_frames  # noqa: WPS433
    os.makedirs(cache_dir, exist_ok=True)
    npy = os.path.join(cache_dir, "%s_%d.npy" % (os.path.basename(clip)[:-4], int(os.path.getmtime(clip))))
    if os.path.isfile(npy):
        return _np.load(npy)
    tstd = sample_frames(clip, n=16).std(axis=0).mean(axis=2)
    _np.save(npy, tstd)
    return tstd


GRID_SCALE = 4          # the (threshold x region) surface is computed at 1/4 linear resolution
GRID_PCTS = list(range(50, 100, 3))                     # p50..p98, the ladder the slider walks
GRID_REGION_POS = list(range(0, 101, 10))               # slider positions; 0 = no cut


def _grid_ppm(pos):
    """Slider position -> region cut in parts-per-million of the frame. Mirrors `regPpm` in the UI.

    Log-mapped on purpose: linear pixels would spend nine tenths of the travel in region sizes nobody
    ever wants. 0 = off, 25 -> 10ppm, 50 -> 100, 75 -> 1000, 100 -> 10000 (1% of the frame)."""
    return 0.0 if pos <= 0 else 10.0 ** (pos / 25.0)


def _mask_grid(tstd, scale=GRID_SCALE):
    """Coverage (fraction of frame that stays VIDEO) over the whole threshold x region plane.

    Structured so the expensive parts are paid once per THRESHOLD, not once per cell: at a given
    percentile the closing and the connected-component labelling are done a single time, and each region
    cut is then a lookup over the component sizes. That is what makes ~190 cells a few seconds instead
    of a few minutes.

    The feather is skipped deliberately — a normalised Gaussian preserves the mean, so it cannot move a
    coverage figure, and it is the slowest step in the chain."""
    import numpy as _np
    from scipy import ndimage as _nd
    H, W = tstd.shape
    h, w = H // scale, W // scale
    ds = tstd[:h * scale, :w * scale].reshape(h, scale, w, scale).mean(axis=(1, 3))
    cr = max(1, int(round(4.0 / scale)))                 # close radius scales with the resolution
    cov = []
    for ppm in [_grid_ppm(p) for p in GRID_REGION_POS]:
        cov.append([0.0] * len(GRID_PCTS))
    for j, pct in enumerate(GRID_PCTS):
        thr = float(_np.percentile(ds, pct))
        b = _nd.binary_closing(ds > thr, structure=_np.ones((cr, cr)))
        lab, n = _nd.label(b)
        sizes = _nd.sum(b, lab, range(1, n + 1)) if n else _np.zeros(0)
        for i, pos in enumerate(GRID_REGION_POS):
            min_px = _grid_ppm(pos) * ds.size / 1e6
            if min_px <= 0 or n == 0:
                keep = b
            else:
                sel = _np.zeros(n + 1, dtype=bool)
                sel[1:] = sizes >= min_px
                keep = sel[lab]
            cov[i][j] = round(float(_nd.binary_fill_holes(keep).mean()), 4)
    return {"pcts": GRID_PCTS, "regionPos": GRID_REGION_POS,
            "regionPpm": [round(_grid_ppm(p), 2) for p in GRID_REGION_POS],
            "cov": cov, "scale": scale, "shape": [H, W],
            "note": "indicative, computed at 1/%d resolution without the feather" % scale}


def _motion_scale_of(png):
    """The auto scale a cached map was drawn at, recovered by re-deriving it is NOT possible from the PNG
    alone — so it is stored in a tiny sidecar next to the map when it is written."""
    side = png + ".scale"
    try:
        return open(side, encoding="utf-8").read().strip()
    except OSError:
        return "auto"


def _render_motion_map(clip, out_png, n=16, scale=None):
    """Per-pixel temporal standard deviation of a clip, as a greyscale PNG: white = moving.

    AUTO-SCALED to the clip's OWN distribution, and that matters more than it sounds. The map was first
    drawn with the sweep tooling's fixed `scale=40` — 40 grey levels of variation renders as white — and
    on these clips that hides nearly everything we work with: the median pixel varies by ~1.5 and the 90th
    percentile by 4-10, which at scale 40 draw as grey 10 and 25-61 out of 255. So a frame that is moving
    all over reads as an almost-empty map, while the clip visibly wiggles outside the few bright patches.
    Lucas spotted exactly that contradiction (2026-08-31) and it is a defect in the MAP, not the clip.

    The liveness thresholds live at 4.5 (dead) and 8.0 (alive), so a map has to make the 4-10 band legible
    or it cannot answer the question it is drawn for. Mapping the clip's own p99.5 to white does that. The
    floor stops a genuinely still clip from being stretched until its compression noise looks alive.

    Returns (path, scale) so the caller can tell the viewer what white means — an unlabelled auto-scaled
    map invites exactly the misreading of comparing two clips whose whites mean different things."""
    import numpy as _np
    from PIL import Image as _Image
    sys.path.insert(0, os.path.join(ESCAPE_ROOT, "cinemagraph_tools"))
    from motion_mask import sample_frames  # noqa: WPS433
    fr = sample_frames(clip, n=n)
    tstd = fr.std(axis=0).mean(axis=2)
    if scale is None:
        scale = max(MOTION_MAP_FLOOR, float(_np.percentile(tstd, MOTION_MAP_PCT)))
    _Image.fromarray((_np.clip(tstd / scale, 0, 1) * 255).astype("uint8"), "L").save(out_png)
    scale = round(float(scale), 2)
    with open(out_png + ".scale", "w", encoding="utf-8") as f:
        f.write(str(scale))
    return out_png, scale


def _state_still_rel(base, room_key, state, doc=None):
    """The panorama a (room, state) is drawn from, relative to the scenario dir, for /sfile.

    Mirrors `cine_scenario.state_still` — the gallery must show the reviewer the SAME image the bake
    composites the clip onto, or the thing being judged is not the thing that ships."""
    if state == "base":
        return "%s/scene.png" % room_key
    try:
        if doc is None:
            doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
        for st in scene_states.scene_states(doc, base):
            if st["room"] == room_key and st["state"] == state and st.get("panorama"):
                return st["panorama"]
    except Exception:  # noqa: BLE001
        pass
    return "%s/scene.png" % room_key


def _room_clips(base, room_key, doc=None):
    """The baked cinemagraphs sitting in a room directory, as {state, file} in state order.

    Named `cine_<state>.mp4` by `cinemagraph_tools/cine_scenario.py` — one per full-scene world state,
    so `cine_base.mp4` is the room's own art animated and `cine_night.mp4` (etc.) would be its variant.
    These are the BAKED merge: the full-frame render with any tile repairs already composited in, which
    is the thing that ships, so it is what the gallery should play. Filesystem-derived on purpose —
    a clip is not wired into scenario.json until someone has looked at it."""
    d = os.path.join(base, room_key)
    out = []
    for f in sorted(glob.glob(os.path.join(d, "cine_*.mp4"))):
        name = os.path.basename(f)
        state = name[len("cine_"):-len(".mp4")]
        # INTERMEDIATES ARE NOT STATES. Two files live beside each clip under the same `cine_` prefix:
        #   `cine_<state>_raw.mp4`  the pre-bake render (loop treatment can change without re-rendering)
        #   `cine_<state>_src.mp4`  the un-patched render (a dropped repair patch rebuilds from it)
        # Both are gitignored and neither is a world state. Listing them showed every room twice, then
        # three times — the same bug twice, which is why it is now a named tuple and a test rather than
        # one more `endswith` bolted on at the point of failure.
        if state.endswith(CLIP_INTERMEDIATE_SUFFIXES):
            continue
        # `cine_<state>.patches.json` records any repair TILE composited into this clip: what was pasted
        # and where. It is written by the pipeline at bake time, and the gallery outlines those regions —
        # a pasted tile is the one part of a clip that can carry its own artefacts, so it is the part you
        # want to be able to find on purpose rather than by chance (Lucas, 2026-08-31).
        patches = []
        pj = os.path.join(d, "cine_%s.patches.json" % state)
        if os.path.isfile(pj):
            try:
                patches = json.load(open(pj, encoding="utf-8"))
            except Exception:  # noqa: BLE001
                patches = []
        # The COMMITTED mask choice, so the gallery's sliders open where the shipped clip actually
        # sits instead of at "no mask". They previously always opened at the off position, which said
        # "all video" about clips that had been baked masked since the day they were rendered.
        mask = {}
        mj = os.path.join(d, "cine_%s.mask.json" % state)
        if os.path.isfile(mj):
            try:
                mask = json.load(open(mj, encoding="utf-8"))
            except Exception:  # noqa: BLE001
                mask = {}
        # THE STILL FOR **THIS** STATE. A variant clip sits over the variant's own panorama, not over
        # `scene.png`: showing the base art underneath a night clip makes the reviewer judge a composite
        # that will never exist. Resolved through `scene_states`, the same way the bake resolves it.
        out.append({"state": state, "file": "%s/%s" % (room_key, name),
                    "patches": patches, "mask": mask,
                    "still": _state_still_rel(base, room_key, state, doc)})
    out.sort(key=lambda c: (c["state"] != "base", c["state"]))   # base first, then variants
    # SERVED — is this clip actually wired for play, or only sitting on disk? Baked-but-unwired is the
    # invisible state that let nine reviewed canyon clips never reach a player (2026-09-01), so it is
    # reported beside every clip rather than being something you have to go and check.
    # Load the doc if the caller did not pass one. Reading `served` off `doc or {}` made this function
    # answer "nothing is served" for every clip whenever it was called without a doc — a silent wrong
    # answer, and the exact shape of the bug it exists to expose.
    try:
        sdoc = doc if doc is not None else _load_scenario(base)
    except Exception:  # noqa: BLE001 — no scenario to read (a clips-only fixture): nothing can be served
        sdoc = {}
    node = next((r for r in ((sdoc or {}).get("rooms") or []) if r.get("key") == room_key), None)
    live = {}
    for h in ((node or {}).get("hotspots") or []):
        c = h.get("cinemagraph") or {}
        if c.get("video") and c.get("box") == [0, 0, 1, 1]:
            live[c.get("state") or "base"] = c["video"]
    for c in out:
        c["served"] = live.get(c["state"]) == c["file"]
    return out


# ---- serving a room's BAKED clips in play --------------------------------------------------------
# `_room_clips` is filesystem-derived on purpose — "a clip is not wired into scenario.json until someone
# has looked at it". That review gate is deliberate and stays. But nothing implemented the step AFTER the
# look, so a reviewed clip never reached the player: canyon had nine baked full-scene clips on disk, none
# referenced anywhere in its scenario, and test play served the stills (Lucas, 2026-09-01).
#
# The engine already has the path. `pano-player.js` gives a cinemagraph whose box is [0,0,1,1] its own
# full-scene branch — drawn straight over the base, no feather (there is no surrounding still to blend
# into) and no per-frame temp canvas. So wiring is a scenario edit, not an engine change.
#
# WHERE THE CLIP HANGS. On a marker-less `ambient` carrier hotspot at [0,0,1,1] — the same trick
# `ensure_variant_carrier` uses for full-scene state variants: `ambient` is filtered out of rendering, so
# the carrier shows no marker and intercepts no clicks. One carrier PER STATE, because a hotspot holds
# exactly one `cinemagraph` and `pickCinemagraphs` selects on `state`.
CLIP_CARRIER_PREFIX = "clip_"


def _clip_carrier_id(state):
    return CLIP_CARRIER_PREFIX + _slug(state)


def _serve_room_clips(room_key, base):
    """Wire every baked clip in a room onto a carrier hotspot so the player actually plays it.

    `cine_base.mp4` carries NO `state` field — `pickCinemagraphs` matches base as absent, and writing
    `state: "base"` would make it match nothing and silently play the still. Any other state is written
    through verbatim.

    Idempotent, and safe to re-run after a re-bake: an existing carrier has its `cinemagraph` refreshed
    rather than being duplicated. Returns (wired, unchanged) — lists of state names."""
    with SAVE_LOCK:
        doc = _load_scenario(base)
        node = next((r for r in doc.get("rooms") or [] if r.get("key") == room_key), None)
        if node is None:
            raise ValueError("no room with key %r" % room_key)
        hs = node.get("hotspots")
        if not isinstance(hs, list):
            raise ValueError("room %r has no hotspots (commit it first)" % room_key)
        clips = _room_clips(base, room_key, doc)
        if not clips:
            raise ValueError("room %r has no baked clips" % room_key)
        wired, unchanged = [], []
        for c in clips:
            state = c["state"]
            cine = {"box": [0, 0, 1, 1], "video": c["file"]}
            if state != "base":
                cine["state"] = state
            cid = _clip_carrier_id(state)
            spot = next((h for h in hs if h.get("id") == cid), None)
            if spot is None:
                spot = {"id": cid, "type": "ambient",
                        "label": "Scene motion (%s)" % state,
                        "box": [0, 0, 1, 1],
                        "note": "Carrier for this room's BAKED full-scene cinemagraph. `ambient` is "
                                "filtered out of rendering, so it shows no marker and intercepts no "
                                "clicks; it exists only to hold the clip. Written by /api/serve-clips."}
                hs.append(spot)
            if spot.get("cinemagraph") == cine:
                unchanged.append(state); continue
            spot["cinemagraph"] = cine
            wired.append(state)
        if wired:
            _save_scenario(doc, base)
    return wired, unchanged


def _scratch_uncommitted(base, cands, committed):
    """Of a list of `_scratch` candidate filenames, the ones that are NOT the file already committed.

    Every commit in this harness is a COPY out of `_scratch` to a stable name (scene.png, cover.png,
    _world/plate.png) that records no back-pointer to its source, and the generators reuse candidate
    filenames across runs — so neither the scenario node nor the filename can answer "is this one
    already the committed art". Compare bytes, cheaply: sizes differ in almost every case, and only a
    size match costs a read.

    `committed` is an absolute path or None (nothing committed → every candidate is pending)."""
    if not committed or not os.path.isfile(committed):
        return list(cands)
    try:
        csz = os.path.getsize(committed)
    except OSError:
        return list(cands)
    out = []
    for f in cands:
        p = os.path.join(base, "_scratch", f)
        try:
            if os.path.getsize(p) != csz or not _same_bytes(p, committed):
                out.append(f)
        except OSError:
            continue                          # candidate vanished mid-listing — not pending
    return out


def _pano_uncommitted(base, room_key, cands):
    """Of a room's _scratch candidates, the ones that are NOT the art currently committed as scene.png.

    `builtFrom` cannot answer this on its own. Single-candidate generation always writes
    `l1_<room>_1.png`, so a REGENERATION reuses the filename of the candidate the room was built from —
    the node still says builtFrom "l1_j_c2_1.png" while that file on disk is now different art nobody has
    looked at yet. Filtering by name would hide exactly the thing that needs reviewing.

    Used by the gallery (build_world_v2.html) to show pending art at full width, base above candidate."""
    return _scratch_uncommitted(base, cands, os.path.join(base, room_key, "scene.png"))


def _cover_candidates(base):
    """The scenario's COVER candidates in _scratch: `gpt_cover_*.png`, newest first.

    `_open`/`_x2` are excluded — those are derived files (an upscale, a variant), not fresh candidates,
    and offering them as choices means committing an upscale as if it were an original. This is the same
    filter the gallery used to apply client-side over /api/scenes; it lives here now so the committed
    cover can be byte-matched out of the list without shipping the bytes to the browser."""
    scratch = os.path.join(base, "_scratch")
    out = []
    for p in glob.glob(os.path.join(scratch, "gpt_cover_*.png")):
        name = os.path.basename(p)
        if "_open" in name or "_x2" in name:
            continue
        out.append((os.path.getmtime(p), name))
    return [n for _m, n in sorted(out, reverse=True)]


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


def _plate_candidates(base):
    """The scenario's world-plate candidates in _scratch: indexed `world_plate_<n>.png` by n, then a
    legacy un-indexed `world_plate.png` if present (from before the multi-candidate model, so an older
    scenario's plate isn't orphaned). Mirrors `_pano_candidates`."""
    scratch = os.path.join(base, "_scratch")
    indexed, legacy = [], []
    for p in glob.glob(os.path.join(scratch, "world_plate*.png")):
        name = os.path.basename(p)
        m = re.match(r"^world_plate_(\d+)\.png$", name)
        if m:
            indexed.append((int(m.group(1)), name))
        elif name == "world_plate.png":
            legacy.append(name)
    return [n for _i, n in sorted(indexed)] + legacy


def _run_gen_world_plate(slot, base, prompt, size, quality, n=1):
    """Build-world: generate N candidate WORLD PLATES — establishing panoramas packing the key world
    elements + palette, generated FIRST in step 2, into <base>/_scratch/world_plate_<n>.png.

    THE PLATE IS NOT AUTO-PROMOTED (changed 2026-08-31, Lucas). It used to generate exactly one and commit
    it straight to _world/plate.png with no choice offered — but the plate is the single most consequential
    image in a scenario: once committed, EVERY room's Generate routes through it as the continuity reference
    (see `_run_gen_room_pano` -> `--ref`), so it fixes the house look for every room at once. Picking that
    from a sample of one was backwards. Now it follows the same generate-N-then-pick contract as clue
    artwork and room panos: candidates land in _scratch, the author picks, and /api/set-world-plate promotes
    the chosen one.

    Nothing breaks while no plate is committed — `_world_plate_abs` returns None and room gen simply runs
    with no reference (`ref_args` is empty), which is the pre-existing fallback."""
    scratch = os.path.join(base, "_scratch")
    os.makedirs(scratch, exist_ok=True)
    ptmp = os.path.join(scratch, ".worldplate.txt")
    with open(ptmp, "w", encoding="utf-8") as f:
        f.write(prompt)
    used = {int(m.group(1)) for m in
            (re.match(r"^world_plate_(\d+)\.png$", f) for f in _plate_candidates(base)) if m}
    nxt = (max(used) + 1) if used else 1
    try:
        for i in range(max(1, int(n))):
            name = "world_plate_%d.png" % (nxt + i)
            subprocess.run(["python3", GEN, "gen", "--prompt-file", ptmp,
                            "--out", os.path.join(scratch, name),
                            "--quality", quality, "--size", size],
                           check=True, capture_output=True, text=True)
            with LOCK:
                JOBS[slot]["outputs"].append(name); JOBS[slot]["done"] += 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_mask_rebuild(slot, base, room, state, pct, enabled, region=0.0):
    """Set a clip's mask threshold (or turn masking off) and REBUILD it, so the file matches the choice.

    The threshold is an authored decision — it decides how much of the shipped frame is generated video
    versus the crisp original still — so it is recorded in `cine_<state>.mask.json` and re-applied by
    every later re-bake instead of quietly reverting to auto."""
    try:
        sj = os.path.join(base, room, "cine_%s.mask.json" % state)
        cfg = {}
        if os.path.isfile(sj):
            try:
                cfg = json.load(open(sj, encoding="utf-8"))
            except Exception:  # noqa: BLE001
                cfg = {}
        cfg["pct"] = pct
        cfg["region"] = float(region)      # ppm of the frame; see auto_mask.drop_small
        cfg["enabled"] = bool(enabled)
        json.dump(cfg, open(sj, "w", encoding="utf-8"), indent=1)
        sys.path.insert(0, os.path.join(ESCAPE_ROOT, "cinemagraph_tools"))
        import cine_scenario as _cs  # noqa: WPS433
        _cs.rebuild_clip(base, room, state, log=lambda m: None)
        with LOCK:
            JOBS[slot]["done"] = 1
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-400:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_patch_rebuild(slot, base, room, state, name, enabled):
    """Flip one repair patch on/off and REBUILD the clip so the file matches the flag.

    A patch is composited into the video, so this cannot be a display toggle: turning it off has to
    produce a new clip built from the unpatched render. The sidecar is written first, then the rebuild
    reads it — so the record and the file can only disagree while the job is mid-flight, never after."""
    try:
        pj = os.path.join(base, room, "cine_%s.patches.json" % state)
        patches = json.load(open(pj, encoding="utf-8")) if os.path.isfile(pj) else []
        hit = False
        for p in patches:
            if p.get("name") == name:
                p["enabled"] = bool(enabled)
                hit = True
        if not hit:
            raise ValueError("no patch %r on %s/%s" % (name, room, state))
        json.dump(patches, open(pj, "w", encoding="utf-8"), indent=1)
        sys.path.insert(0, os.path.join(ESCAPE_ROOT, "cinemagraph_tools"))
        import cine_scenario as _cs  # noqa: WPS433
        _cs.rebuild_clip(base, room, state, log=lambda m: None)
        with LOCK:
            JOBS[slot]["done"] = 1
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-400:]
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


def _seamfix_argv(inp, out, left=None, right=None, feather=None, full=False, pos=None,
                  crop=None, occluder=None, edit_frac=None):
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
    if crop:                                    # CROP-INPAINT: only a band around the seam is sent
        argv += ["--crop", str(crop)]
    if occluder:                                # OCCLUDER: stand an object ON the seam
        argv += ["--occluder", str(occluder)]
    if edit_frac:                               # how much of the crop is editable (middle band)
        argv += ["--edit-frac", str(edit_frac)]
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
        # Cap raised 0.45 -> 0.9 (Lucas, 2026-08-07: "make the area selector able to go everywhere"). The
        # band is a REGION selector for patch/occluder as much as a seam straddle, so a side must be able
        # to reach nearly the whole frame. Still bounded — a side of 1.0+ would wrap past itself.
        try:
            v = float(req.get(k))
        except (TypeError, ValueError):
            return None
        return max(0.001, min(0.9, v)) if v > 0 else None

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


def room_target(base, room_key, file=None):
    """Resolve which PNG in a room dir the seam tools act on: the committed scene, or a state VARIANT.

    Seam repair was scene.png-only, which left the night/weather variants with no way to fix a wrap
    discontinuity the AI edit had introduced — the whole point of the edit route is that it re-lights the
    scene, and it can perfectly well break a seam the base had already repaired (Lucas, 2026-08-13).

    `file` must be a BARE FILENAME inside the room dir (e.g. "scene_night.png"). Anything carrying a path
    separator or a `..` is REFUSED rather than basenamed: silently rewriting "../scene.png" into
    "scene.png" cannot escape the room, but it would quietly seam-fix a different image than the caller
    named, and a seam fix is a destructive in-place edit. Refuse, then re-check the resolved parent as a
    belt-and-braces second gate. Returns (abs_path, undo_stem); the stem keys the per-image undo stack, so
    a variant's undos never collide with the base scene's.
    """
    rd = os.path.join(base, room_key)
    name = str(file or "scene.png") or "scene.png"
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError("seam target must be a bare filename inside the room directory")
    if not name.lower().endswith(".png"):
        raise ValueError("seam target must be a .png")
    if "_undo" in name or name.endswith("_seam.png"):
        raise ValueError("refusing to seam-fix an undo snapshot or a working file")
    p = os.path.abspath(os.path.join(rd, name))
    if os.path.dirname(p) != os.path.abspath(rd):
        raise ValueError("seam target must live in the room directory")
    if not os.path.isfile(p):
        raise ValueError("no such image in room %s: %s" % (room_key, name))
    return p, os.path.splitext(name)[0]


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


# The repair MENU (2026-08-07; trimmed to four 2026-08-07). These are PARALLEL options, not stages: pick
# the cheapest one that works for the scene in front of you. The two `seam_ops` ones are pure pixel work —
# instant, free, and they never re-render your art through the model; the two AI ones confine the model to
# a crop around the seam instead of the whole frame. Every one pushes the SAME undo snapshot, so one Undo
# steps back through whatever mix you tried.
#
# DELIBERATELY NOT OFFERED (Lucas, 2026-08-07) — do not re-add:
#   "crop"  — crop & rescale never actually solved the problem, it just paid ~2% of the scene to hide it.
#   "full"  — whole-scene re-render is an AI image of an AI image; it also pushed a fresh seam to the far
#             meridian, so it traded one seam for another. `seam_ops.crop` and `generate_scene seamfix
#             --full` still exist as library/CLI paths; the harness just won't dispatch to them.
_SEAM_LOCAL_OPS = {"gradient", "roll"}                  # handled in-process by seam_ops (no API, no job)
_SEAM_AI_MODES = {"patch", "occluder"}                  # go through generate_scene seamfix


def _seam_local(path, mode, req):
    """Run a non-AI repair in place, pushing an undo snapshot first. Returns the op's report dict."""
    import seam_ops
    d, base_name = os.path.dirname(path), os.path.basename(path)
    stem = os.path.splitext(base_name)[0]
    tmp = os.path.join(d, stem + "_seamtmp.png")
    kw = {}
    if mode == "gradient":
        kw = {"pos": float(req.get("pos") or 1.0), "span": int(req.get("span") or 64)}
    elif mode == "roll":
        kw = {"window": int(req.get("window") or 33)}
    report = seam_ops.run(mode, path, tmp, **kw)
    _seam_push(d, stem, path)                          # same stack the AI repairs use -> shared Undo
    shutil.move(tmp, path)
    return report


def _seam_measure(path, pos=1.0):
    """How big is the seam, against the scene's own detail? Drives the panel's 'is it worth it' readout."""
    import seam_ops
    return seam_ops.measure(path, pos)


def _run_seamfix(slot, image, left=None, right=None, feather=None, full=False, pos=None):
    """Seam-safe 360 wrap for a _scratch candidate: produces a new <stem>_seam.png candidate whose L/R
    edges meet cleanly (generate_scene.py seamfix). Non-destructive — the original stays; the fixed
    version appears in the grid to pick + commit, exactly like the door-open candidate flow."""
    inp = os.path.join(SCENE, os.path.basename(image))
    stem = os.path.splitext(os.path.basename(image))[0]
    out = os.path.join(SCENE, stem + "_seam.png")
    try:
        # env=gen_env() (2026-09-02): seam repair calls the image API, so it needs OPENAI_API_KEY resolved
        # the same way generation does. It inherited os.environ, which only carries the key when the SERVER
        # itself was started from an interactive shell — exactly the latent failure `gen_env` was written
        # for. It surfaced when the occluder pass was driven from a script instead of the console: every
        # room failed instantly with "OPENAI_API_KEY not set". Same fix on all three seamfix call sites.
        subprocess.run(_seamfix_argv(inp, out, left, right, feather, full, pos),
                       check=True, capture_output=True, text=True, env=gen_env())
        with LOCK:
            JOBS[slot]["outputs"].append(os.path.basename(out))
            JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def _run_seamfix_scratch(slot, base, image, left=None, right=None, feather=None, full=False, pos=None,
                         crop=None, occluder=None, edit_frac=None):
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
        subprocess.run(_seamfix_argv(img, tmp, left, right, feather, full, pos, crop, occluder, edit_frac),
                       check=True, capture_output=True, text=True, env=gen_env())
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


def _undo_seam_room(base, room_key, file=None):
    """Undo the most recent committed-room seam-fix STAGE: pop the top undo snapshot back over the target.
    Note: cinemagraph/variant/open-door baked AFTER a fix still reflect the fixed pixels — undo is a scene
    step, best used before those exist. `file` selects a state VARIANT instead of scene.png; each image
    keeps its OWN undo stack (keyed by stem), so undoing a night fix can never restore a day scene."""
    d = os.path.join(base, room_key)
    target, stem = room_target(base, room_key, file)
    depth = _seam_pop(d, stem, target)
    return {"room": room_key, "file": os.path.basename(target), "depth": depth}


def _run_seamfix_room(slot, base, room_key, left=None, right=None, feather=None, full=False, pos=None,
                      crop=None, occluder=None, edit_frac=None, file=None):
    """Seam-fix a COMMITTED room IN PLACE: seam-safe the L/R wrap edges of scene.png (generate_scene.py
    seamfix), replacing scene.png (pushes the pre-fix scene onto the `scene_undoN` stack first — per-stage undo).
    The per-candidate `_run_seamfix` makes a new candidate; this is the post-commit repair for the committed scene.
    Interior hotspots (fractional boxes) are unaffected — the seam is at the ±180° edges; regenerate any
    cinemagraph/variant/open-door whose box sits near the seam, so do this BEFORE those scene-baked assets."""
    scene, stem = room_target(base, room_key, file)      # scene.png, or a state variant (scene_night.png…)
    tmp = os.path.join(base, room_key, "%s_seam.png" % stem)
    try:
        subprocess.run(_seamfix_argv(scene, tmp, left, right, feather, full, pos, crop, occluder, edit_frac),
                       check=True, capture_output=True, text=True, env=gen_env())
        _seam_push(os.path.join(base, room_key), stem, scene)   # per-image undo stack, keyed by stem
        shutil.move(tmp, scene)
        with LOCK:
            JOBS[slot]["outputs"].append("%s.png (seam-fixed)" % stem)
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


def gen_env():
    """Environment for a generation subprocess, guaranteed to carry OPENAI_API_KEY if it exists at all.

    `~/.bashrc` exports the key BELOW the standard "if not running interactively, return" guard, so it
    reaches an interactive terminal and nothing else. Anything launched by a long-running daemon — the
    observer, a cron job, this server if it was started from a script — inherits an environment without
    it, and the failure is a flat "OPENAI_API_KEY not set" after the user has already walked away.
    (Diagnosed 2026-08-13 when the first observer-fired Egypt night run failed on all six rooms.)

    So resolve it at call time from a login+INTERACTIVE bash — `-i` is the part that reads `~/.bashrc`.
    Runtime environment only, never a file read, and the value is never printed or logged.
    """
    env = os.environ.copy()
    if env.get("OPENAI_API_KEY"):
        return env
    try:
        r = subprocess.run(["bash", "-lic", 'printf %s "${OPENAI_API_KEY:-}"'],
                           capture_output=True, text=True, timeout=20)
        key = (r.stdout or "").strip()
    except Exception:  # noqa: BLE001
        key = ""
    if key:
        env["OPENAI_API_KEY"] = key
    return env


def ensure_variant_carrier(base, room_key, carrier_id, label="Nightfall"):
    """Ensure a room has the marker-less FULL-SCENE variant carrier, and return its id.

    A variant's box defaults to its hotspot's box and `ambient` hotspots are filtered out of rendering,
    so an ambient at [0,0,1,1] swaps the WHOLE panorama on a world-state condition with no engine change
    (see AGENTS.md → *Full-scene state variants*; worked example: wrangling/egypt `quay` → `night_wash`).
    Idempotent — a re-run after a failed generation finds the existing carrier and leaves it alone.
    """
    with SAVE_LOCK:
        doc = _load_scenario(base)
        node = next((r for r in doc.get("rooms") or [] if r.get("key") == room_key), None)
        if node is None:
            raise ValueError("no room with key %r" % room_key)
        hs = node.get("hotspots")
        if not isinstance(hs, list):
            raise ValueError("room %r has no hotspots (commit it first)" % room_key)
        if any(h.get("id") == carrier_id for h in hs):
            return carrier_id
        hs.append({"id": carrier_id, "type": "ambient", "label": label, "box": [0, 0, 1, 1],
                   "note": "Full-scene state variant. `ambient` is filtered out of rendering, so this "
                           "carrier shows no marker and intercepts no clicks; it exists only to hold "
                           "the variant art."})
        _save_scenario(doc, base)
    return carrier_id


def restretch_to(path, size):
    """Stretch an edit reply back to the base panorama's exact size, in place. Returns True if it moved.

    SAFETY NET ONLY as of 2026-09-02 — callers must ASK for the base's native size, and then this is a
    no-op. The old docstring claimed "the image-edit endpoint will not return 3:1 — it hands back
    1536x1024", and the fullscene caller relied on that: it let `--size` default to 1536x1024 and
    stretched the 1.5:1 reply out to 3:1 here. That is a **2x horizontal stretch**, and the premise it
    rested on — that the model lays the scene out inside the squashed frame, so a resize restores it —
    only holds for structure COPIED from the input. Anything the model re-draws it draws at natural
    proportions, and those objects came out twice as wide (egypt's night variants). /images/edits does
    return 3072x1024 when asked; verified against the live API. Skipped when the reply already matches.
    """
    from PIL import Image
    with Image.open(path) as im:
        if im.size == size:
            return False
        im.convert("RGB").resize(size, Image.LANCZOS).save(path)
    return True


def run_fullscene_variant(base, room_key, state, prompt, when=None, carrier=None, label="Nightfall"):
    """FULL-SCENE state variant (the night-arc route) — the whole panorama re-lit, composition held.

    Unlike `_run_variant`, which masks a box and edits inside it, this posts the committed day panorama
    itself to the image-EDIT endpoint with NO mask, so the model sees the whole scene: it holds the
    layout to within a couple of percent AND *adds* light a deterministic grade cannot (a blazing
    lighthouse, lit windows, a moon). Then restretch, ensure the carrier, record the variant.

    ⚠️ It works exactly ONCE. This is an AI edit of an AI image; one pass reads correctly, a second
    compounds the artefacts. Always regenerate FROM `scene.png`, never from a previous variant — which
    is why this function always reads the base scene and never the existing variant file.

    Returns the variant dict that was recorded.
    """
    from PIL import Image
    day = os.path.join(base, room_key, "scene.png")
    if not os.path.isfile(day):
        raise ValueError("room %s has no committed scene.png (commit the room first)" % room_key)
    safe_state = re.sub(r"[^A-Za-z0-9_]+", "_", str(state or "")).strip("_") or "state"
    carrier = re.sub(r"[^A-Za-z0-9_]+", "_", str(carrier or "")).strip("_") or "%s_wash" % safe_state
    rel = "%s/scene_%s.png" % (room_key, safe_state)
    out = os.path.join(base, room_key, "scene_%s.png" % safe_state)
    with Image.open(day) as im:
        target = im.size
    # ASK FOR THE BASE'S NATIVE SIZE (2026-09-02). `generate_scene.py edit` defaults `--size` to
    # 1536x1024 and this call never overrode it, so every night variant was generated at 1.5:1 and then
    # stretched to the 3:1 base by `restretch_to` — a 2x horizontal stretch. Structure the model copied
    # from the input survived it, but anything it RE-DREW came back at natural proportions inside the
    # squashed frame and was left twice as wide (Lucas, on egypt's nights: "stretched weirdly"). Verified
    # 2026-09-02 that /images/edits returns 3072x1024 when asked, so the stretch was never necessary.
    # `restretch_to` stays as a no-op safety net for a reply that ignores the requested size.
    subprocess.run(["python3", GEN, "edit", "--input", day, "--prompt", prompt, "--out", out,
                    "--size", "%dx%d" % target],
                   check=True, capture_output=True, text=True, env=gen_env())
    restretch_to(out, target)
    ensure_variant_carrier(base, room_key, carrier, label)
    variant = {"state": safe_state, "box": [0, 0, 1, 1], "prompt": prompt, "panorama": rel}
    if when is not None:
        variant["when"] = when
    _add_variant(room_key, carrier, variant, base)
    return variant


def _run_fullscene(slot, base, room_key, state, prompt, when=None, carrier=None):
    """Thread body for /api/gen-fullscene-variant — same JOBS/slot contract as _run_variant."""
    try:
        v = run_fullscene_variant(base, room_key, state, prompt, when, carrier)
        with LOCK:
            JOBS[slot]["outputs"].append(v["panorama"])
            JOBS[slot]["done"] = 1
    except subprocess.CalledProcessError as e:
        with LOCK:
            JOBS[slot]["error"] = (e.stderr or e.stdout or str(e)).strip()[-500:]
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[slot]["error"] = str(e)[-500:]
    with LOCK:
        JOBS[slot]["active"] = False


def collect_variants(base):
    """Every state variant in the scenario, flattened for review: which room, which carrier, what art.

    The build_world console had no way to LOOK at a generated variant — the rooms table shows the base
    panorama only, so a night pass could be generated, recorded, and never once seen before a student
    hit it (2026-08-13, Lucas). This backs the console's Environmental-variants gallery.

    TWO sources, because a room's alternate art can arrive by two different routes:
      * hotspot `variants[]` — the generated re-lights and reveals; editable (regenerate / delete).
      * the room-level `panoramaOpen` (scene_open.png) — the door-open partner COMMITTED ALONGSIDE the
        base from the candidate pool, never declared as a variant, and so invisible here until now
        (2026-08-27, Lucas: "all variants displayed"). Marked readOnly: it isn't regenerated from a
        prompt, it's re-committed with its base, so the gallery only shows it.
    Cinemagraphs are deliberately NOT included — they're clips, picked in the rooms table.
    """
    doc = _load_scenario(base)
    out = []
    for r in doc.get("rooms") or []:
        rk = r.get("key")
        room_base = r.get("panorama") or ("%s/scene.png" % rk)
        declared = set()
        for h in (r.get("hotspots") or []):
            for v in (h.get("variants") or []):
                pano = v.get("panorama")
                if pano:
                    declared.add(pano)
                out.append({
                    "room": rk,
                    "roomTitle": r.get("title"),
                    "hotspot": h.get("id"),
                    "hotspotType": h.get("type"),
                    "state": v.get("state"),
                    "when": v.get("when"),
                    "prompt": v.get("prompt"),
                    "panorama": pano,
                    "base": room_base,
                    "fullScene": v.get("box") == [0, 0, 1, 1] or h.get("box") == [0, 0, 1, 1],
                    "readOnly": False,
                    "exists": bool(pano) and os.path.isfile(os.path.join(base, pano)),
                })
        # The door-open partner. Skipped when a hotspot variant already points at the same file, so a
        # room that declares its open state properly isn't listed twice.
        op = r.get("panoramaOpen")
        if op and op not in declared:
            out.append({
                "room": rk,
                "roomTitle": r.get("title"),
                "hotspot": None,
                "hotspotType": None,
                "state": "open",
                "when": None,
                "whenLabel": "when this room's door opens",
                "prompt": None,
                "panorama": op,
                "base": room_base,
                "fullScene": True,
                "readOnly": True,
                "exists": os.path.isfile(os.path.join(base, op)),
            })
    return out


def _start(slot, kind, target, total, tag=None):
    """Claim `slot` and run `target()` on a daemon thread. Returns False if the slot is already busy.

    The thread body is GUARDED: a job whose body raises before its own `active = False` would otherwise
    leave the slot claimed forever, and since JOBS lives in memory the only cure is restarting the server
    — every later job on that slot is refused with "already running" in the meantime. That is exactly what
    the `/api/gen-fullscene-variant` arg-shift did on 2026-08-26 (its lambda dropped the leading `slot`,
    so the except handler indexed JOBS by a filesystem path, raised KeyError, and killed the thread).
    The lambda is fixed; this makes the whole class impossible, on every slot, whatever the body does.
    """
    with LOCK:
        j = JOBS.get(slot)
        if j and j["active"]:
            return False
        JOBS[slot] = {"active": True, "kind": kind, "done": 0, "total": total,
                      "outputs": [], "error": None, "tag": tag}

    def _guarded():
        try:
            target()
        except BaseException as e:  # noqa: BLE001 — the slot must be released no matter what died
            with LOCK:
                if slot in JOBS and not JOBS[slot].get("error"):
                    JOBS[slot]["error"] = "job crashed: %s" % str(e)[-300:]
        finally:
            with LOCK:
                if slot in JOBS:
                    JOBS[slot]["active"] = False

    threading.Thread(target=_guarded, daemon=True).start()
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
        if route == "/api/motion-map":        # where a baked clip actually moves, as a PNG the UI overlays
            # Rendered on demand and cached beside the clip in _scratch (gitignored), keyed on the clip's
            # mtime so a re-bake invalidates it — a stale map describes a video that no longer exists,
            # which is the exact bug add_to_viewer's motion_map() had to grow a freshness check for.
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            room = re.sub(r"[^A-Za-z0-9_]", "", (q.get("room") or [""])[0])
            state = re.sub(r"[^A-Za-z0-9_]", "", (q.get("state") or ["base"])[0])
            clip = os.path.join(base, room, "cine_%s.mp4" % state)
            if not room or not os.path.isfile(clip):
                return self._json({"error": "no such clip"}, 404)
            cache_dir = os.path.join(base, "_scratch", "motion")
            os.makedirs(cache_dir, exist_ok=True)
            try:
                scale = float((q.get("scale") or ["0"])[0]) or None
            except ValueError:
                scale = None
            tag = ("%g" % scale) if scale else "auto"
            out = os.path.join(cache_dir, "%s_%s_%s_%d.png"
                               % (room, state, tag, int(os.path.getmtime(clip))))
            used = None
            if not os.path.isfile(out):
                try:
                    _, used = _render_motion_map(clip, out, scale=scale)
                except Exception as e:  # noqa: BLE001
                    return self._json({"error": "motion map failed: %s" % str(e)[:200]}, 500)
            # What white MEANS, so the viewer can label it and nobody compares two differently-scaled maps.
            if used is None:                      # cache hit: recover the scale from the cached name
                used = tag if tag != "auto" else _motion_scale_of(out)
            return self._serve_file(base, os.path.relpath(out, base),
                                    headers={"X-Motion-Scale": used,
                                             "Access-Control-Expose-Headers": "X-Motion-Scale"})
        if route == "/api/mask-grid":         # coverage over the whole (threshold x region) plane
            # THE MAP FOR THE 2D PAD. The two mask axes interact — a region cut can only bite once the
            # threshold is tight enough to break the frame into separate regions, so at a loose threshold
            # the whole frame is ONE component and the cut does nothing at all. That is invisible from
            # two independent sliders and obvious from a surface, which is what this serves.
            #
            # Computed at 1/GRID_SCALE resolution, with close radius and the region cut scaled with it,
            # and WITHOUT the final feather (a normalised blur preserves the mean, so it cannot move a
            # coverage number). It is a NAVIGATION AID and is labelled as one: the number the reviewer
            # acts on always comes from /api/motion-mask at full resolution. Do not let a caller quote
            # these figures as the mask's coverage — that is the browser-emulation trap in another hat.
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            room = re.sub(r"[^A-Za-z0-9_]", "", (q.get("room") or [""])[0])
            state = re.sub(r"[^A-Za-z0-9_]", "", (q.get("state") or ["base"])[0])
            clip = os.path.join(base, room, "cine_%s.mp4" % state)
            if not room or not os.path.isfile(clip):
                return self._json({"error": "no such clip"}, 404)
            cache_dir = os.path.join(base, "_scratch", "motion")
            os.makedirs(cache_dir, exist_ok=True)
            out = os.path.join(cache_dir, "grid_%s_%s_%d.json" % (room, state, int(os.path.getmtime(clip))))
            if os.path.isfile(out):
                try:
                    return self._json(json.load(open(out, encoding="utf-8")))
                except Exception:  # noqa: BLE001
                    pass
            try:
                grid = _mask_grid(_motion_tstd(clip, cache_dir))
            except Exception as e:  # noqa: BLE001
                return self._json({"error": "grid failed: %s" % str(e)[:200]}, 500)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(grid, f)
            return self._json(grid)
        if route == "/api/motion-mask":       # the cinemagraph mask, at auto or a chosen percentile
            # White/opaque = show the VIDEO, black/transparent = show the STILL. Built by `auto_mask`,
            # which is the mechanism Lucas confirmed ("auto threshold on the mask is working well") and
            # which had never been called from anywhere: a percentile ladder over the clip's OWN motion,
            # scored by object SOLIDITY, then closed, hole-filled and feathered. Percentiles because the
            # absolute temporal-std numbers differ per scene.
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            room = re.sub(r"[^A-Za-z0-9_]", "", (q.get("room") or [""])[0])
            state = re.sub(r"[^A-Za-z0-9_]", "", (q.get("state") or ["base"])[0])
            clip = os.path.join(base, room, "cine_%s.mp4" % state)
            if not room or not os.path.isfile(clip):
                return self._json({"error": "no such clip"}, 404)
            pct_raw = (q.get("pct") or ["auto"])[0]
            # THE REGION CUT, the second and independent axis (`auto_mask.drop_small`). Carried as
            # parts-per-million of the frame rather than raw pixels, so one slider position means the
            # same thing on a 3072x1024 panorama and on a cropped tile. 0 = off.
            try:
                region_ppm = max(0.0, float((q.get("region") or ["0"])[0]))
            except ValueError:
                region_ppm = 0.0
            # RGBA when the caller is CSS. `mask-image` reads the ALPHA channel, so a greyscale PNG is
            # opaque everywhere and masks NOTHING — the video played in full while the coverage number
            # said 0.7%, which is exactly the contradiction Lucas reported (2026-08-31).
            want_alpha = (q.get("alpha") or ["0"])[0] in ("1", "true")
            cache_dir = os.path.join(base, "_scratch", "motion")
            # The region cut is part of the cache KEY. Leaving it out served the previous cut's PNG for
            # a new slider position — a preview that silently disagrees with its own label is the whole
            # failure mode this endpoint exists to avoid.
            out = os.path.join(cache_dir, "mask_%s_%s_%s_r%g%s_%d.png"
                               % (room, state, pct_raw, region_ppm, "_a" if want_alpha else "",
                                  int(os.path.getmtime(clip))))
            meta = None
            if not os.path.isfile(out):
                try:
                    import numpy as _np
                    from PIL import Image as _Image
                    sys.path.insert(0, os.path.join(ESCAPE_ROOT, "cinemagraph_tools"))
                    from auto_mask import auto_mask, mask_at_percentile  # noqa: WPS433
                    tstd = _motion_tstd(clip, cache_dir)
                    min_px = int(region_ppm * tstd.size / 1e6)
                    if pct_raw == "auto":
                        m, thr, rep = auto_mask(tstd, min_px=min_px)
                        meta = {"pct": "auto", "thr": thr, "cov": float(m.mean()),
                                "region": region_ppm, "minPx": min_px,
                                "kept": rep.get("kept"), "dropped": rep.get("dropped")}
                    else:
                        pct = max(1.0, min(99.9, float(pct_raw)))
                        m, thr, cov, reg = mask_at_percentile(tstd, pct, min_px=min_px)
                        meta = {"pct": pct, "thr": thr, "cov": cov, "region": region_ppm,
                                "minPx": min_px, "kept": reg["kept"], "dropped": reg["dropped"]}
                    g = (_np.clip(m, 0, 1) * 255).astype("uint8")
                    if want_alpha:
                        rgba = _np.zeros(g.shape + (4,), dtype="uint8")
                        rgba[..., :3] = 255
                        rgba[..., 3] = g
                        _Image.fromarray(rgba, "RGBA").save(out)
                    else:
                        _Image.fromarray(g, "L").save(out)
                    with open(out + ".meta", "w", encoding="utf-8") as f:
                        json.dump(meta, f)
                except Exception as e:  # noqa: BLE001
                    return self._json({"error": "mask failed: %s" % str(e)[:200]}, 500)
            if meta is None:
                try:
                    meta = json.load(open(out + ".meta", encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    meta = {"pct": pct_raw, "thr": 0, "cov": 0}
            return self._serve_file(base, os.path.relpath(out, base), headers={
                "X-Mask-Coverage": "%.1f" % (100 * meta["cov"]),
                "X-Mask-Threshold": "%.2f" % meta["thr"],
                "X-Mask-Pct": str(meta["pct"]),
                "X-Mask-Min-Px": str(meta.get("minPx", 0)),
                "X-Mask-Regions": str(meta.get("kept") if meta.get("kept") is not None else ""),
                "X-Mask-Dropped": str(meta.get("dropped") if meta.get("dropped") is not None else ""),
                "Access-Control-Expose-Headers":
                    "X-Mask-Coverage,X-Mask-Threshold,X-Mask-Pct,X-Mask-Min-Px,X-Mask-Regions,X-Mask-Dropped"})
        if route == "/api/plate-candidates":  # world-plate candidates in _scratch + which one is committed
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            _pfiles = _plate_candidates(base)
            return self._json({"files": _pfiles,
                               # the committed plate is shown once, at the top of its card — so the
                               # candidate it was promoted from must drop out of the list below it.
                               "uncommitted": _scratch_uncommitted(base, _pfiles, _world_plate_abs(base)),
                               "committed": bool(_world_plate_abs(base)),
                               "worldPlate": (_load_scenario(base).get("worldPlate") or "")})
        if route == "/api/cover-candidates":  # scenario cover candidates in _scratch + which is committed
            try:
                base = self._query_base()
            except ValueError:
                return self._json({"error": "bad scenario"}, 400)
            _cfiles = _cover_candidates(base)
            _cabs = os.path.join(base, "cover.png")
            return self._json({"files": _cfiles,
                               "uncommitted": _scratch_uncommitted(base, _cfiles, _cabs),
                               "cover": (_load_scenario(base).get("cover") or "")})
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
        if route == "/api/variants":         # ?chapter&scenario — every state variant, for the review gallery
            q = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            try:
                base = _scenario_base((q.get("chapter") or [None])[0], (q.get("scenario") or [None])[0])
            except ValueError as ve:
                return self._json({"ok": False, "error": str(ve)}, 400)
            return self._json({"ok": True, "variants": collect_variants(base)})
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

    def _serve_file(self, base, rel, headers=None):
        """Serve a file from under `base` (SCENE or the scenario dir), which live outside the
        served ROOT. Path-confined to `base`.

        `headers` adds response headers — used by the motion map to report the scale it auto-picked,
        so the viewer can say what white means instead of leaving two differently-scaled maps looking
        directly comparable."""
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
        for k, v in (headers or {}).items():
            self.send_header(k, str(v))
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
                try:
                    scene_p, _stem = room_target(base, rk, req.get("file"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                lf, rf, ff, _full, pos = _seam_bounds(req)
                mode = str(req.get("mode") or "patch")   # no whole-frame mode any more; legacy full=1 ignored
                if mode in _SEAM_LOCAL_OPS:      # instant, in-process, no model — still pushes an undo snapshot
                    try:
                        return self._json({"ok": True, "instant": True, "report": _seam_local(scene_p, mode, req)})
                    except Exception as e:  # noqa: BLE001
                        return self._json({"ok": False, "error": str(e)}, 400)
                if mode not in _SEAM_AI_MODES:
                    return self._json({"ok": False, "error": "unknown seam mode %r" % mode}, 400)
                crop = req.get("crop") or (0.34 if mode in ("patch", "occluder") else None)
                occl = req.get("occluder") if mode == "occluder" else None
                if mode == "occluder" and not str(occl or "").strip():
                    return self._json({"ok": False, "error": "occluder mode needs a description of what stands on the seam"}, 400)
                full = False                             # both remaining AI modes composite a crop
                ef = req.get("editFrac")
                if not _start("seam", "seamfix", lambda: _run_seamfix_room("seam", base, rk, lf, rf, ff, full, pos, crop, occl, ef,
                                                        req.get("file")), 1):
                    return self._json({"ok": False, "error": "a seamfix job is already running"}, 409)
                return self._json({"ok": True, "slot": "seam"})
            if route == "/api/select-scenario":
                req = self._body()
                try:
                    _select_scenario(str(req.get("chapter") or ""), str(req.get("scenario") or ""))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "active": dict(ACTIVE), "config": _scenario_config()})
            if route == "/api/serve-clips":
                # Wire ONE room's baked clips onto carriers so play stops serving the still. Per room,
                # next to the clip it affects — the same shape as every other Commit in this harness.
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    wired, unchanged = _serve_room_clips(req.get("roomKey"), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "wired": wired, "unchanged": unchanged})
            if route == "/api/commit-planned":
                # Promote ONE room's plannedHotspots into its live hotspots, boxes and all. Per room, not
                # per scenario: the gallery offers it next to the room it affects, the same shape as the
                # per-candidate Commit on the art and cinemagraph tabs.
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    created, already, boxless = _commit_planned_hotspots(req.get("roomKey"), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "created": created, "already": already,
                                   "boxless": boxless})
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
                    # "needs replacement" flags ride the same Save (no second button in the mixer)
                    summary["flagged"] = _apply_audio_flags(base, req.get("flags") or {})
                except (ValueError, TypeError) as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **summary})
            if route == "/api/audio-flags":
                # current needs-replacement flags, so the mixer opens with earlier flags already lit
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, "flags": _audio_flags(base)})
            if route == "/api/run-tests":
                # One go/no-go over every escape-room suite, for the console's top-bar button. Runs on a
                # job slot like any other long task: each suite's result is appended to `outputs` as it
                # finishes, so the UI shows progress rather than a three-minute dead spinner. `fast:true`
                # skips the Playwright browser suites (~20 s vs ~3-4 min) — the browser ones are the only
                # thing that proves a student's real path works, so `fast` is for iterating, not for
                # clearing a push.
                req = self._body()
                fast = bool(req.get("fast"))
                import run_all_tests                                   # local, stdlib-only, cheap import
                suites = run_all_tests._suites(fast)

                def _go():
                    def _event(rec):
                        with LOCK:
                            j = JOBS.get("tests")
                            if j is not None:
                                j["outputs"].append(rec)
                                j["done"] = rec["index"]
                    summary = run_all_tests.run(fast=fast, on_event=_event)
                    with LOCK:
                        j = JOBS.get("tests")
                        if j is not None:
                            j["tag"] = summary                          # verdict + counts, read by the UI

                if not _start("tests", "tests", _go, len(suites)):
                    return self._json({"ok": False, "error": "a test run is already going"}, 409)
                return self._json({"ok": True, "slot": "tests", "total": len(suites), "fast": fast})
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
            if route == "/api/gen-fullscene-variant":
                # The whole-panorama re-light (night arc). Distinct from /api/gen-variant-room, which
                # masks a box: this one holds the composition and ADDS light, and it is the route the
                # console's Environmental-variants panel regenerates through.
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                state = (req.get("state") or "").strip()
                prompt = (req.get("prompt") or "").strip()
                if not rk or not state:
                    return self._json({"ok": False, "error": "need roomKey and state"}, 400)
                if not prompt:
                    return self._json({"ok": False, "error": "empty variant prompt"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                if not os.path.isfile(os.path.join(base, rk, "scene.png")):
                    return self._json({"ok": False, "error": "room %s has no committed scene.png" % rk}, 400)
                if _batch_running(base):
                    return self._json({"ok": False, "error": "a batch is running — wait for it to finish"}, 409)
                if not _start("variant", "variant",
                              lambda: _run_fullscene("variant", base, rk, state, prompt,
                                                     req.get("when"), req.get("carrier")), 1):
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
            if route == "/api/delete-cinemagraph":       # un-commit: drop the ACTIVE clip, keep the pool
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    _remove_cinemagraph(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                        str(req.get("hotspotId") or "").strip(), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True})
            if route == "/api/uncommit-cinemagraph":     # ✓ toggled off: un-deploy but KEEP the clip in the pool
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    _uncommit_cinemagraph(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                          str(req.get("hotspotId") or "").strip(), base)
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True})
            if route == "/api/delete-cinemagraph-candidate":   # ✕ on a tile: remove one clip from the pool
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    _delete_cinemagraph_candidate(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                                  str(req.get("hotspotId") or "").strip(), int(req.get("index")), base)
                except (ValueError, TypeError) as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True})
            if route == "/api/reloop-cinemagraph":        # switch boomerang↔crossfade AFTER generation
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    out = _reloop_cinemagraph(re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or "")),
                                              str(req.get("hotspotId") or "").strip(),
                                              str(req.get("which") or "candidate"),
                                              int(req.get("index") or 0), str(req.get("loop") or ""), base)
                    return self._json({"ok": True, **out})
                except (ValueError, TypeError) as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                except Exception as e:  # noqa: BLE001 — surface ffmpeg trouble to the UI
                    return self._json({"ok": False, "error": str(e)[-400:]}, 500)
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
            if route == "/api/accept-still":          # the HUMAN accept on a committed still
                req = self._body()
                rk = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("roomKey") or ""))
                if not rk:
                    return self._json({"ok": False, "error": "need roomKey"}, 400)
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                    return self._json({"ok": True, **_accept_still(
                        base, rk, bool(req.get("accepted", True)),
                        req.get("note") or "", req.get("state") or None)})
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
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
            if route == "/api/set-puzzle-prompts":    # build-world story flow: bulk-save edited puzzle prompts
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **_set_puzzle_prompts(base, req.get("prompts") or [])})
            if route == "/api/set-clues":             # build-world story flow: bulk-save edited clue bodies
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **_set_clues(base, req.get("clues") or [])})
            if route == "/api/set-locked-messages":   # build-world story flow: bulk-save edited lockedBody nav messages
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                return self._json({"ok": True, **_set_locked_messages(base, req.get("messages") or [])})
            if route == "/api/gen-world-plate":      # build-world: the scenario's shared continuity reference (first in step 2)
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                blocked = _preflight_guard(base)
                if blocked:
                    return self._json({"ok": False, "error": blocked}, 409)
                prompt = (_load_scenario(base).get("worldPlatePrompt") or "").strip()
                if not prompt:
                    return self._json({"ok": False, "error": "no worldPlatePrompt in the spec — add one first"}, 400)
                size = req.get("size", "3072x1024")
                ok_size, size_err = _valid_size(size)
                if not ok_size:
                    return self._json({"ok": False, "error": size_err}, 400)
                # N candidates to choose between (default 2, Lucas 2026-09-01 — four was more than he
                # wanted to look at and cost ~4 min a call). The ceiling stays at MAX_PLATE_CANDIDATES:
                # this is the default, not a limit, so a caller that wants a wider pool still can.
                try:
                    n = max(1, min(int(req.get("n", 2)), MAX_PLATE_CANDIDATES))
                except (TypeError, ValueError):
                    n = 2
                if not _start("worldplate", "genplate",
                              lambda: _run_gen_world_plate("worldplate", base, prompt, size, "high", n), n):
                    return self._json({"ok": False, "error": "already generating the world plate"}, 409)
                return self._json({"ok": True, "slot": "worldplate", "n": n})
            if route == "/api/gen-room-pano":        # build-world level 1: one hi-res pano for a room
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                blocked = _preflight_guard(base)
                if blocked:
                    return self._json({"ok": False, "error": blocked}, 409)
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
                lf, rf, ff, _full, pos = _seam_bounds(req)
                mode = str(req.get("mode") or "patch")   # no whole-frame mode any more; legacy full=1 ignored
                img_p = os.path.join(base, "_scratch", image)
                if mode in _SEAM_LOCAL_OPS:
                    if not os.path.isfile(img_p):
                        return self._json({"ok": False, "error": "no scratch pano %s" % image}, 400)
                    try:
                        return self._json({"ok": True, "instant": True, "report": _seam_local(img_p, mode, req)})
                    except Exception as e:  # noqa: BLE001
                        return self._json({"ok": False, "error": str(e)}, 400)
                if mode not in _SEAM_AI_MODES:
                    return self._json({"ok": False, "error": "unknown seam mode %r" % mode}, 400)
                crop = req.get("crop") or (0.34 if mode in ("patch", "occluder") else None)
                occl = req.get("occluder") if mode == "occluder" else None
                if mode == "occluder" and not str(occl or "").strip():
                    return self._json({"ok": False, "error": "occluder mode needs a description of what stands on the seam"}, 400)
                full = False                             # both remaining AI modes composite a crop
                ef = req.get("editFrac")
                if not _start("seam", "seamfix", lambda: _run_seamfix_scratch("seam", base, image, lf, rf, ff, full, pos, crop, occl, ef), 1):
                    return self._json({"ok": False, "error": "a seamfix job is already running"}, 409)
                return self._json({"ok": True, "slot": "seam"})
            if route == "/api/seam-measure":       # how big is the seam vs the scene's own detail?
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rk = req.get("roomKey")
                if rk:
                    try:
                        p, _ = room_target(base, re.sub(r"[^A-Za-z0-9_]", "", str(rk)), req.get("file"))
                    except ValueError as ve:
                        return self._json({"ok": False, "error": str(ve)}, 400)
                else:
                    p = os.path.join(base, "_scratch", os.path.basename(str(req.get("image") or "")))
                if not os.path.isfile(p):
                    return self._json({"ok": False, "error": "no image to measure"}, 400)
                try:
                    return self._json({"ok": True, **_seam_measure(p, float(req.get("pos") or 1.0))})
                except Exception as e:  # noqa: BLE001
                    return self._json({"ok": False, "error": str(e)}, 400)
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
                    return self._json({"ok": True, **_undo_seam_room(base, rk, req.get("file"))})
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
                    # a state variant keeps its own undo stack, keyed by its stem (scene_night, …)
                    stem = os.path.splitext(os.path.basename(str(req.get("file") or "scene.png")))[0]
                    depth = _seam_depth(os.path.join(base, rk), stem or "scene")
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
            if route == "/api/validate-story":
                # The Story stage's closing gate — see authoring_v2/validate_story.py. `accept` snapshots
                # the current landing card as the vetted reference; otherwise diff the rest of the text
                # against that snapshot.
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                rel = os.path.relpath(base, os.path.join(os.path.dirname(HERE), "rooms"))
                argv = ["python3", os.path.join(HERE, "validate_story.py"), rel]
                if req.get("accept"):
                    argv.append("--accept")
                r = subprocess.run(argv, capture_output=True, text=True)
                out = (r.stdout or "") + (r.stderr or "")
                return self._json({"ok": True, "output": out.strip(),
                                   "failed": sum(1 for l in out.splitlines() if l.startswith("FAIL"))})
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
                                               engine=str(req.get("engine") or "gpt4o"))
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
            if route == "/api/mask-set":         # set a clip's mask threshold, then rebuild it
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                room = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("room") or ""))
                state = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("state") or "base"))
                pct = req.get("pct", "auto")
                if pct != "auto":
                    try:
                        pct = max(1.0, min(99.9, float(pct)))
                    except (TypeError, ValueError):
                        pct = "auto"
                try:
                    region = max(0.0, float(req.get("region") or 0))
                except (TypeError, ValueError):
                    region = 0.0
                if not room:
                    return self._json({"ok": False, "error": "need a room"}, 400)
                slot = "mask_%s_%s" % (room, state)
                if not _start(slot, "maskrebuild",
                              lambda: _run_mask_rebuild(slot, base, room, state, pct,
                                                        req.get("enabled", True), region), 1):
                    return self._json({"ok": False, "error": "this clip is already rebuilding"}, 409)
                return self._json({"ok": True, "slot": slot})
            if route == "/api/patch-set":        # enable/disable a repair patch, then rebuild the clip
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                room = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("room") or ""))
                state = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("state") or "base"))
                name = re.sub(r"[^A-Za-z0-9_]", "", str(req.get("name") or ""))
                enabled = bool(req.get("enabled"))
                if not room or not name:
                    return self._json({"ok": False, "error": "need room + patch name"}, 400)
                slot = "patch_%s_%s" % (room, state)
                if not _start(slot, "patchrebuild",
                              lambda: _run_patch_rebuild(slot, base, room, state, name, enabled), 1):
                    return self._json({"ok": False, "error": "this clip is already rebuilding"}, 409)
                return self._json({"ok": True, "slot": slot})
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
            if route == "/api/delete-plate-candidate":
                # drop a world-plate candidate the author does not want. Only ever removes a _scratch
                # candidate — never the committed _world/plate.png, which is a pushable asset.
                req = self._body()
                try:
                    base = _scenario_base(req.get("chapter"), req.get("scenario"))
                except ValueError as ve:
                    return self._json({"ok": False, "error": str(ve)}, 400)
                fn = os.path.basename(str(req.get("file") or ""))
                if not re.match(r"^world_plate(_\d+)?\.png$", fn):
                    return self._json({"ok": False, "error": "not a plate candidate: %s" % fn}, 400)
                fp = os.path.join(base, "_scratch", fn)
                if not os.path.isfile(fp):
                    return self._json({"ok": False, "error": "no such candidate: %s" % fn}, 400)
                os.remove(fp)
                return self._json({"ok": True, "removed": fn})
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
