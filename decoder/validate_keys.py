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

Soft (non-failing) WARN: a scenario whose built rooms all key to the same option index
(e.g. all 0) — an "always the same slot" tell; vary the correct position across rooms.

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


def scenario_expected(doc):
    """Ordered correct-index vector the codec will encode for this scenario's BUILT rooms."""
    vec, notes = [], []
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
            # An intentional ungraded room takes no codec slot (mintCode skips rooms with no roomResult),
            # so skip it here too: a pre-awakened orientation room with only a lock (henges/beach), OR a
            # pure JUNCTION room whose only control is a world-state `dial` — a monorail car with a
            # drive-lever switch-door (wrangling/trees, 2026-08-05), which routes but never grades. A built
            # non-escape room with a puzzle, a lock, a dial, or preAwakened set is fine; none of those is a mistake.
            has_lock = any(h.get("type") == "lock" for h in r.get("hotspots", []))
            has_dial = any(h.get("type") == "dial" for h in r.get("hotspots", []))
            if r.get("preAwakened") or has_lock or has_dial:
                continue
            notes.append(f"built room '{r.get('key')}' has no puzzle hotspot")
            vec.append(None)
            continue
        q = puzzles[0]
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
    return vec, notes


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
    if not scenarios:
        print("no scenario.json found under", ROOMS_GLOB)
        return 1

    failures, warnings = 0, 0
    for path in scenarios:
        rel = path.relative_to(ROOT)
        doc = json.loads(path.read_text())
        sid = doc.get("id")
        exp, notes = scenario_expected(doc)

        for n in notes:
            print(f"FAIL  {rel}: {n}")
            failures += 1

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

        if exp and len(set(exp)) == 1 and len(exp) > 1:
            print(f"WARN  {rel}: all built rooms key to index {exp[0]} — vary the correct position (tell)")
            warnings += 1
        print(f"PASS  {rel}: id {sid}, {key_name} correct = c({', '.join(map(str, exp))})")

    print(f"\n{len(scenarios)} scenario(s): {failures} failure(s), {warnings} warning(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
