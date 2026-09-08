#!/usr/bin/env python3
"""run_all_tests.py — every escape-room test suite, one go/no-go.

Why this exists: the suites are scattered by language and location (node in `tests/`, Playwright in
`tests/e2e/`, unittest beside each harness, one per built scenario under `rooms/`, an R self-test in
`decoder/`, plus the standalone validators). Before a live class Lucas needs ONE answer — is it safe to
push — not a memory of eight commands. It backs the build_world console's "Run all tests" button and
runs standalone:

    python3 authoring_v2/run_all_tests.py            # everything (browser suites included, ~3-4 min)
    python3 authoring_v2/run_all_tests.py --fast     # skip Playwright (~20 s)
    python3 authoring_v2/run_all_tests.py --json     # machine-readable, for the harness

Exit code is 0 only when EVERY suite passes, so it drops straight into a pre-push check.

Design notes:
  * A suite that cannot run (no Rscript, no Playwright browsers) is reported SKIP, not PASS — a missing
    runner must never read as a green light. SKIPs are surfaced in the summary and make the verdict
    "GO (with skips)" rather than a clean GO.
  * Per-scenario `rooms/<ch>/<sc>/test_<name>.py` suites are DISCOVERED, not listed, so a new scenario
    is covered the day it is wired rather than whenever someone remembers to edit this file.
  * The validators are included because they are the guards that catch grading drift
    (`decoder/validate_keys.py`) and missing assets — the two failure modes that only show up in front
    of students.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # escape_rooms/
TESTS = os.path.join(ROOT, "tests")

# Scenarios whose assets must validate. `ready` ones are what students actually touch, so a failure
# there is a no-go; in-development ones are informational (they legitimately have gaps).
def _ready_scenarios():
    inv = os.path.join(ROOT, "rooms", "scenario_inventory.json")
    try:
        with open(inv, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception:                                     # noqa: BLE001 — no inventory → nothing to assert
        return []
    return ["%s/%s" % (s["chapter"], s["scenario"])
            for s in doc.get("scenarios", []) if s.get("status") == "ready"]


def _suites(fast=False):
    """(name, group, argv, cwd, needs) for every suite, in cheap-to-expensive order."""
    out = []
    add = lambda name, group, argv, cwd=ROOT, needs=None, advisory=False: out.append(
        {"name": name, "group": group, "argv": argv, "cwd": cwd, "needs": needs, "advisory": advisory})

    # --- guards: the two that catch silent grading/asset drift -------------------------------------
    # The VERDICT asks about the scenarios students will actually open, so the key guard is scoped to
    # `ready` ones. An in-development scenario legitimately has connective rooms with no puzzle (Egypt's
    # nine seal rooms), and letting that hold the light permanently red would train everyone to ignore
    # it — the one thing a go/no-go must never do. The full sweep still runs, as ADVISORY.
    ready = _ready_scenarios()
    if ready:
        add("decoder keys ↔ published scenarios", "guards",
            [sys.executable, "decoder/validate_keys.py"] + ready)
    add("decoder keys ↔ every scenario (advisory)", "guards",
        [sys.executable, "decoder/validate_keys.py"], advisory=True)
    add("key-guard's own regression suite", "guards", [sys.executable, "decoder/test_validate_keys.py"])
    for sc in ready:
        add("assets: %s" % sc, "guards", [sys.executable, "authoring_v2/validate_assets.py", sc])
    # ALSO run it with NO scenario filter. `validate_assets` guards its cross-scenario checks behind
    # `if not want:` — inventory freshness, duplicate codec ids, and the shared-engine `?v=` cache-token
    # coherence check — so a per-scenario loop alone NEVER runs them (found 2026-08-29). Advisory: an
    # in-development scenario can legitimately trip the per-room misses this full sweep also reports.
    add("assets: full sweep + cross-scenario checks (advisory)", "guards",
        [sys.executable, "authoring_v2/validate_assets.py"], advisory=True)
    # SEAM STAGE — every committed still's 360 wrap join, for the scenarios students open. This is here
    # because the seam was the one art property with no gate at all: it was documented as a technique in
    # three files, required by none, and beacons duly shipped twelve stills nobody had checked (2026-09-02).
    # A room is only clean once a HUMAN has accepted it — the metric screens, it cannot certify — so the
    # check asserts on the recorded `authoring.seam.accepted`, not on a score. Scoped to `ready` for the
    # same reason as the key guard: an in-development scenario legitimately has unaccepted rooms.
    for sc in ready:
        add("seams accepted: %s" % sc, "guards",
            [sys.executable, "authoring_v2/seam_check.py", "--chapter", sc.split("/")[0],
             "--scenario", sc.split("/")[1], "--require-accepted"])
    add("seams: full sweep (advisory)", "guards",
        [sys.executable, "authoring_v2/seam_check.py", "--all"], advisory=True)
    # Scene/spec sweep — ADVISORY, because several built scenarios carry known spec drift it reports.
    # It is here at all because its ROLE -> ENGINE TYPE check is the only corpus-wide guard against a
    # dead escape: temple's `ledger` was silently rewritten to `puzzle` by the box editor on 2026-08-27
    # and the escape became unclickable in play, with the check that would have caught it never run.
    add("scenes/specs ↔ committed hotspots (advisory)", "guards",
        [sys.executable, "authoring_v2/validate_scenes.py"], advisory=True)

    # --- unit: python ------------------------------------------------------------------------------
    # authoring_v2 only — the v1 harness was retired to z_authoring_v1/ on 2026-08-28 (its three suites
    # tested a server nothing launches any more; v2 carries every one of its endpoints).
    for p in sorted(glob.glob(os.path.join(ROOT, "authoring_v2", "test_*.py"))):
        rel = os.path.relpath(p, ROOT)
        add(rel, "python", [sys.executable, rel])

    # cinemagraph_tools was MISSING from this runner until 2026-09-06, which is the worst omission it
    # could have had: `test_cine_judge.py` exists specifically to pin verdicts this pipeline has got
    # wrong on real art, and `test_still_pins.py` pins the mask blackout — i.e. exactly the regressions
    # a go/no-go is for. They ran only when someone remembered to point pytest at that directory. Run
    # from their own directory: they import sibling modules (`cine_judge`, `motion_spec`) by bare name.
    for p in sorted(glob.glob(os.path.join(ROOT, "cinemagraph_tools", "test_*.py"))):
        add(os.path.relpath(p, ROOT), "python",
            [sys.executable, os.path.basename(p)], cwd=os.path.dirname(p))

    # --- per-scenario: discovered, so a new scenario is covered the day it is wired -----------------
    for p in sorted(glob.glob(os.path.join(ROOT, "rooms", "*", "*", "test_*.py"))):
        rel = os.path.relpath(p, ROOT)
        add(rel, "scenarios", [sys.executable, os.path.basename(p)], cwd=os.path.dirname(p))

    # --- unit: node --------------------------------------------------------------------------------
    node_files = sorted(os.path.basename(p) for p in
                        glob.glob(os.path.join(TESTS, "*.test.js")) + glob.glob(os.path.join(TESTS, "*.test.mjs")))
    if node_files:
        add("node unit suites (%d files)" % len(node_files), "node",
            ["node", "--test"] + node_files, cwd=TESTS, needs="node")

    # --- codec: the JS↔R contract ------------------------------------------------------------------
    add("R codec self-test (decode_codes.R)", "codec", ["Rscript", "decode_codes.R"],
        cwd=os.path.join(ROOT, "decoder"), needs="Rscript")

    # --- browser: the only suites that prove a student's actual path works --------------------------
    if not fast:
        add("Playwright end-to-end (browser)", "browser", ["npx", "playwright", "test", "--reporter=line"],
            cwd=TESTS, needs="npx")
    return out


_SUMMARY_PATTERNS = [
    r"^\s*(\d+)\s+passed\b",                       # playwright: "22 passed (2.2m)"
    r"^all tests passed \((\d+)\)",                # the harness suites' own line
    r"^# pass (\d+)",                              # node --test
    r"^Ran (\d+) tests?",                          # unittest
    r"^(\d+) scenario\(s\)",                       # validate_keys
]


def _one_line(text, ok):
    """The most informative single line from a suite's output — a count if it printed one."""
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    if not lines:
        return "no output"
    if not ok:                                     # on failure the LAST meaningful lines matter most
        tail = [l for l in lines if not l.startswith("[WebServer]")]
        return (tail[-1] if tail else lines[-1])[:200]
    for pat in _SUMMARY_PATTERNS:
        for l in reversed(lines):
            m = re.search(pat, l)
            if m:
                return l.strip()[:200]
    return lines[-1][:200]


def run(fast=False, on_event=None):
    """Run every suite. `on_event(dict)` is called as each finishes (the harness streams these)."""
    results, t0 = [], time.time()
    suites = _suites(fast)
    for i, s in enumerate(suites):
        rec = {"name": s["name"], "group": s["group"], "index": i + 1, "total": len(suites)}
        if s["needs"] and not shutil.which(s["needs"]):
            rec.update(status="skip", detail="%s not installed — suite NOT run" % s["needs"], seconds=0)
        else:
            t = time.time()
            try:
                p = subprocess.run(s["argv"], cwd=s["cwd"], capture_output=True, text=True, timeout=900)
                out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
                ok = p.returncode == 0
                # An advisory suite that fails is a WARN: surfaced in full, but it does not gate the push.
                rec.update(status="pass" if ok else ("warn" if s.get("advisory") else "fail"),
                           detail=_one_line(out, ok), seconds=round(time.time() - t, 1))
                if not ok:
                    rec["output"] = out[-4000:]        # enough tail to diagnose without flooding the UI
            except subprocess.TimeoutExpired:
                rec.update(status="fail", detail="timed out after 900 s", seconds=900)
            except Exception as e:                      # noqa: BLE001 — a runner that dies is a FAIL, not a pass
                rec.update(status="fail", detail="could not run: %s" % e, seconds=round(time.time() - t, 1))
        results.append(rec)
        if on_event:
            on_event(rec)
    failed = [r for r in results if r["status"] == "fail"]
    skipped = [r for r in results if r["status"] == "skip"]
    warned = [r for r in results if r["status"] == "warn"]
    return {
        "verdict": "no-go" if failed else ("go-with-skips" if skipped else "go"),
        "passed": len([r for r in results if r["status"] == "pass"]),
        "failed": len(failed), "skipped": len(skipped), "warned": len(warned),
        "seconds": round(time.time() - t0, 1), "fast": bool(fast), "results": results,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fast", action="store_true", help="skip the Playwright browser suites")
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    a = ap.parse_args()
    live = not a.json
    if live:
        print("Running escape-room test suites%s…\n" % (" (fast: no browser)" if a.fast else ""), flush=True)
    mark = {"pass": "ok  ", "fail": "FAIL", "skip": "skip", "warn": "warn"}
    summary = run(fast=a.fast, on_event=(lambda r: print(
        "  %s [%d/%d] %-46s %s" % (mark[r["status"]], r["index"], r["total"], r["name"][:46], r["detail"]),
        flush=True)) if live else None)
    if a.json:
        print(json.dumps(summary, indent=1))
    else:
        print("\n%s — %d passed, %d failed, %d warned, %d skipped in %.0f s" % (
            {"go": "GO", "go-with-skips": "GO (with skips — a suite did not run)", "no-go": "NO-GO"}[summary["verdict"]],
            summary["passed"], summary["failed"], summary["warned"], summary["skipped"], summary["seconds"]))
        for r in summary["results"]:
            if r["status"] in ("fail", "warn"):
                print("\n--- %s ---\n%s" % (r["name"], r.get("output", r["detail"])))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
