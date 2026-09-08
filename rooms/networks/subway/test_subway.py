#!/usr/bin/env python3
"""test_subway.py — regression guards for networks/subway ("The Faintest Line").

Two halves, because this scenario has two independent sources of truth and each can break alone:

  DATA   — the four graded rungs are re-derived here from `data/lichen_expression.csv`. This is the
           bespoke half that cannot live in the central validator: each rung encodes its own question
           (a pairwise correlation, a one-vs-all threshold isolate, a module-abundance trap, and a
           degree-within-module boss) and only recomputing it proves the wired answer still holds.
  LAYOUT — the escape does NOT bind to the CSV. It binds to the RAIL LAYOUT: the player plots the hops
           they rode and reads the two ghost stations off a grid. So the escape's answer is pinned to
           the canonical A2 layout here (Halliwell E5, Cold Harbour I4), independently of the map
           renderer. `_scratch/verify_escape.py` carries the fuller construction proof — uniqueness,
           no-redundancy, decoy crossings, berth agreement — and is run from there; this file pins the
           answer itself, because _scratch is gitignored and never ships.

Run: python3 test_subway.py   (stdlib only, on purpose — the map renderer pulls in networkx and
matplotlib, and a plotting dep must never be able to fail the answer checks.)

THE QUEUE IS WHY THIS FILE LOOKS UNUSUAL. subway pins no puzzle to a room. Each driver's cab is a
`queue: true` SLOT and the graded content lives in `SCENARIO.puzzleQueue`, served next-unsolved-rung
first (`shared/puzzle_queue.js`), because the player roams a 13-platform network and nobody can predict
which cab they reach first. So the content checks read the QUEUE, and the decoder is keyed by RUNG.
Two consequences pinned below: a slot missing `queue: true` serves nothing at all (subway shipped that
way until 2026-09-07 with every other validator green), and the planned twin needs the flag too,
because a harness re-commit rebuilds hotspots from `plannedHotspots`.

SELF-ARMING CHECKS. Where a phase is genuinely still open the check reports PENDING rather than failing,
and the pending count is printed loudly at the end so it can never be mistaken for a pass. As of
2026-09-07 the only PENDING item is the unauditioned placeholder audio; the ride and the cinemagraph
subjects are Lucas's own work in progress and are deliberately not asserted here.

Failure modes it guards:
  - the CSV is regenerated or re-seeded and a rung's verified winner (XAN_4574 / XAN_6246 / XAN_1815 /
    XAN_1192) silently stops being the winner;
  - a winner's MARGIN collapses so the rung no longer has a single clean answer — the threshold rung's
    stable band (|r| 0.15 to 0.7569, NOT the 0.72-0.78 the design record claimed until 2026-09-07)
    narrows around the 0.75 the prompt states, or the boss's degree lead over the decoy becomes a tie;
  - the TAUGHT TRAP decays: the abundance shortcut (XAN_1815) must stay both the most abundant gene in
    the pigment module AND poorly connected, or rung 3 stops teaching the wrong lesson it exists to
    teach and the boss stops correcting it;
  - the boss's decoy (XAN_3514) stops being loud-but-peripheral, which is the whole shape of the boss;
  - the escape's ghost squares drift off E5/I4, or a real station moves into an answer square;
  - the codec id stops being 21 (a collision cross-decodes two scenarios' submission codes);
  - `status` is flipped to "ready" while any of the build's known gaps is still open;
  - once content lands: a `correct` index drifts off the data-supported option, or out of lockstep with
    decode_codes.R's NETWORKS_SUBWAY_KEY.
"""
import csv
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []
pending = []


def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def pend(msg):
    print("  --  PENDING: " + msg)
    pending.append(msg)


# ── the data ─────────────────────────────────────────────────────────────────────────────────────
rows = list(csv.DictReader(open(os.path.join(HERE, "data", "lichen_expression.csv"), encoding="utf-8")))
expr = {}
for r in rows:
    expr.setdefault(r["gene"], {})[r["sample_id"]] = float(r["expression"])
genes = sorted(expr)
samples = sorted({r["sample_id"] for r in rows})

CUTOFF = 0.75
doc = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
rooms = {r["key"]: r for r in doc["rooms"]}


def pearson(a, b):
    xa = [expr[a][s] for s in samples]
    xb = [expr[b][s] for s in samples]
    n = len(xa)
    ma, mb = sum(xa) / n, sum(xb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(xa, xb))
    sa = math.sqrt(sum((x - ma) ** 2 for x in xa))
    sb = math.sqrt(sum((y - mb) ** 2 for y in xb))
    return cov / (sa * sb)


R = {a: {b: pearson(a, b) for b in genes if b != a} for a in genes}
mean = {g: statistics.mean(expr[g].values()) for g in genes}


def degree(g, cutoff=CUTOFF):
    return sum(1 for h, r in R[g].items() if abs(r) > cutoff)


def neighbours(g, cutoff=CUTOFF):
    return {h for h, r in R[g].items() if abs(r) > cutoff}


print("networks/subway — the shape the DATA has to keep")
print("\n-- rung 1: the reference pair (pairwise correlation) --")
ranked = sorted(((abs(r), h) for h, r in R["XAN_4418"].items()), reverse=True)
check(ranked[0][1] == "XAN_4574",
      "XAN_4418's tightest partner is XAN_4574 (|r| %.3f; runner-up %s at %.3f)"
      % (ranked[0][0], ranked[1][1], ranked[1][0]))
check(ranked[0][0] / ranked[1][0] > 5,
      "the winner clears the runner-up by >5x (%.1fx) — one clean winner, not a near-tie"
      % (ranked[0][0] / ranked[1][0]))
check("XAN_1192" not in (ranked[0][1],),
      "the probe is a SATELLITE pair — it does not hand the player the boss (XAN_1192)")

print("\n-- rung 2: the control strand (threshold + one-vs-all) --")
isolates = [g for g in genes if degree(g) == 0]
check(isolates == ["XAN_6246"], "XAN_6246 is the SOLE isolate at |r|>%.2f (%s)" % (CUTOFF, isolates))
# THE STABLE BAND IS 0.15-0.75, NOT 0.72-0.78 (found 2026-09-07 by this test; the queue note and
# notes.md both claimed the wider band and both were corrected). XAN_6246's strongest tie to anything
# is |r| 0.10, so it is isolated under any sane cutoff; but the next-weakest genes sit at 0.7569
# (XAN_1815 — the TAUGHT TRAP) and 0.7590 (XAN_2781), so at 0.76 the room has THREE isolates and no
# single answer. The rung is safe because its prompt states |r|>0.75 explicitly — that is the whole
# point of the rung — but any hint that nudges a player to "about 0.8" breaks it, which is why the
# ceiling is pinned here.
best = {g: max(abs(v) for v in R[g].values()) for g in genes}
for c in (0.15, 0.40, 0.60, 0.72, 0.74, 0.75):
    check([g for g in genes if degree(g, c) == 0] == ["XAN_6246"],
          "still the sole isolate at cutoff %.2f — stable across the band the prompt lives in" % c)
check(best["XAN_6246"] < 0.2,
      "XAN_6246's strongest tie to anything is |r| %.3f — isolated by a mile, not by a hair"
      % best["XAN_6246"])
ceiling = min(best[g] for g in genes if g != "XAN_6246")
check(0.75 < ceiling < 0.76,
      "the band's CEILING is %.4f (the next-weakest gene's best tie) — above it the room gains a "
      "second isolate, so no hint may suggest a cutoff over 0.75" % ceiling)
joiners = sorted((best[g], g) for g in genes if g != "XAN_6246")[:2]
check([g for _, g in joiners] == ["XAN_1815", "XAN_2781"],
      "and the first two genes to join the isolates above the ceiling are XAN_1815 (%.4f) and "
      "XAN_2781 (%.4f) — the first of them is the TAUGHT TRAP, so a too-high cutoff would muddy "
      "rung 3 as well as rung 2" % (joiners[0][0], joiners[1][0]))

print("\n-- rung 3: the taught trap (module + abundance) --")
# The pigment module is what the player recovers from the correlation structure: the boss's own
# neighbourhood. Deriving it that way rather than hard-coding a gene list is the point — if the
# structure changes, the module changes with it and the trap has to survive the change.
module = neighbours("XAN_1192") | {"XAN_1192"}
loudest = max(module, key=lambda g: mean[g])
runner = max(module - {loudest}, key=lambda g: mean[g])
check(loudest == "XAN_1815",
      "the most abundant gene in the pigment module is XAN_1815 (%.0f vs %s at %.0f)"
      % (mean[loudest], runner, mean[runner]))
check(mean[loudest] / mean[runner] > 4,
      "and it wins on abundance by >4x (%.1fx) — the shortcut looks decisive, which is why it baits"
      % (mean[loudest] / mean[runner]))
check(degree("XAN_1815") == 1,
      "XAN_1815 has degree 1 — loud and peripheral, so the shortcut is WRONG (degree %d)"
      % degree("XAN_1815"))

print("\n-- rung 4: the boss (module + network position) --")
check(min(mean, key=lambda g: mean[g]) == "XAN_1192",
      "XAN_1192 is the LOWEST-expressed gene in the whole dataset (%.1f units, rank %d of %d)"
      % (mean["XAN_1192"], 1 + sorted(mean.values()).index(mean["XAN_1192"]), len(genes)))
in_module = sorted(((degree(g), g) for g in module), reverse=True)
check(in_module[0][1] == "XAN_1192",
      "XAN_1192 is the most connected gene in its module (degree %d vs %d for %s)"
      % (in_module[0][0], in_module[1][0], in_module[1][1]))
check(in_module[0][0] > in_module[1][0],
      "its degree lead is strict — no tie for the regulator")
check(neighbours("XAN_1192") == module - {"XAN_1192"},
      "it connects to EVERY other gene in the module — the hub, which is what 'regulator' means here")
loud = max(mean, key=lambda g: mean[g])
check(loud == "XAN_3514",
      "the decoy is the loudest gene in the transcriptome, XAN_3514 (%.0f units)" % mean[loud])
check(degree("XAN_3514") < degree("XAN_1192"),
      "and it is peripheral next to the answer (degree %d vs %d) — loud bystander, not regulator"
      % (degree("XAN_3514"), degree("XAN_1192")))
check(mean["XAN_3514"] / mean["XAN_1192"] > 50,
      "the boss's answer is %.0fx QUIETER than the decoy — abundance cannot find it"
      % (mean["XAN_3514"] / mean["XAN_1192"]))

print("\n-- the ladder escalates: one new move per rung, no plateau --")
# Each rung's move, as the analysis a player must add to the previous one. Named here so a future
# re-skin cannot quietly collapse two rungs onto the same move.
moves = ["pairwise correlation",
         "correlation + a threshold, applied one-vs-all",
         "threshold + module membership + abundance",
         "threshold + module membership + degree"]
check(len(set(moves)) == len(moves), "no two rungs run the same analysis")
for i in range(1, len(moves)):
    check(moves[i] != moves[i - 1], "rung %d is not a re-skin of rung %d" % (i + 1, i))
check(len(doc["puzzleQueue"]) == 4, "the queue is 4 rungs long (%d)" % len(doc["puzzleQueue"]))
for i, want in enumerate(["XAN_4574", "XAN_6246", "XAN_1815", "XAN_1192"]):
    note = doc["puzzleQueue"][i].get("note", "")
    check(want in note, "puzzleQueue[%d]'s design note still names %s as its answer" % (i, want))

print("\n-- the escape binds to the RAIL LAYOUT, not the CSV --")
# The canonical A2 layout: layout A with Fullers Cross moved to (7, 1) (Lucas, 2026-08-12).
# Transcribed from _scratch/verify_escape.py, which holds the construction proof.
GHOSTS = {"Halliwell": (6.0, 6.0), "Cold Harbour": (13.0, 4.0)}
POS = {"Kettle Yard": (2, 9), "Vat Row": (10, 3), "Skein Lane": (1, 5), "Teasel Green": (11, 7),
       "Tenter Fields": (4, 1), "Cropping Yard": (8, 11), "Gall Street": (10, 1),
       "Logwood Quay": (16, 7), "Saffron Hill": (16, 2), "Indigo Reach": (10, 6),
       "Alum Wharf": (0, 12), "Bleachfield": (14, 0.5), "Fullers Cross": (7, 1),
       "Ochre Steps": (18, 9), "Mordant Lane": (3, -2), "Scouring Bank": (11, 14),
       "Tannery Row": (7, -1), "Dyers Gate": (9, 9)}
GRID_ORIGIN, GRID_SQ = (-3.5, -3.5), 2.0


def gridref(p):
    c = int((p[0] - GRID_ORIGIN[0]) // GRID_SQ)
    r = int((p[1] - GRID_ORIGIN[1]) // GRID_SQ) + 1
    return "%s%d" % (chr(ord("A") + c), r)


check(gridref(GHOSTS["Halliwell"]) == "E5", "Halliwell reads E5 (got %s)" % gridref(GHOSTS["Halliwell"]))
check(gridref(GHOSTS["Cold Harbour"]) == "I4",
      "Cold Harbour reads I4 (got %s)" % gridref(GHOSTS["Cold Harbour"]))
for name, p in GHOSTS.items():
    dx = min((p[0] - GRID_ORIGIN[0]) % GRID_SQ, GRID_SQ - (p[0] - GRID_ORIGIN[0]) % GRID_SQ)
    dy = min((p[1] - GRID_ORIGIN[1]) % GRID_SQ, GRID_SQ - (p[1] - GRID_ORIGIN[1]) % GRID_SQ)
    check(min(dx, dy) >= 0.4,
          "%s sits %.2f clear of the nearest grid line — a player reading a border is never "
          "choosing between two squares" % (name, min(dx, dy)))
answer_squares = {"E5", "I4"}
intruders = sorted("%s@%s" % (s, gridref(p)) for s, p in POS.items() if gridref(p) in answer_squares)
check(not intruders, "no REAL station shares an answer square (%s)" % intruders)
check(doc.get("id") == 21, "codec id is 21 (got %r)" % doc.get("id"))

print("\n-- the promotion switch tells the truth --")
check(doc.get("status") in ("in_development", "ready"),
      "status is the in_development/ready SWITCH, not prose — the inventory and the newsletter "
      "dropdown both read it (got %r)" % str(doc.get("status"))[:40])
if doc.get("status") == "ready":
    check(os.path.exists(os.path.join(HERE, "play.html")),
          "a ready scenario has a play.html — the file students actually open")

print("\n-- sound: present everywhere, and no placeholder ships unheard --")
# Staged 2026-09-07 by REUSING verified-CC0 clips already in the tree rather than pulling 24 new files
# (see notes/solve_sounds.md -> subway). That cleared the silent-solve gap that shipped hawaii mute, but
# nobody has LISTENED to any of them in place, so each carries `needsReplacement`. The flag is the point:
# it lets the validator go green on COMPLETENESS while this check refuses PROMOTION until a human has
# been through them. Audition, then drop the flag on the ones that stay.
placeholders = []
for r in doc["rooms"]:
    sfx = r.get("sfx") or []
    if isinstance(sfx, dict):
        sfx = [sfx]
    check(bool([x for x in sfx if x and x.get("src")]), "%s has an ambience bed" % r["key"])
    placeholders += [(r["key"], x["src"]) for x in sfx if x.get("needsReplacement")]
    for h in r.get("hotspots") or []:
        if h.get("type") in ("puzzle", "lock", "ledger", "grid"):
            ss = h.get("solveSfx")
            check(bool(ss and ss.get("src")),
                  "%s/%s (%s) has a solveSfx — a silent solve is the hawaii bug"
                  % (r["key"], h.get("id"), h.get("type")))
            if ss and ss.get("needsReplacement"):
                placeholders.append((r["key"], ss["src"]))
if doc.get("status") == "ready":
    check(not placeholders,
          "no `needsReplacement` audio survives into a READY scenario (%d still flagged)"
          % len(placeholders))
elif placeholders:
    pend("%d audio cue(s) are unauditioned placeholders — listen in place, then drop "
         "`needsReplacement`; promotion is blocked until they are gone" % len(placeholders))

print("\n-- shipped content: the DYNAMIC QUEUE is where subway's puzzles live --")
# THE ARCHITECTURAL FACT that shapes every check below: subway does not pin a puzzle to a room. Each
# driver's cab is a `queue:true` SLOT and the content lives in `SCENARIO.puzzleQueue`, served next-rung-
# first (shared/puzzle_queue.js), because the player roams and no one can predict which cab they reach
# first. So the graded content is checked against the QUEUE, and the decoder is keyed by rung, not room.
SLOTS = ["car_madder", "car_woad", "car_weld", "car_verdigris", "car_lampblack"]
queue = doc.get("puzzleQueue") or []
check(len(queue) == 4, "the queue holds all four rungs (%d)" % len(queue))
for rk in SLOTS:
    h = next((x for x in rooms[rk]["hotspots"] if x.get("type") == "puzzle"), None)
    check(h is not None, "%s carries its driving-desk gate" % rk)
    if h is None:
        continue
    # Without `queue:true` the engine never reaches resolveSlot, so the desk serves NOTHING and the
    # whole authored ladder is unreachable while every other validator stays green. It shipped that way
    # until 2026-09-07, which is why this is pinned per slot.
    check(h.get("queue") is True, "%s/%s is flagged queue:true — the slot actually serves the ladder"
          % (rk, h.get("id")))
    ph = next((x for x in (rooms[rk].get("plannedHotspots") or []) if x.get("type") == "puzzle"), None)
    check(ph is not None and ph.get("queue") is True,
          "%s's PLANNED twin also carries queue:true — a harness re-commit rebuilds hotspots from the "
          "planned manifest and would otherwise silently drop it" % rk)

print("\n-- each rung keys to the option the DATA supports --")
# The load-bearing seam: the option list is prose, so a reorder during editing silently re-keys a rung
# while every schema check stays green. These recompute the winner and compare it to option[correct].
WINNER = ["XAN_4574", "XAN_6246", "XAN_1815", "XAN_1192"]
for i, want in enumerate(WINNER):
    if i >= len(queue):
        break
    q = (queue[i] or {}).get("question") or {}
    opts = q.get("options") or []
    if not opts:
        pend("puzzleQueue[%d] has no question yet" % i)
        continue
    ci = q.get("correct")
    check(isinstance(ci, int) and 0 <= ci < len(opts), "rung %d correct index in range" % (i + 1))
    if isinstance(ci, int) and 0 <= ci < len(opts):
        check(opts[ci] == want,
              "rung %d keys to %s, which is what the data gives (option %d of %d)"
              % (i + 1, want, ci, len(opts)))
    check(len(opts) >= 6, "rung %d has >=6 options (%d)" % (i + 1, len(opts)))
    check(len(set(opts)) == len(opts), "rung %d has no duplicate option text" % (i + 1))
    # Every distractor must be a REAL gene from the dataset — a "plausible wrong analysis" result, not
    # invented noise. This is the cheapest guard against a typo'd gene name nobody can ever select.
    strays = [o for o in opts if o not in genes]
    check(not strays, "rung %d's options are all real genes from the CSV (strays: %s)" % (i + 1, strays))
    fb = q.get("feedback") or {}
    check("reveal" not in fb, "rung %d has no reveal" % (i + 1))
    check(len(fb.get("wrong") or []) >= 3, "rung %d has >=3 escalating hints" % (i + 1))
    check(want in (fb.get("correct") or ""),
          "rung %d's correct-feedback NAMES the answer — it is auto-logged to the field notebook "
          "verbatim, and the notebook is what the player reads back" % (i + 1))
    # axis-orientation-agnostic hints: students may map either axis, so directional language is a bug
    bad = [w for w in (fb.get("wrong") or [])
           if re.search(r"\b(left|right|leftmost|rightmost|furthest (?:to the )?(?:left|right))\b", w, re.I)]
    check(not bad, "rung %d's hints use no left/right language (%d offender(s))" % (i + 1, len(bad)))
    check((queue[i].get("starterCode") or "").strip() == "lichen_expression",
          "rung %d's starterCode is the bare data-object name only (%r)"
          % (i + 1, queue[i].get("starterCode")))
    check(not re.search(r"cor\(|filter\(|group_by|arrange\(|ggplot|aes\(", q.get("prompt", "")),
          "rung %d's prompt leaks no code" % (i + 1))

print("\n-- the taught trap survives contact with the ladder --")
if len(queue) == 4:
    r3 = (queue[2].get("question") or {}); r4 = (queue[3].get("question") or {})
    o3, o4 = r3.get("options") or [], r4.get("options") or []
    # The trap only teaches if the shortcut is OFFERED at the boss and refused there. If XAN_1815
    # stopped being an option in rung 4, the boss would no longer correct the lesson rung 3 taught.
    check("XAN_1815" in o4, "rung 4 still OFFERS the shortcut answer XAN_1815 as a distractor")
    check(o4[r4["correct"]] != "XAN_1815", "and rung 4 does NOT key to it")
    check("XAN_3514" in o4, "rung 4 offers the loud bystander XAN_3514 — the decoy the boss rules out")
    check("XAN_3514" in o3, "rung 3 offers XAN_3514 too — the 'forgot to filter to the module' mistake")

print("\n-- the escape lock --")
lock = next((h for h in rooms["ochre_hall"]["hotspots"] if h.get("type") == "lock"), None)
check(lock is not None, "ochre_hall carries the traffic-office lock")
if lock:
    # Re-derive the answer from the LAYOUT rather than trusting the string: lower letter first, which is
    # the convention the filing card states in-world.
    want = "".join(sorted([gridref(GHOSTS["Halliwell"]), gridref(GHOSTS["Cold Harbour"])]))
    check(lock.get("answer") == want,
          "the lock's answer is the two ghost squares, lower letter first: %s" % want)
    check(lock.get("length") == len(want), "and its length matches (%r)" % lock.get("length"))
    check(bool(lock.get("endsEscape")),
          "the lock is flagged endsEscape — ochre_hall is also the lampblack boarding platform and the "
          "player's first room, so it is NOT phase:'escape' and the terminal flag is what ends the escape")
    fbl = lock.get("feedback") or {}
    check(bool(fbl.get("correct")) and bool(fbl.get("wrong")), "the lock has correct + wrong feedback")
    # NO PARTIAL FEEDBACK is the escape's whole defence: the pair must be guessed at once and cannot be
    # searched one reference at a time. Wrong-feedback that named a half would quietly destroy that.
    check(not re.search(r"E5|I4|half|one of|first ref|second ref", fbl.get("wrong") or "", re.I),
          "and its wrong-feedback gives NO partial information — the pair cannot be binary-searched")
    # The entry convention has to be READABLE IN-WORLD or the player has the pair and not the order.
    # This is the Egypt playtest failure mode and no other check in this repo catches it.
    cards = [h for h in rooms["ochre_hall"]["hotspots"]
             if h.get("type") == "clue" and re.search(r"lower letter", str(h.get("body")), re.I)]
    check(bool(cards),
          "some clue in ochre_hall states the filing convention (both references, one entry, lower "
          "letter first) — without it the escape is unsolvable with the right answer in hand")
    sheets = [h for h in rooms["ochre_hall"]["hotspots"]
              if h.get("type") == "clue" and h.get("image")]
    check(bool(sheets), "and the carried survey sheet is present as a clue image")
    for sh in sheets:
        check("network_map" not in (sh.get("image") or ""),
              "the sheet is NOT network_map.png — that is the ANSWER KEY and would end the escape on "
              "sight (%s)" % sh.get("image"))
        img = os.path.join(HERE, sh["image"])
        check(os.path.exists(img), "the sheet's image exists on disk (%s)" % sh["image"])
        check(bool(sh.get("pickup")), "the sheet is a PICKUP — the map is carried, not visited")

print("\n-- every clue says something --")
for r in doc["rooms"]:
    for h in r.get("hotspots") or []:
        if h.get("type") != "clue":
            continue
        check(bool((h.get("body") or "").strip()) or bool(h.get("image")),
              "%s/%s renders something" % (r["key"], h.get("id")))
        # A clue must never hand over a gene name — that is the analysis, done for the player.
        named = [g for g in WINNER if g in (h.get("body") or "")]
        check(not named, "%s/%s names no answer gene (%s)" % (r["key"], h.get("id"), named))

print("\n-- decoder lockstep: keyed by RUNG, not by room --")
dec = os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R")
src = open(dec, encoding="utf-8").read() if os.path.exists(dec) else ""
m = re.search(r"NETWORKS_SUBWAY_KEY\s*<-\s*list\((?:[^)]*?)correct\s*=\s*c\(([^)]*)\)", src, re.S)
if not m:
    pend("no NETWORKS_SUBWAY_KEY in decode_codes.R")
else:
    key = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
    wired = [(q.get("question") or {}).get("correct") for q in queue]
    check(key == wired, "decode_codes.R key %s matches the queue's correct indices %s" % (key, wired))
    check(len(set(key)) > 1,
          "the correct index VARIES across rungs (%s) — the player never sees options shuffled, so a "
          "constant index is a visible tell" % key)
    check(re.search(r"scenario_id\s*=\s*21", src) is not None, "the key declares scenario_id 21")
    # id 21 does not fit v1's 4-bit id nibble; a v1 mint would truncate 21 to 5 and mis-grade silently.
    check(re.search(r"encode_code\(version\s*=\s*2,\s*scenario_id\s*=\s*21", src) is not None,
          "the decoder self-test mints subway at VERSION 2 (id 21 overflows v1's 4-bit id field)")

print()
if pending:
    print("%d PENDING check(s) — these arm themselves as content lands; the scenario is NOT complete:"
          % len(pending))
    for p in pending:
        print("    - " + p)
    print()
print("%s — %d failure(s), %d pending" % ("FAILED" if fails else "ALL PASS", len(fails), len(pending)))
sys.exit(1 if fails else 0)
