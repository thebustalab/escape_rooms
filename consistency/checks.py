"""Repo-local custom consistency checks for the escape rooms.

Each function takes the engine's Ctx (see Utilities/consistency_audit/consistency_audit.py)
and returns a list of finding dicts via ctx.finding(target, locator, message, ...).
Ctx gives: .targets (list of {relpath, path, data}), .repo_root, .check.
"""
import os
import subprocess


def _built_puzzle_corrects(scenario):
    """In room order, the `correct` index of each built room's first MCQ puzzle."""
    out = []
    for room in scenario.get("rooms", []):
        if not room.get("built"):
            continue
        for hs in room.get("hotspots", []):
            if hs.get("type") == "puzzle" and isinstance(hs.get("question"), dict) \
                    and "correct" in hs["question"]:
                out.append((room.get("key"), hs["question"]["correct"]))
                break
    return out


def check_correct_not_all_same_slot(ctx):
    """Flag a scenario whose built MCQ rooms all park the correct answer at one index (a tell)."""
    out = []
    for t in ctx.targets:
        pairs = _built_puzzle_corrects(t["data"])
        idxs = [i for _, i in pairs]
        if len(idxs) > 1 and len(set(idxs)) == 1:
            out.append(ctx.finding(
                t["relpath"], "$.rooms[*].hotspots(puzzle).question.correct",
                "All %d built rooms put the correct answer at index %d — vary it (a tell)."
                % (len(idxs), idxs[0])))
    return out


def check_codec_lockstep(ctx):
    """Delegate to decoder/validate_keys.py (JSON correct-indices vs the R decoder key).

    Best-effort: reuse the existing guard rather than duplicating its logic. A non-zero
    exit becomes one error finding; a missing script becomes an info finding.
    """
    script = os.path.join(ctx.repo_root, "decoder", "validate_keys.py")
    if not os.path.exists(script):
        return [ctx.finding("decoder/validate_keys.py", "$",
                            "Codec-lockstep guard not found; skipped.")]
    try:
        proc = subprocess.run(["python3", script], cwd=ctx.repo_root,
                              capture_output=True, text=True, timeout=120)
    except Exception as exc:  # noqa: BLE001 - report any runner failure as a finding
        return [ctx.finding("decoder/validate_keys.py", "$",
                            "Could not run codec-lockstep guard: %s" % exc)]
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()
        msg = tail[-1] if tail else "validate_keys.py failed"
        return [ctx.finding("decoder/validate_keys.py", "$",
                            "Codec lockstep FAILED: %s" % msg)]
    return []
