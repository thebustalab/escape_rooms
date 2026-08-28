#!/usr/bin/env python3
"""validate_story.py — check every player-facing string against the VETTED LANDING STORY.

The last action of the harness's **Story** stage. The landing card is settled in stage 1 ("Concept,
landing & world"); everything else the player reads is authored in stage 2; this is the gate between
stage 2 and the rest of the build.

WHY IT EXISTS (2026-08-27). The landing story is the ONLY place a term can be established — it is the
first and often the only thing a player reads before the world starts talking to them. When the opening
is rewritten, downstream text that leaned on the old wording is left referring to something that no
longer exists, and nothing catches it: the JSON is valid, the scene validator is happy, the room plays.

Concretely: temple's opening was rewritten and stopped naming a rite called "the Closing". A hand
sweep for orphaned terms came back CLEAN — and was wrong. The reference was alive in
`hotspots[].question.prompt`, one level deeper than the sweep walked. That is the failure this file
exists to make impossible.

TWO CHECKS, and the first one is the point:

  1. COVERAGE. Enumerate every player-facing string WITH ITS JSON PATH — including the nested ones a
     hand pass forgets: `question.prompt`, every string in `question.feedback.wrong[]`,
     `question.feedback.correct`, ledger `prompt`/`rows[].label`/`feedback.*`, lock `feedback.*`,
     `entry.title`/`entry.text`, `done`/`escapeDone`, `enterLabel`, every hotspot `label` and `body`,
     and `lockedBody`. Printed as a tally so an unscanned field is VISIBLE rather than assumed.

  2. DROPPED TERMS — the precise check, and the one that FAILS. The landing story is snapshotted when
     it is vetted (`.vetted_story.txt`, written by --accept). On every later run the current opening is
     diffed against that snapshot: a distinctive term that WAS in the vetted opening, is NOT in the
     current one, and is STILL used downstream is a genuine orphan — the exact shape of the temple
     "Closing" break. Near-zero false positives, because it keys on an actual edit rather than guessing
     which nouns need establishing.

  2b. DEFINITE REFERENCE (advisory only). `the <Capitalised…>` whose words never appear in the opening.
     Tried as a FAIL first and it was far too blunt — it flags "the Noatak", "the Tukey", "the Anchor",
     all legitimate proper nouns a room may introduce itself. Kept as a review list, never a gate.

  3. CLOCK DRIFT (advisory). Time-of-day words used downstream that the landing story does not use —
     an opening that says "midday" and a finish screen that says "dawn" is a contradiction no schema
     check can see.

Run:  python3 authoring_v2/validate_story.py                       # every scenario
      python3 authoring_v2/validate_story.py hierarchical_clustering/temple
Tests: python3 authoring_v2/test_validate_story.py
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOMS = os.path.join(os.path.dirname(HERE), "rooms")

TIME_WORDS = {"dawn", "daybreak", "sunrise", "morning", "midday", "noon", "zenith", "afternoon",
              "dusk", "sunset", "twilight", "evening", "night", "midnight", "nightfall"}

# Words that follow "the" and are capitalised but are ordinary title-case scenery, not a named
# institution the opening must establish.
STOPHEADS = {"East", "West", "North", "South", "Register", "Registers"}

# Ordinary words that survive the 4-letter filter and would otherwise make every reword look like a
# dropped term. Only DISTINCTIVE vocabulary should gate a build.
COMMON = {"that", "this", "with", "from", "have", "here", "your", "them", "they", "when", "what",
          "which", "were", "will", "been", "into", "each", "then", "than", "some", "only", "over",
          "must", "more", "most", "both", "every", "still", "there", "their", "would", "could",
          "before", "after", "until", "while", "these", "those", "where", "about", "again", "last",
          "left", "long", "take", "takes", "does", "said", "says", "one", "two", "the"}


def strip_html(t):
    return re.sub(r"<[^>]+>", " ", str(t or ""))


def walk_text(doc):
    """Every player-facing string, with its JSON path. THE COVERAGE GUARD — if a field is missing from
    this walker it is invisible to the check, so it is enumerated explicitly rather than by recursion
    over unknown keys."""
    def emit(path, val):
        if isinstance(val, str) and val.strip():
            yield path, val

    for f in ("story", "enterLabel", "title", "subtitle"):
        yield from emit("scenario.%s" % f, doc.get(f))
    for f in ("done", "escapeDone", "debrief"):
        blk = doc.get(f)
        # `done`/`escapeDone` are usually {title, body} but a bare STRING is also valid and shipped
        # (dimensionality_reduction/clouds) — assuming the dict form crashed the whole corpus sweep.
        if isinstance(blk, str):
            yield from emit("scenario.%s" % f, blk)
        elif isinstance(blk, dict):
            for k in ("title", "body", "intro"):
                yield from emit("scenario.%s.%s" % (f, k), blk.get(k))

    for r in doc.get("rooms", []):
        rk = r.get("key", "?")
        yield from emit("%s.title" % rk, r.get("title"))
        yield from emit("%s.debrief" % rk, r.get("debrief"))
        e = r.get("entry")
        if isinstance(e, str):
            yield from emit("%s.entry" % rk, e)
        elif isinstance(e, dict):
            for k in ("title", "text", "body", "button"):
                yield from emit("%s.entry.%s" % (rk, k), e.get(k))
        for h in (r.get("hotspots") or []) + (r.get("plannedHotspots") or []):
            if not isinstance(h, dict):
                continue
            hid = h.get("id") or h.get("label") or "?"
            base = "%s/%s" % (rk, hid)
            for k in ("label", "body", "prompt", "lockedBody", "caption", "empty", "hint"):
                yield from emit("%s.%s" % (base, k), h.get(k))
            for i, o in enumerate(h.get("options") or []):
                yield from emit("%s.options[%d]" % (base, i), o if isinstance(o, str) else o.get("label"))
            for i, row in enumerate(h.get("rows") or []):
                yield from emit("%s.rows[%d].label" % (base, i),
                                row.get("label") if isinstance(row, dict) else row)
            # the nested block a hand sweep forgets
            q = h.get("question") or {}
            yield from emit("%s.question.prompt" % base, q.get("prompt"))
            for i, o in enumerate(q.get("options") or []):
                yield from emit("%s.question.options[%d]" % (base, i), o)
            for src, tag in ((q.get("feedback") or {}, "question.feedback"),
                             (h.get("feedback") or {}, "feedback")):
                for k, v in src.items():
                    if isinstance(v, str):
                        yield from emit("%s.%s.%s" % (base, tag, k), v)
                    elif isinstance(v, list):
                        for i, s in enumerate(v):
                            yield from emit("%s.%s.%s[%d]" % (base, tag, k, i), s)


def content_words(phrase):
    return [w.lower() for w in re.findall(r"[A-Za-z']+", phrase)
            if w.lower() not in {"the", "of", "a", "an"}]


def check_scenario(path):
    doc = json.load(open(path, encoding="utf-8"))
    landing = strip_html(doc.get("story", ""))
    fails, warns = [], []
    if not landing.strip():
        return ["no landing `story` — nothing to check the rest of the text against"], [], 0

    land_words = set(w.lower() for w in re.findall(r"[A-Za-z']+", landing))
    items = [(p, t) for p, t in walk_text(doc) if not p.startswith("scenario.story")]

    # 2 — DROPPED TERMS: what the vetted opening had, this one lost, and the rooms still say.
    snap = os.path.join(os.path.dirname(path), ".vetted_story.txt")
    if os.path.isfile(snap):
        old = set(w.lower() for w in re.findall(r"[A-Za-z']{4,}", strip_html(open(snap, encoding="utf-8").read())))
        dropped = {w for w in old - land_words if w not in COMMON}
        for p_, raw in items:
            for w in sorted(dropped):
                if re.search(r"\b%s\b" % re.escape(w), strip_html(raw), re.I):
                    fails.append('%s: still says "%s", which the VETTED opening had and the current '
                                 "opening no longer establishes." % (p_, w))
    else:
        warns.append("no .vetted_story.txt snapshot — run with --accept once the landing card is "
                     "settled, so later edits can be diffed against it")

    # 2b — definite reference: advisory only (see the docstring; too blunt to gate on)
    seen = set()
    for p, raw in items:
        for m in re.finditer(r"\bthe ((?:[A-Z][a-z]+)(?: (?:of|the) [A-Z][a-z]+| [A-Z][a-z]+)*)",
                             strip_html(raw)):
            phrase = m.group(1)
            if phrase.split()[0] in STOPHEADS:
                continue
            cw = content_words(phrase)
            if cw and not any(w in land_words for w in cw):
                key = (phrase.lower(), p)
                if key in seen:
                    continue
                seen.add(key)
                warns.append('%s: "the %s" — definite reference; check the opening establishes it '
                             "(often a legitimate local proper noun)." % (p, phrase))

    # 3 — clock drift (advisory)
    land_times = {w for w in TIME_WORDS if w in land_words}
    for p, raw in items:
        used = {w for w in TIME_WORDS if re.search(r"\b%s\b" % w, strip_html(raw), re.I)}
        odd = used - land_times
        if odd and land_times:
            warns.append("%s: says %s, but the landing story's clock is %s"
                         % (p, "/".join(sorted(odd)), "/".join(sorted(land_times))))
    return fails, warns, len(items)


def accept(rel):
    """Snapshot the current landing story as the VETTED reference."""
    p = os.path.join(ROOMS, rel, "scenario.json")
    doc = json.load(open(p, encoding="utf-8"))
    snap = os.path.join(os.path.dirname(p), ".vetted_story.txt")
    open(snap, "w", encoding="utf-8").write(doc.get("story", ""))
    print("vetted landing story snapshotted -> %s (%d chars)" % (snap, len(doc.get("story", ""))))


def main():
    want = [a for a in sys.argv[1:] if a != "--accept"]
    if "--accept" in sys.argv:
        for rel in want:
            accept(rel)
        return 0
    bad = False
    for p in sorted(glob.glob(os.path.join(ROOMS, "*", "*", "scenario.json"))):
        rel = os.path.relpath(p, ROOMS).replace(os.sep + "scenario.json", "")
        if want and rel not in want:
            continue
        try:
            fails, warns, n = check_scenario(p)
        except Exception as e:                       # a malformed scenario must not kill the sweep
            print("ERROR %s: %s" % (rel, e)); bad = True; continue
        if not fails and not warns:
            print("PASS  %s  (%d player-facing strings checked)" % (rel, n)); continue
        print("----  %s  (%d player-facing strings checked)" % (rel, n))
        for f in fails:
            print("FAIL  %s" % f); bad = True
        for w in warns:
            print("warn  %s" % w)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
