#!/usr/bin/env python3
"""
preflight.py — the ONE gate between tab 1 (Concept & world) and tab 2 (Still art).

WHY THIS EXISTS AS A SCRIPT AND NOT A CHECKLIST
  Every pre-art check we have is cheap, and every one of them has been skipped at least once because
  it lived in prose. `seam_stage.py`'s docstring records the cost: the art phase "sat between two
  skills as the human bit, gated by nothing, which is how twelve unchecked seams once shipped."
  A checklist item inside a skill is a reminder. This is a gate: it exits non-zero, and the harness
  refuses to spend a generation without a fresh pass.

WHY IT STAMPS A HASH
  Passing once is not enough — the failure we actually hit (heist, 2026-09-03) was specs authored
  BEFORE the dataset existed and never re-checked afterwards. The stamp records a hash of
  scenario.json (which carries every room's sceneSpec) plus the dataset. Edit either and the stamp
  goes stale, so the gate re-arms itself automatically.

  usage:  python3 authoring_v2/preflight.py <chapter>/<scenario>
  escape: PREFLIGHT_OVERRIDE=1 (recorded in the stamp, so an override is never invisible)
"""
import hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = ".preflight_ok"


def _hash(base):
    h = hashlib.sha256()
    for p in [os.path.join(base, "scenario.json")] + sorted(
            os.path.join(base, "data", f) for f in os.listdir(os.path.join(base, "data"))
            if f.endswith(".csv")) if os.path.isdir(os.path.join(base, "data")) else [os.path.join(base, "scenario.json")]:
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def stamp_is_fresh(base):
    """True when a stamp exists AND matches the current scenario.json + datasets.

    GRANDFATHERED: a scenario that already has committed art is past the gate this protects, so it is
    never blocked — locking every existing scenario out of a re-generation would be a nasty surprise
    and is not the failure mode here. The gate is for a scenario about to spend its FIRST generation.
    """
    try:
        doc = json.load(open(os.path.join(base, "scenario.json")))
        if any(r.get("built") for r in doc.get("rooms", [])):
            return True, {"grandfathered": "scenario already has committed art"}
    except Exception:
        pass
    p = os.path.join(base, STAMP)
    if not os.path.isfile(p):
        return False, "no preflight stamp — run authoring_v2/preflight.py"
    try:
        rec = json.load(open(p))
    except Exception:
        return False, "preflight stamp unreadable — re-run preflight"
    if rec.get("hash") != _hash(base):
        return False, "preflight stamp is STALE (scenario.json or the dataset changed since it passed)"
    return True, rec


def main(target):
    base = os.path.join(ROOT, "rooms", target)
    if not os.path.isdir(base):
        print("no such scenario:", target); return 2
    fails, warns = [], []

    def ck(ok, msg):
        print(("  PASS  " if ok else "  FAIL  ") + msg)
        if not ok: fails.append(msg)

    # 1 — the file parses, and carries what art generation needs
    try:
        doc = json.load(open(os.path.join(base, "scenario.json")))
        ck(True, "scenario.json parses")
    except Exception as e:
        ck(False, f"scenario.json does not parse: {e}"); return 1
    ck(bool((doc.get("worldPlatePrompt") or "").strip()), "worldPlatePrompt is non-empty")
    ck(bool((doc.get("coverPrompt") or "").strip()), "coverPrompt is non-empty")
    speccy = [r for r in doc.get("rooms", []) if (r.get("authoring") or {}).get("sceneSpec")]
    ck(len(speccy) == len(doc.get("rooms", [])),
       f"every room has a sceneSpec ({len(speccy)}/{len(doc.get('rooms', []))})")

    # 2 — the mechanical scene check (silent killers: role->engine, labels, seam, sweep order)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "authoring_v2", "validate_scenes.py")],
                       capture_output=True, text=True, cwd=ROOT)
    mine = [l for l in (r.stdout + r.stderr).splitlines() if target in l]
    hard = [l for l in mine if l.strip().upper().startswith("FAIL") or l.strip().startswith("ERROR")]
    soft = [l for l in mine if l.strip().startswith("warn") and "no `back` door" not in l]
    ck(not hard, f"validate_scenes has no FAILs ({len(hard)})")
    for l in hard: print("         " + l.strip())
    if soft:
        warns += soft
        print(f"  warn  validate_scenes: {len(soft)} warning(s) — read them, they are not blocking")
        for l in soft[:6]: print("         " + l.strip())

    # 3 — the landing-text gate (needs a vetted snapshot to diff against)
    if not os.path.isfile(os.path.join(base, ".vetted_story.txt")):
        ck(False, "no .vetted_story.txt — Lucas must sign off the opening, then run validate_story.py --accept")
    else:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "authoring_v2", "validate_story.py"), target],
                           capture_output=True, text=True, cwd=ROOT)
        ck(r.returncode == 0, "validate_story gate is green")
        if r.returncode: print("         " + (r.stdout + r.stderr).strip()[:400])

    # 4 — SEMANTIC: rooms bound to real rows. validate_scenes cannot see this; it is the class of
    #     staleness that would have generated a blown vault door for a crew that was let in.
    jobs = set()
    dd = os.path.join(base, "data")
    if os.path.isdir(dd):
        for f in os.listdir(dd):
            if f.endswith(".csv"):
                with open(os.path.join(dd, f)) as fh:
                    rows = fh.read().splitlines()
                if rows:
                    for line in rows[1:]:
                        jobs.add(line.split(",")[0].strip())
    bound = {}
    for rm in doc.get("rooms", []):
        m = re.search(r"THE JOB:\s*\*\*(.+?)\*\*", rm.get("designNote") or "")
        if m: bound[rm["key"]] = m.group(1)
    if bound:
        bad = {k: v for k, v in bound.items() if v not in jobs}
        ck(not bad, f"every room bound to a named row exists in the dataset ({len(bound)} bound)")
        for k, v in bad.items(): print(f"         {k}: '{v}' is not a row in the data")
    else:
        warns.append("no room declares 'THE JOB: **name**' — nothing to cross-check against the data")
        print("  warn  no room declares a bound job; the data-agreement check found nothing to verify")

    # 5 — the scenario's own verification scripts must still pass
    sd = os.path.join(base, "_scratch")
    vs = sorted(f for f in os.listdir(sd) if f.startswith("verify_") and f.endswith(".py")) if os.path.isdir(sd) else []
    for f in vs:
        rr = subprocess.run([sys.executable, os.path.join(sd, f)], capture_output=True, text=True, cwd=sd)
        ck(rr.returncode == 0 and "FAIL" not in rr.stdout, f"_scratch/{f} passes")
    ck(bool(vs), f"the scenario ships its own verification scripts ({len(vs)} found)")

    print()
    if fails:
        print(f"PREFLIGHT FAILED — {len(fails)} blocking issue(s). Art generation stays locked.")
        return 1
    rec = {"target": target, "hash": _hash(base), "warnings": len(warns),
           "override": os.environ.get("PREFLIGHT_OVERRIDE") == "1"}
    json.dump(rec, open(os.path.join(base, STAMP), "w"), indent=1)
    print(f"PREFLIGHT PASSED — stamped {STAMP}" + (f" ({len(warns)} non-blocking warning(s))" if warns else ""))
    print("Art generation is unlocked until scenario.json or the dataset changes.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1].strip("/")))
