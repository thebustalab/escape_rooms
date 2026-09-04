#!/usr/bin/env python3
"""art_cli.py — agent-triggerable art generation for the build-world harness.

WHY THIS EXISTS. The build_world console (`harness_server.py`, :8752) can already generate state
variants and cinemagraphs, but only through its web UI, in a browser, on the desktop. Lucas often wants
to fire those jobs from the MOBILE assistant and then walk to the computer to review the results. This
CLI exposes the same generation primitives with **no browser and no running harness server**, so an agent
can trigger them through an observer row (project `escape_art`) and return immediately — the
fire-and-forget shape the root `AGENTS.md` asks for.

IT SHARES THE HARNESS'S LOGIC, IT DOES NOT COPY IT. `harness_server` is imported as a module (its server
only starts under `if __name__ == "__main__"`, so importing is inert) and this CLI calls its scenario
resolution, scenario.json load/save, variant MERGE (`_add_variant`) and batch machinery. Image calls shell
out to `generate_scene.py`, exactly as the server's own `/api/gen-variant-room` does. If the harness
changes how a variant is recorded, this CLI changes with it.

THREE JOB TYPES
  • `night`       full-scene state variant. The night-arc route (`authoring_v2/AGENTS.md` → *Full-scene
                  state variants*): post the committed day panorama to the image-EDIT endpoint with a
                  night prompt and no mask, **asking for the BASE'S OWN NATIVE SIZE**, then ensure a
                  marker-less `ambient` carrier hotspot at box [0,0,1,1] holds the variant. Costs an
                  API call per room.

                  ⚠️ CORRECTED 2026-09-02 — DO NOT STRETCH. This entry used to say the endpoint "will
                  not return 3:1 — it comes back 1536x1024" and must be restretched to the base's size.
                  That is wrong, and following it stretched every night variant 2x horizontally:
                  `generate_scene.py edit` merely DEFAULTS `--size` to 1536x1024 and the caller never
                  overrode it. The premise — that the model lays the scene out inside the squashed frame,
                  so a resize restores it — holds only for structure COPIED from the input; anything it
                  RE-DRAWS it draws at natural proportions, and those objects came back twice as wide
                  (Lucas, on egypt: "stretched weirdly"). Verified against the live API: /images/edits
                  returns 3072x1024 when asked for it.

                  The code has been right since that date — `_run_night` delegates to
                  `harness_server.run_fullscene_variant`, which reads the base's size and passes it as
                  `--size`, leaving `restretch_to` as a no-op safety net for a reply that ignores the
                  request. Only this docstring lagged, which is its own lesson: a stale docstring above
                  correct code is the shape that gets copied into the next caller. Egypt's seven night
                  variants predate the fix and are still 2x-stretched — regenerate them.
  • `variant`     masked-box state variant on one hotspot — the `dooropen` primitive, i.e. the same thing
                  the console's "generate variant" button does. Costs an API call per job.
  • `cinemagraph` queued onto the scenario's batch and launched through `~/ComfyUI/cinemagraph_batch.py`
                  (detached, local GPU, no API cost, bounces lm_server once). Fired last, after the
                  synchronous image jobs, because it walks away and reports through a status file.

USAGE
    python3 art_cli.py status  --chapter wrangling --scenario egypt
    python3 art_cli.py run     --chapter wrangling --scenario egypt --spec-file jobs.json [--dry-run]
    python3 art_cli.py run     --chapter wrangling --scenario egypt --spec '{"jobs":[...]}'

SPEC SHAPE — one JSON object, `jobs` is a list; unknown keys are rejected loudly rather than ignored.
    {"jobs": [
      {"type":"night",  "room":"deck", "prompt":"…", "state":"night",
                        "when":{"solved":"library"}, "carrier":"night_wash"},
      {"type":"variant","room":"pharos","hotspot":"harbour_below","state":"beam_on_ship",
                        "box":[0.80,0.32,0.91,0.47],"prompt":"…","when":{"eq":["pharos_beam","ship"]}},
      {"type":"cinemagraph","room":"lantern","hotspot":"great_lamp","prompt":"…","loop":"boomerang"}
    ]}

`--dry-run` validates everything — scenario, rooms, committed scenes, hotspots, boxes, prompts — and
prints the plan without spending a penny. ALWAYS worth a dry run first from a mobile turn.

ENVIRONMENT. The image routes need `OPENAI_API_KEY`. **Do not assume the observer has it** — it very
likely does not; see `_gen_env()` for the diagnosis and the runtime fallback that makes this work
anyway. `status` and `--dry-run` need no key, and `run` preflights for one before spending anything.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harness_server as HS          # noqa: E402  (inert on import — the server is __main__-guarded)

GEN = os.path.join(HERE, "generate_scene.py")


def _gen_env():
    """Environment for the generation subprocess, guaranteed to carry OPENAI_API_KEY if it exists at all.

    WHY THIS IS NEEDED (diagnosed 2026-08-13, after the first live Egypt run failed with six
    `OPENAI_API_KEY not set` errors and spent nothing). The observer launches this CLI with
    `subprocess.run(...)` and **no shell**, so the child simply inherits the observer's own environment
    — no rc file is consulted at any point in the chain. And `~/.bashrc` exports the key at line 153,
    which is *below* the standard `if not running interactively, return` guard at line 6. So the key
    reaches an interactive terminal and nothing else. The long-running observer (started 2026-07-20)
    was launched before that export existed and has never had it.

    Rather than depend on when the observer was last restarted, resolve the key at call time by asking
    a login+interactive bash for it — the same runtime-environment route the root `AGENTS.md` mandates
    for live credentials (`os.environ`, never a file read). The value is injected into the child's env
    and is never printed, logged, or written anywhere.

    `-i` is required as well as `-l`: it is interactivity, not login, that makes bash read `~/.bashrc`.
    """
    env = os.environ.copy()
    if env.get("OPENAI_API_KEY"):
        return env
    try:
        r = subprocess.run(["bash", "-lic", 'printf %s "${OPENAI_API_KEY:-}"'],
                           capture_output=True, text=True, timeout=20)
        key = (r.stdout or "").strip()
    except Exception:                                  # noqa: BLE001 — a missing key is reported below
        key = ""
    if key:
        env["OPENAI_API_KEY"] = key
    return env


def _have_image_key(env):
    return bool(env.get("OPENAI_API_KEY"))

NIGHT_KEYS = {"type", "room", "prompt", "state", "when", "carrier", "size"}
VARIANT_KEYS = {"type", "room", "hotspot", "state", "box", "prompt", "when", "quality"}
CINE_KEYS = {"type", "room", "hotspot", "prompt", "loop", "box", "candidates"}


# --------------------------------------------------------------------------- validation

def _fail(msg):
    raise ValueError(msg)


def _room_node(doc, key):
    return next((r for r in doc.get("rooms") or [] if r.get("key") == key), None)


def _check_job(base, doc, job, i):
    """Validate one job against the scenario on disk. Raises ValueError naming the job index."""
    where = f"job {i}"
    typ = job.get("type")
    if typ not in ("night", "variant", "cinemagraph"):
        _fail(f"{where}: type must be night|variant|cinemagraph (got {typ!r})")
    allowed = {"night": NIGHT_KEYS, "variant": VARIANT_KEYS, "cinemagraph": CINE_KEYS}[typ]
    extra = set(job) - allowed
    if extra:
        _fail(f"{where}: unknown key(s) {sorted(extra)} for a {typ} job")
    rk = job.get("room")
    node = _room_node(doc, rk)
    if node is None:
        _fail(f"{where}: no room {rk!r} in this scenario")
    scene = os.path.join(base, rk, "scene.png")
    if not os.path.isfile(scene):
        _fail(f"{where}: room {rk!r} has no committed scene.png — commit its art first")
    if not (job.get("prompt") or "").strip():
        _fail(f"{where}: needs a prompt")
    if typ in ("variant", "cinemagraph"):
        hid = (job.get("hotspot") or "").strip()
        if not hid:
            _fail(f"{where}: a {typ} job needs a hotspot id")
        spot = next((h for h in (node.get("hotspots") or []) if h.get("id") == hid), None)
        if spot is None:
            _fail(f"{where}: no hotspot {hid!r} in room {rk!r}")
        box = job.get("box") or spot.get("box")
        if not (isinstance(box, list) and len(box) == 4):
            _fail(f"{where}: needs a box[4] (hotspot {hid!r} has none to fall back on)")
        job["box"] = box                                    # resolve the fallback once, here
    if typ == "variant" and not (job.get("state") or "").strip():
        _fail(f"{where}: a variant job needs a state")
    if typ == "night":
        job.setdefault("state", "night")
        job.setdefault("carrier", "night_wash")
    return job


def _plan(base, spec):
    doc = HS._load_scenario(base)
    jobs = spec.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        _fail("spec needs a non-empty `jobs` list")
    return [_check_job(base, doc, dict(j), i) for i, j in enumerate(jobs)]


# --------------------------------------------------------------------------- night (full-scene)

# The full-scene helpers now live in `harness_server` so the console's Environmental-variants panel and
# this CLI run the SAME code — the console regenerates through /api/gen-fullscene-variant, which calls
# `run_fullscene_variant` directly. These thin aliases keep the CLI's own call sites (and its tests)
# reading naturally; do not reimplement either here.
_ensure_carrier = HS.ensure_variant_carrier
_restretch = HS.restretch_to


def _run_night(base, job, env=None):
    """One full-scene night variant. Delegates to the harness so the recorded shape can't drift —
    notably the `prompt`, which the review panel needs in order to offer a regenerate."""
    v = HS.run_fullscene_variant(base, job["room"], job["state"], job["prompt"],
                                 job.get("when"), job.get("carrier"))
    return {"job": "night", "room": job["room"], "state": v["state"],
            "file": v["panorama"], "carrier": job.get("carrier")}


# --------------------------------------------------------------------------- masked-box variant

def _run_variant(base, job, env=None):
    rk, hid, state = job["room"], job["hotspot"], job["state"]
    safe_state = HS.re.sub(r"[^A-Za-z0-9_]+", "_", state).strip("_") or "state"
    safe_id = HS.re.sub(r"[^A-Za-z0-9_]+", "_", hid).strip("_") or "obj"
    fname = f"var_{safe_id}_{safe_state}.png"
    out = os.path.join(base, rk, fname)
    subprocess.run(["python3", GEN, "dooropen", "--input", os.path.join(base, rk, "scene.png"),
                    "--box", ",".join(str(x) for x in job["box"]),
                    "--prompt", job["prompt"], "--out", out],
                   check=True, capture_output=True, text=True, env=env)
    variant = {"state": safe_state, "box": job["box"], "prompt": job["prompt"],
               "panorama": f"{rk}/{fname}"}
    if job.get("when") is not None:
        variant["when"] = job["when"]
    HS._add_variant(rk, hid, variant, base)
    return {"job": "variant", "room": rk, "hotspot": hid, "state": safe_state,
            "file": f"{rk}/{fname}"}


# --------------------------------------------------------------------------- cinemagraph batch

def _run_cinemagraphs(base, jobs):
    """Queue every cinemagraph job onto the scenario's batch and launch it DETACHED.

    Deliberately last and deliberately fire-and-forget: the batch is a long local-GPU run that bounces
    lm_server once and reports through `_scratch/cine_batch_status.json`. Nothing here waits on it —
    check back with `art_cli.py status`.
    """
    if HS._batch_running(base):
        _fail("a batch is already running for this scenario — wait for it, or check `status`")
    with HS.BATCH_LOCK:
        queue = HS._batch_read_queue(base)
        for j in jobs:
            minimal = {"type": "cinemagraph", "roomKey": j["room"], "hotspotId": j["hotspot"],
                       "box": j["box"], "prompt": j["prompt"]}
            if j.get("loop"):
                minimal["loop"] = j["loop"]
            if j.get("candidates"):
                minimal["candidates"] = j["candidates"]
            HS._expand_job(base, minimal)          # validate before queueing, same as /api/batch-add
            queue.append(minimal)
        HS._batch_write_queue(base, queue)
        total = HS._launch_batch(base)
    return {"job": "cinemagraph-batch", "launched": total,
            "note": "detached local-GPU run; poll `art_cli.py status`"}


# --------------------------------------------------------------------------- commands

def cmd_status(a):
    base = HS._scenario_base(a.chapter, a.scenario)
    doc = HS._load_scenario(base)
    rows = []
    for r in doc.get("rooms") or []:
        variants = [(h.get("id"), v.get("state"), v.get("panorama"))
                    for h in (r.get("hotspots") or []) for v in (h.get("variants") or [])]
        clips = [h.get("id") for h in (r.get("hotspots") or []) if h.get("video")]
        rows.append((r.get("key"), os.path.isfile(os.path.join(base, r.get("key") or "", "scene.png")),
                     variants, clips))
    out = {"scenario": f"{a.chapter}/{a.scenario}", "status": doc.get("status"),
           "batch": {"running": HS._batch_running(base), "status": HS._batch_status(base),
                     "queued": len(HS._batch_read_queue(base))},
           "rooms": [{"key": k, "committed": c, "variants": [
               {"hotspot": h, "state": s, "panorama": p} for h, s, p in v], "clips": cl}
               for k, c, v, cl in rows]}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_run(a):
    base = HS._scenario_base(a.chapter, a.scenario)
    if a.spec_file:
        spec = json.load(open(a.spec_file, encoding="utf-8"))
    elif a.spec:
        spec = json.loads(a.spec)
    else:
        _fail("need --spec or --spec-file")
    jobs = _plan(base, spec)

    print(f"scenario {a.chapter}/{a.scenario} — {len(jobs)} job(s)")
    for i, j in enumerate(jobs):
        bits = [j["type"], j["room"]]
        if j.get("hotspot"):
            bits.append(j["hotspot"])
        if j.get("state"):
            bits.append(f"state={j['state']}")
        print(f"  {i}. " + " · ".join(bits))
    needs_key = any(j["type"] in ("night", "variant") for j in jobs)
    env = _gen_env() if needs_key else os.environ.copy()
    if needs_key:
        print(f"image key: {'resolved' if _have_image_key(env) else 'NOT FOUND'}")

    if a.dry_run or str(a.dry).strip().lower() in ("1", "true", "yes", "y"):
        print("\nDRY RUN — validated only, nothing generated, nothing spent.")
        return 0

    # Preflight, so a fleet of jobs fails in one line instead of once per job. The first live Egypt run
    # (2026-08-13) printed the same missing-key error six times and looked like six separate failures.
    if needs_key and not _have_image_key(env):
        print("\nerror: OPENAI_API_KEY could not be resolved from the environment or from a login "
              "shell — see _gen_env(). Nothing generated, nothing spent.")
        return 2

    results, errors = [], []
    for i, j in enumerate(jobs):
        if j["type"] == "cinemagraph":
            continue                                   # batched together, after the API jobs
        try:
            r = _run_night(base, j, env) if j["type"] == "night" else _run_variant(base, j, env)
            results.append(r)
            print(f"  ok   job {i}: {r['file']}", flush=True)
        except subprocess.CalledProcessError as e:
            msg = (e.stderr or e.stdout or str(e)).strip()[-400:]
            errors.append({"job": i, "error": msg})
            print(f"  FAIL job {i}: {msg}", flush=True)
        except Exception as e:                          # noqa: BLE001
            errors.append({"job": i, "error": str(e)[-400:]})
            print(f"  FAIL job {i}: {e}", flush=True)

    cines = [j for j in jobs if j["type"] == "cinemagraph"]
    if cines:
        try:
            results.append(_run_cinemagraphs(base, cines))
            print(f"  ok   cinemagraph batch launched ({len(cines)} job(s))", flush=True)
        except Exception as e:                          # noqa: BLE001
            errors.append({"job": "cinemagraph-batch", "error": str(e)[-400:]})
            print(f"  FAIL cinemagraph batch: {e}", flush=True)

    print("\n" + json.dumps({"ok": not errors, "results": results, "errors": errors},
                            indent=2, ensure_ascii=False))
    return 1 if errors else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("status", cmd_status), ("run", cmd_run)):
        s = sub.add_parser(name)
        s.set_defaults(fn=fn)
        s.add_argument("--chapter", required=True)
        s.add_argument("--scenario", required=True)
        if name == "run":
            s.add_argument("--spec", help="the job spec as a JSON string")
            s.add_argument("--spec-file", dest="spec_file", help="path to the job spec JSON")
            s.add_argument("--dry-run", dest="dry_run", action="store_true",
                           help="validate and print the plan; generate nothing")
            # Observer rows can't add or drop a bare flag — the command template is fixed — so the same
            # switch is also reachable as a VALUE: `--dry {dry}` passes "" (run) or "1" (validate only).
            s.add_argument("--dry", default="",
                           help='value form of --dry-run for observer rows ("1"/"true"/"yes" = dry run)')
    a = p.parse_args()
    try:
        return a.fn(a)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
