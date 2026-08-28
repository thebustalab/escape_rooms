#!/usr/bin/env python3
"""
validate_keys.py — assert every pano scenario.json is in lockstep with decode_codes.R.

WHY: the browser codec (shared/codec.js) encodes, per BUILT room, the student's selected
MCQ option index (0-based). decoder/decode_codes.R grades a code by comparing that index to
the scenario key's `correct` vector. The player does NOT shuffle options, so the correct
index is fixed by scenario.json — and if scenario.json's `question.correct` values drift out
of sync with the decoder's `correct = c(...)` vector, grading silently mis-scores. This
script fails loudly on that drift. Run it before pushing the site.

What it checks, per rooms/<chapter>/<scenario>/scenario.json:
  - the ordered list of BUILT rooms' correct indices (a puzzle's question.correct; a
    console-check OR Type 4 pick-the-point room encodes answer=1 when solved) must EQUAL the
    `correct` vector of the decoder key whose scenario_id matches the scenario's id;
  - every correct index is within its options list;
  - no MCQ has duplicate option text (a duplicated option lets the correct index resolve to the wrong
    slot while still matching the decoder number — the hawaii room2 bug, 2026-07-22);
  - exactly one decoder key matches the scenario id (else: missing / ambiguous).

Soft (non-failing) WARN: a scenario whose built MCQ rooms all key to the same option index
(e.g. all 0) — an "always the same slot" tell; vary the correct position across rooms.
Counted over MCQ rooms ONLY. A console-`check` or pick-the-point room encodes answer=1 by
construction — there is no option list and nothing for a student to notice — so an all-console
scenario (wrangling/trees, dimensionality_reduction/henges) legitimately keys to c(1,1,1,1) and
used to trip this warning every run. A tell needs a chooser; only MCQs have one.

Non-failing SKIP: a freshly-scaffolded scenario with no built graded rooms yet (all stubs) has
no decoder key — that's added at wiring time — so it's skipped rather than failed.

Exit 0 if all scenarios pass; exit 1 on any hard failure. No dependencies (stdlib only);
run with python3.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../escape_rooms/decoder
ROOT = HERE.parent                               # .../escape_rooms
DECODER = HERE / "decode_codes.R"
ROOMS_GLOB = "rooms/*/*/scenario.json"


def _is_mcq(q):
    """True for a payload the student answers by PICKING AN OPTION — the only kind whose correct
    index is a position a student could learn to exploit. A `check`/`pick` room encodes 1 because it
    was solved, not because anyone chose slot 1, so it can't carry a positional tell."""
    return "question" in q


def _graded_index(q, where, notes, vec):
    """Append the correct-index one graded puzzle payload `q` will encode.

    Used by the dynamic-queue path. The room path below keeps its own inline copy of these rules
    deliberately: it is the long-standing, well-tested path and was left byte-identical so this
    change cannot alter any existing scenario's key. If the two ever drift, reconcile them here."""
    if "question" in q:                       # MCQ: encoded answer = chosen index
        opts, c = q["question"].get("options", []), q["question"].get("correct")
        # Duplicate options are always a bug: the codec records the *index*, so if two options carry
        # the same text the correct index can silently resolve to the wrong (or a duplicated) slot —
        # exactly the hawaii room2 failure (2026-07-22), which passed the index-vs-key check because
        # scenario.json and the decoder agreed on the number while that slot held the wrong text.
        dupes = sorted({o for o in opts if opts.count(o) > 1})
        if dupes:
            notes.append(f"{where} has duplicate MCQ option(s): {', '.join(dupes)} "
                         f"— the correct index may resolve to the wrong text")
        if not isinstance(c, int) or not (0 <= c < len(opts)):
            notes.append(f"{where} correct index {c} out of range (0..{len(opts)-1})")
            vec.append(None)
        elif dupes:
            vec.append(None)                  # structural fail already noted; skip the vector compare
        else:
            vec.append(c)
    elif "check" in q:                        # console-check: solved encodes answer = 1
        vec.append(1)
    elif "pick" in q:                         # Type 4 pick-the-point: solved encodes answer = 1
        vec.append(1)
    else:
        notes.append(f"{where} has neither a question, a check nor a pick")
        vec.append(None)


def scenario_expected(doc):
    """Ordered correct-index vector the codec will encode for this scenario's BUILT rooms."""
    # DYNAMIC PUZZLE QUEUE (shared/puzzle_queue.js): when a scenario authors `puzzleQueue`, the
    # codec emits one step per LADDER RUNG in QUEUE order, not one per room in room order — because
    # the room that serves rung k differs between students, so a room-ordered key cannot grade
    # anything. Derive the key from the queue instead, and ignore the rooms entirely.
    queue = doc.get("puzzleQueue")
    if isinstance(queue, list) and queue:
        vec, notes = [], []
        n_mcq = 0
        for i, q in enumerate(queue):
            _graded_index(q, f"puzzleQueue[{i}]", notes, vec)
            n_mcq += _is_mcq(q)
        return vec, notes, n_mcq, []

    vec, notes, n_mcq, ungraded = [], [], 0, []
    for r in doc.get("rooms", []):
        if not r.get("built"):
            continue
        if r.get("phase") == "escape":
            # ESCAPE-objective rooms (two-phase design, 2026-07-17) are ungraded and deliberately
            # excluded from the submission codec by shared/pano-player.js mintCode(); skip them here
            # too so the decoder key stays in lockstep with the ANALYSIS rooms only.
            continue
        puzzles = [h for h in r.get("hotspots", []) if h.get("type") == "puzzle"]
        if not puzzles:
            # An intentional ungraded room takes no codec slot (mintCode keys its steps off `roomResults`,
            # so a room the student never solves in simply never contributes), which means such a room can
            # NEVER put the code out of lockstep with the key. Examples that are all deliberate: a
            # pre-awakened orientation room with only a lock (henges/beach); a pure JUNCTION whose only
            # control is a world-state `dial` (a trees monorail car); a CLUE room carrying evidence the
            # player needs later (Egypt's nine seal rooms, temple's galleries); and a plain PASSAGE with
            # nothing but doors (Egypt's `boat` crossing, temple's `root_crawl`).
            #
            # This used to FAIL and append None — which was wrong twice over (2026-08-28). It cannot
            # mis-grade, so failing overstated it; and the None then hit `if None in exp: continue` below,
            # which SKIPPED THE KEY COMPARISON FOR THE WHOLE SCENARIO. Egypt and temple were flagged this
            # way, so their decoder keys were never actually checked — the guard was silently not guarding.
            # Now: skip the slot (matching the codec), and WARN only for a room with no authored content at
            # all, which is the one case that really might be a forgotten puzzle.
            kinds = {h.get("type") for h in r.get("hotspots", [])}
            if r.get("preAwakened") or kinds & {"lock", "dial", "clue", "grid", "ledger"}:
                continue
            ungraded.append(f"built room '{r.get('key')}' has no puzzle and no authored content "
                            f"(only {', '.join(sorted(k for k in kinds if k)) or 'nothing'}) — "
                            f"intentional passage, or a forgotten puzzle?")
            continue
        q = puzzles[0]
        n_mcq += _is_mcq(q)                       # only MCQ slots can carry a positional tell
        if "question" in q:                       # MCQ: encoded answer = chosen index
            opts, c = q["question"].get("options", []), q["question"].get("correct")
            # Duplicate options are always a bug: the codec records the *index*, so if two options carry
            # the same text the correct index can silently resolve to the wrong (or a duplicated) slot —
            # exactly the hawaii room2 failure (2026-07-22), which passed the index-vs-key check because
            # scenario.json and the decoder agreed on the number while that slot held the wrong text.
            dupes = sorted({o for o in opts if opts.count(o) > 1})
            if dupes:
                notes.append(f"room '{r.get('key')}' has duplicate MCQ option(s): {', '.join(dupes)} "
                             f"— the correct index may resolve to the wrong text")
            if not isinstance(c, int) or not (0 <= c < len(opts)):
                notes.append(f"room '{r.get('key')}' correct index {c} out of range (0..{len(opts)-1})")
                vec.append(None)
            elif dupes:
                vec.append(None)                  # structural fail already noted; skip the vector compare
            else:
                vec.append(c)
        elif "check" in q:                        # console-check: solved encodes answer = 1
            vec.append(1)
        elif "pick" in q:                         # Type 4 pick-the-point: solved encodes answer = 1
            vec.append(1)                          # (graded like a check — see notes/puzzle_types_design_notes.md)
        else:
            notes.append(f"room '{r.get('key')}' puzzle has neither question, check, nor pick")
            vec.append(None)
    return vec, notes, n_mcq, ungraded


def decoder_keys(text):
    """Map scenario_id -> list of (key_name, correct_vector) parsed from decode_codes.R."""
    # boundaries: every top-level `NAME <- list(` / `NAME <- function`
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'(?m)^(\w+)\s*<-\s*(?:list|function)\s*\(', text)]
    by_id = {}
    for i, (pos, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        block = text[pos:end]
        sid = re.search(r'scenario_id\s*=\s*(\d+)', block)
        cor = re.search(r'correct\s*=\s*c\(([^)]*)\)', block)
        if not sid or not cor:
            continue
        vec = [int(x) for x in re.findall(r'-?\d+', cor.group(1))]
        by_id.setdefault(int(sid.group(1)), []).append((name, vec))
    return by_id


def main():
    keys = decoder_keys(DECODER.read_text())
    scenarios = sorted(ROOT.glob(ROOMS_GLOB))
    # Optional `chapter/scenario` filters (2026-08-28). Default is UNCHANGED — every scenario, exit 1 on
    # any failure — because that is the pre-push guard the canon tells you to run. The filter exists so a
    # go/no-go check can ask the narrower question "are the scenarios students will actually open sound?"
    # without an in-development scenario's known-acceptable state holding the verdict permanently red.
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]
    if wanted:
        keep = {w.strip("/") for w in wanted}
        scenarios = [p for p in scenarios
                     if "%s/%s" % (p.parent.parent.name, p.parent.name) in keep]
        if not scenarios:
            print("no scenario.json matched:", ", ".join(sorted(keep)))
            return 1
    if not scenarios:
        print("no scenario.json found under", ROOMS_GLOB)
        return 1

    failures, warnings = 0, 0
    for path in scenarios:
        rel = path.relative_to(ROOT)
        doc = json.loads(path.read_text())
        sid = doc.get("id")
        exp, notes, n_mcq, ungraded = scenario_expected(doc)

        for n in notes:
            print(f"FAIL  {rel}: {n}")
            failures += 1
        for n in ungraded:                        # cannot mis-grade — advisory, and never gates
            print(f"WARN  {rel}: {n}")
            warnings += 1

        # A freshly-scaffolded scenario (all rooms still stubs) has no built graded rooms yet, so it
        # legitimately has no decoder key — the key is added at wiring time (see the design skill). Skip
        # the key requirement until at least one graded room is built; a scenario with built rooms but a
        # structural problem still fails above (notes populated).
        if not exp and not notes:
            print(f"SKIP  {rel}: id {sid} — no built graded rooms yet (decoder key added at wiring)")
            continue

        matches = keys.get(sid, [])
        if not matches:
            print(f"FAIL  {rel}: scenario id {sid} has no matching decoder key in decode_codes.R")
            failures += 1
            continue
        if len(matches) > 1:
            print(f"FAIL  {rel}: scenario id {sid} matches multiple decoder keys "
                  f"({', '.join(n for n, _ in matches)}) — ambiguous")
            failures += 1
            continue

        key_name, key_vec = matches[0]
        if None in exp:
            continue                              # already reported a structural fail above
        if exp != key_vec:
            print(f"FAIL  {rel}: correct vector {exp} != {key_name} correct = c({', '.join(map(str, key_vec))})")
            failures += 1
            continue

        # Only an MCQ scenario can have an "always the same slot" tell — see _is_mcq. A console/pick
        # scenario keys to all-1s structurally, so warning on it is pure noise (2026-08-27).
        if exp and len(set(exp)) == 1 and len(exp) > 1 and n_mcq > 1:
            print(f"WARN  {rel}: all {n_mcq} built MCQ rooms key to index {exp[0]} — vary the correct position (tell)")
            warnings += 1
        print(f"PASS  {rel}: id {sid}, {key_name} correct = c({', '.join(map(str, exp))})")

    print(f"\n{len(scenarios)} scenario(s): {failures} failure(s), {warnings} warning(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
