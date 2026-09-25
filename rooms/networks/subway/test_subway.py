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
# COLUMNS RENAMED 2026-09-25 (Lucas): sample_id -> lichen_isolate, gene -> gene_id. The room asks the
# player to pass `gene_id` to runMatrixAnalysis's `columns_w_sample_ID_info`, which is correct — the
# genes ARE the samples of this analysis — but beside a column literally called `sample_id` it reads
# like a mistake. The names now say which axis is which.
rows = list(csv.DictReader(open(os.path.join(HERE, "data", "lichen_expression.csv"), encoding="utf-8")))
expr, norm = {}, {}
for r in rows:
    expr.setdefault(r["gene_id"], {})[r["lichen_isolate"]] = float(r["expression"])
    norm.setdefault(r["gene_id"], {})[r["lichen_isolate"]] = float(r["expression_normalized"])
genes = sorted(expr)
samples = sorted({r["lichen_isolate"] for r in rows})

# THE METRIC IS THE CHAPTER'S, NOT PEARSON'S (2026-09-25, Lucas). The room used to be graded on
# |r| > 0.75, but chapter 7 never teaches correlation: it teaches distance -> similarity
# (1 / (1 + distance) * 100) -> threshold -> network, and a student who followed the chapter could not
# reach any of these answers. The ladder is now stated and graded in that vocabulary, cutoff
# SIMILARITY > 7.8. Recomputed here rather than assumed, because the whole point of this file is to
# re-derive what the player derives.
#
# THE NORMALISATION LIVES IN THE DATA, and that is not a convenience — it is forced. A gene network puts
# the GENES in the rows, and `scale_variance` scales COLUMNS, so no argument a student could pass will
# put the genes on a common footing; unscaled, one gene averages 5644 units and another 71, and distance
# then sees abundance and nothing else. Requiring a hand-rolled scaling step before the pivot would be
# asking for a move chapter 7 does not teach. So `expression_normalized` ships in the CSV, standardised
# gene-wise and then isolate-wise in ONE pass — the second pass leaves every isolate column at exactly
# mean 0 / sd 1, which makes `scale_variance` a NO-OP, so TRUE, FALSE and the default all agree. Pinned
# below. This file therefore reads `expression_normalized` for the network and `expression` for
# abundance, exactly as the player does.
CUTOFF = 7.8
doc = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
rooms = {r["key"]: r for r in doc["rooms"]}


# The player's network is built from the SHIPPED normalised column, not from anything recomputed here.
# Reading it straight off disk is the point: if the CSV were ever regenerated wrongly, this file must
# fail rather than quietly re-derive a correct matrix of its own.
Z = {g: [norm[g][s] for s in samples] for g in genes}


def similarity(a, b):
    d = math.sqrt(sum((x - y) ** 2 for x, y in zip(Z[a], Z[b])))
    return 1 / (1 + d) * 100


R = {a: {b: similarity(a, b) for b in genes if b != a} for a in genes}
# THE FLOOR IS MEASURED, NOT DERIVED. Two genes with no relationship sit near 1/(1+sqrt(2(n-1))), but
# the one-pass normalisation leaves the gene rows at sd ~0.98 rather than exactly 1, so the analytic
# value (4.77) is not the floor this data actually has (4.15). Rung 1's and rung 2's hints quote the
# real one, so the real one is what gets pinned.
FLOOR = min(min(v.values()) for v in R.values())
mean = {g: statistics.mean(expr[g].values()) for g in genes}


def degree(g, cutoff=CUTOFF):
    return sum(1 for h, r in R[g].items() if r > cutoff)


def neighbours(g, cutoff=CUTOFF):
    return {h for h, r in R[g].items() if r > cutoff}


print("networks/subway — the shape the DATA has to keep")
print("\n-- the shipped normalisation: what makes scale_variance a no-op --")
# THE ONE INVARIANT THE WHOLE ARRANGEMENT RESTS ON. `expression_normalized` is standardised gene-wise
# and THEN isolate-wise. The second pass is not tidiness: it leaves every isolate COLUMN at mean 0 and
# sd 1, which is precisely the condition under which runMatrixAnalysis's `scale_variance = TRUE`
# (the DEFAULT for dist) changes nothing. That is what lets the room state one threshold and have it be
# right whether the player passes TRUE, passes FALSE, or passes nothing — which is the reason the room
# needs no step chapter 7 has not taught. Break this and the stated 7.8 silently stops being the right
# number for half the class.
# The ISOLATE axis is the one that must be EXACT — it went last, and it is the axis scale_variance
# touches. The GENE axis is standardised first and is then nudged by that final pass, so it lands close
# to but not exactly on mean 0 / sd 1; that is harmless (the metric only needs the genes COMPARABLE, not
# unit-variance) and is why the two tolerances differ by four orders of magnitude. Do not "fix" the gene
# tolerance by iterating the normalisation to convergence: that was tried, and the extra sweeps compress
# the structure until the usable band narrows from 0.72 wide to 0.51.
iso_cols = [[norm[g][sm] for g in genes] for sm in samples]
iso_mean = max(abs(statistics.mean(v)) for v in iso_cols)
iso_sd = max(abs(statistics.stdev(v) - 1) for v in iso_cols)
check(iso_mean < 1e-4 and iso_sd < 1e-4,
      "every isolate COLUMN is centred and scaled (worst |mean| %.2e, worst |sd-1| %.2e) — this is the "
      "no-op condition, and it is what makes scale_variance irrelevant" % (iso_mean, iso_sd))
gene_rows = [[norm[g][sm] for sm in samples] for g in genes]
gene_sd = [statistics.stdev(v) for v in gene_rows]
# The gene axis is guarded by RATIO, not by distance from 1. What matters is that no gene's spread
# dominates the distance calculation; after the final isolate pass the rows land at sd 0.78 to 1.21, a
# 1.5x spread, against the 80x spread in raw ABUNDANCE that made unnormalised distance useless. The
# bound is what the metric actually needs.
check(max(gene_sd) / min(gene_sd) < 2.0,
      "and no GENE row dominates the distances — row spreads run %.3f to %.3f, a %.2fx range, against "
      "the 80x range in raw abundance that made unnormalised distance unusable"
      % (min(gene_sd), max(gene_sd), max(gene_sd) / min(gene_sd)))
# ...and abundance must NOT be readable from it, or rung 3 could be answered off the wrong column.
nm = {g: statistics.mean(norm[g].values()) for g in genes}
check(max(abs(v) for v in nm.values()) < 0.05,
      "expression_normalized carries NO abundance — every gene averages ~0 on it (largest %.4f), so "
      "rung 3 has to go back to `expression`" % max(abs(v) for v in nm.values()))

print("\n-- rung 1: the reference pair (pairwise similarity) --")
ranked = sorted(((r, h) for h, r in R["XAN_4418"].items()), reverse=True)
check(ranked[0][1] == "XAN_4574",
      "XAN_4418's closest partner is XAN_4574 (similarity %.2f; runner-up %s at %.2f)"
      % (ranked[0][0], ranked[1][1], ranked[1][0]))
# MEASURE THE MARGIN ABOVE THE FLOOR, not as a raw ratio. 1/(1+d) is strongly compressive, so a pair at
# r 0.83 and a pair at r 0.08 score 10.90 and 4.96 — a ratio of only 2.2x that badly understates the
# separation, because 4.48 of both numbers is the score two UNRELATED genes get. Against the floor the
# gap is what it always was: the winner is 13x further above it than the runner-up.
w, ru = ranked[0][0] - FLOOR, ranked[1][0] - FLOOR
check(w / ru > 5,
      "the winner clears the runner-up by >5x measured above the no-relationship floor of %.2f "
      "(%.2f vs %.2f above it, %.1fx) — one clean winner, not a near-tie" % (FLOOR, w, ru, w / ru))
check("XAN_1192" not in (ranked[0][1],),
      "the probe is a SATELLITE pair — it does not hand the player the boss (XAN_1192)")

print("\n-- rung 2: the control strand (threshold + one-vs-all) --")
isolates = [g for g in genes if degree(g) == 0]
check(isolates == ["XAN_6246"], "XAN_6246 is the SOLE isolate at similarity>%.1f (%s)" % (CUTOFF, isolates))
# THE BAND HAS TWO EDGES AND THEY FAIL DIFFERENTLY — this is why the prompt states the threshold
# outright. The ladder is whole only for a cutoff in roughly 8.48 .. 9.23 (similarity), and 9 is chosen
# to sit clear of both edges.
#   ABOVE the ceiling: XAN_1815 (the TAUGHT TRAP) and XAN_2781 become isolates too, so rung 2 has THREE
#     answers and rung 3's module loses its most abundant member — both rungs break at once.
#   BELOW the floor: the module closes into a clique, every member reaches degree 7, and rung 4's
#     regulator has no strict lead — the BOSS loses its single answer, silently.
# So no hint may nudge a player off the stated 9 in EITHER direction. (Under the old |r| grading the
# equivalent band was 0.15-0.7569 and only the upper edge was live; the lower edge is new, and is the
# reason 8.5 — which Lucas first suggested — is too close to the cliff.)
best = {g: max(R[g].values()) for g in genes}
check(best["XAN_6246"] < FLOOR + 0.5,
      "XAN_6246's strongest tie to anything scores %.2f against a no-relationship floor of %.2f — "
      "isolated by a mile, not by a hair" % (best["XAN_6246"], FLOOR))
ceiling = min(best[g] for g in genes if g != "XAN_6246")
check(CUTOFF < ceiling,
      "the band's CEILING is %.4f (the next-weakest gene's best tie) — above it the room gains a "
      "second isolate, so no hint may suggest a cutoff over it" % ceiling)
joiners = sorted((best[g], g) for g in genes if g != "XAN_6246")[:2]
check([g for _, g in joiners] == ["XAN_1815", "XAN_2781"],
      "and the first two genes to join the isolates above the ceiling are XAN_1815 (%.4f) and "
      "XAN_2781 (%.4f) — the first of them is the TAUGHT TRAP, so a too-high cutoff would muddy "
      "rung 3 as well as rung 2" % (joiners[0][0], joiners[1][0]))
check(ceiling - CUTOFF > 0.1,
      "the stated cutoff of %.1f clears that ceiling by %.3f — comfortably more than any rounding"
      % (CUTOFF, ceiling - CUTOFF))
# THE LOWER EDGE, found by walking down rather than asserted: below it the pigment module closes into a
# clique and rung 4's regulator has no strict degree lead. Nothing in rung 2 notices, which is exactly
# why it is pinned here — the boss would break silently.
_all_sims = sorted({R[a][b] for a in genes for b in R[a]})
def _boss_lead_strict(c):
    mods = [g for g in genes if degree(g, c) > 0]
    d = sorted((degree(g, c) for g in mods), reverse=True)
    return len(d) > 1 and degree("XAN_1192", c) == d[0] and d[0] > d[1]
_floor_edge = max([v for v in _all_sims if v < CUTOFF and not _boss_lead_strict(v)] or [0])
check(CUTOFF - _floor_edge > 0.1,
      "and it clears the BAND'S LOWER EDGE (%.3f, where the module becomes a clique and the boss's "
      "degree lead ties) by %.3f — the boss breaks silently below it, so no hint may push a player down "
      "there either" % (_floor_edge, CUTOFF - _floor_edge))

print("\n-- rung 3: the taught trap (module + abundance) --")
# The pigment module is what the player recovers from the correlation structure. Derive it the way the
# PROMPT instructs — "the largest group of co-expressed genes" — i.e. the largest CONNECTED COMPONENT at
# the cutoff, and assert that group is uniquely the largest. It used to be derived as the boss's own
# ego network (neighbours("XAN_1192")), which happens to coincide today because the boss touches all
# seven other members; but that made the test agree with the answer by construction. A re-seeded CSV
# that grew the component a hop further, or let another component overtake it, would change both the
# rung-3 and rung-4 answers while this file stayed green.
def component(seed):
    seen, stack = {seed}, [seed]
    while stack:
        for nb in neighbours(stack.pop()):
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return seen

comps, unseen = [], set(genes)
while unseen:
    c = component(next(iter(unseen)))
    comps.append(c)
    unseen -= c
comps.sort(key=len, reverse=True)
check(len(comps[0]) > len(comps[1]),
      "the largest connected group is unique — %d genes vs %d for the next biggest, so "
      "'the largest group of co-expressed genes' has ONE answer (component sizes %s)"
      % (len(comps[0]), len(comps[1]), sorted((len(c) for c in comps), reverse=True)))
module = comps[0]
check("XAN_1192" in module,
      "the regulator sits inside that largest group — rungs 3 and 4 both read from it")
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
# This block used to compare four prose strings written a few lines above it, so it asserted that four
# literals in this file differ from each other and could never fail. Replaced 2026-09-22 with checks
# that bind to the DATA: each rung's answer must be out of reach of the previous rung's method, which
# is what "one new move per rung, no plateau" actually means.
answers = ["XAN_4574", "XAN_6246", "XAN_1815", "XAN_1192"]
check(len(set(answers)) == 4, "no two rungs answer the same gene (%s)" % answers)

# rung 1's move (argmax |r| against the probe) must NOT also land rung 2, 3 or 4.
r1 = max((g for g in genes if g != "XAN_4418"), key=lambda g: R["XAN_4418"][g])
check(r1 == "XAN_4574" and r1 not in answers[1:],
      "rung 1's move (nearest neighbour of the probe) reaches only rung 1's answer")

# rung 2's move (degree, one-vs-all) must not land rung 3's answer — abundance is the new move there.
by_degree = sorted(genes, key=degree)
check(by_degree[0] == "XAN_6246" and by_degree[0] != answers[2],
      "rung 2's move (rank by degree) does not reach rung 3's answer")

# rung 3's move (abundance inside the module) must NOT land the boss — this is the taught trap, and it
# is the single most important non-plateau in the ladder.
check(max(module, key=lambda g: mean[g]) != "XAN_1192",
      "rung 3's move (most abundant in the module) does NOT reach the boss — the trap is live")

# rung 4's move (degree inside the module) must not be answerable by rung 3's.
check(max(module, key=degree) != max(module, key=lambda g: mean[g]),
      "rung 4's move (most connected in the module) disagrees with rung 3's — the boss corrects it")
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
SLOTS = ["car_madder", "car_woad", "car_weld", "car_verdigris"]
queue = doc.get("puzzleQueue") or []
check(len(queue) == 4, "the queue holds all four rungs (%d)" % len(queue))
# ONE SLOT PER RUNG, and the fifth cab LIVE FROM THE START. The escape is gated on having ridden every line
# (rode_<line>), and a cab's lever only works once its desk is solved. With five queue slots and four rungs
# the fifth cab visited could never be energised, so its line could never be ridden and the escape was
# unreachable, while every other check stayed green (found 2026-09-19).
n_slots = sum(1 for r in rooms.values() for h in r.get("hotspots", []) if h.get("queue"))
check(n_slots == len(queue), "one queue slot per rung (%d slots, %d rungs) — a spare slot can never be solved"
      % (n_slots, len(queue)))
lb = {h["id"]: h for h in rooms["car_lampblack"]["hotspots"]}
check("availableWhen" not in lb["selector"], "car_lampblack's lever works from the first visit (no gate)")
check(all(v.get("when") is True for v in lb["night_wash"].get("variants", [])),
      "car_lampblack is energised from the start (its energised variant is unconditional)")
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
    # >=6 DATA-DERIVED DISTRACTORS is the rule, so >=7 options counting the right one. This read
    # `>= 6` until 2026-09-22, which would have let a rung ship with five distractors.
    check(len(opts) >= 7,
          "rung %d has >=6 distractors, i.e. >=7 options (%d)" % (i + 1, len(opts)))
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
    # STARTER CODE: the PREP, never the ANALYSIS (Lucas, 2026-09-25). It used to be the bare object
    # name, `lichen_expression`. That was right while the room was graded on correlation, where the
    # first move is a one-liner; it is wrong now that the room is graded in the chapter's vocabulary,
    # because the prep has two steps a student cannot be expected to guess and CANNOT get wrong without
    # silently shifting the stated threshold: the genes have to become the ROWS (they are what is being
    # compared, and the obvious pivot puts the samples there), and each gene has to be z-scored FIRST,
    # along an axis `scale_variance` cannot reach — it scales the sample columns, not the gene rows, so
    # the default TRUE moves the whole similarity scale and the stated 9 stops being the right number.
    # So the prep is given, identically on every rung, and the analysis is still entirely the player's.
    st = (queue[i].get("starterCode") or "")
    for frag in ("expression_normalized", "pivot_wider", 'names_from = "lichen_isolate"',
                 "lichen_expression_wide"):
        check(frag in st, "rung %d's starterCode carries the prep step %r" % (i + 1, frag))
    # It stops at the PIVOT. runMatrixAnalysis, the similarity conversion, the threshold and reading the
    # network are all the player's, and all of them are chapter 7 verbatim.
    check(not re.search(r"runMatrixAnalysis|similarity|1 */ *\(1 *\+|filter\(|scale\(", st),
          "rung %d's starterCode stops at the PIVOT — the distance call, the similarity conversion, the "
          "threshold and reading the network are the player's work" % (i + 1))
    check(st == (queue[0].get("starterCode") or ""),
          "rung %d's starterCode is identical to rung 1's — the prep is the same on every rung, so a "
          "player who edited it on one cab is not fighting a different block on the next" % (i + 1))
    check(not re.search(r"cor\(|filter\(|group_by|arrange\(|ggplot|aes\(", q.get("prompt", "")),
          "rung %d's prompt leaks no code" % (i + 1))
    # THE STATED THRESHOLD MUST BE THE ONE THIS FILE GRADES AT. Rungs 2, 3 and 4 all name it in prose;
    # if an edit moved the number in a prompt without moving CUTOFF here, every check above would stay
    # green while the room asked for a graph nobody derives. Rung 1 states no threshold and is exempt.
    if i > 0:
        check(("above %g" % CUTOFF) in q.get("prompt", "") or ("above <b>%g</b>" % CUTOFF) in q.get("prompt", ""),
              "rung %d's prompt states the threshold this file grades at (%g)" % (i + 1, CUTOFF))

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
    #
    # CARRIED TEXT, not `body`. A `pickup` clue is read TWICE: in the room (`body`) and afterwards from
    # the notebook (`pickup`), and the two are separate strings that a hand-edit can easily desync — which
    # is exactly what happened on 2026-09-22, when the convention was added to `body` alone and the copy
    # the player actually carries to the lock did not have it. Assert on what they are holding when they
    # type the answer, i.e. `pickup` where there is one.
    carried = lambda h: str(h.get("pickup") or h.get("body") or "")
    cards = [h for h in rooms["ochre_hall"]["hotspots"]
             if h.get("type") == "clue" and re.search(r"lower letter", carried(h), re.I)]
    check(bool(cards),
          "the filing convention (both references, one entry, lower letter first) is in the CARRIED text "
          "of an ochre_hall clue — without it the escape is unsolvable with the right answer in hand")
    # "Unused" is the word the standing orders use for the target, and it has an obvious wrong reading:
    # the stretches past the last interchange on the woad and weld lines cannot be ridden, so a player
    # naturally reads THOSE stations as the disused ones (Lucas, playtest 2026-09-22). The orders must
    # therefore DEFINE unused by the property that actually identifies a ghost — absent from every map —
    # rather than leaving it to be inferred from where the train will take you.
    defined = [h for h in rooms["ochre_hall"]["hotspots"]
               if h.get("type") == "clue" and re.search(r"no map", carried(h), re.I)]
    check(bool(defined),
          "an ochre_hall clue DEFINES 'unused' as appearing on no map — otherwise the unreachable ends "
          "of the woad and weld lines read as the answer")
    # And the reason those stretches cannot be ridden has to be sayable in-world, or the single-direction
    # lever is itself evidence for the wrong reading.
    closed = [h for h in rooms["ochre_hall"]["hotspots"]
              if h.get("type") == "clue" and re.search(r"through running", carried(h), re.I)]
    check(bool(closed),
          "an ochre_hall clue explains why the far ends of those lines cannot be ridden (no through "
          "running), so 'the train will not go there' stops reading as 'disused'")
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
