#!/usr/bin/env python3
"""
test_heist.py — regression guards for the flat_clustering/heist scenario ("Nobody Works Alone").

Pins the parts that can silently break WITHOUT a browser: both branches' verified k-means answers
staying in lockstep with `data/case_file.csv`, the two elbows staying readable, both scaling traps
staying live, the two bosses staying INDEPENDENT of each other, and — once the rooms are wired —
the MCQ option sets, the no-reveal rule and the decoder key.

Run: python3 test_heist.py

Needs numpy + pandas + scikit-learn (the same stack `_scratch/verify_ladder.py` uses). Truth labels
are NOT read from `_scratch/*.npy`: they are re-derived by clustering the CSV, so this test fails
if the data drifts away from the design rather than agreeing with a stale artefact.

Failure modes it guards:
  - the CSV changes and a rung's verified answer (18 / k=5 / 10 / 29 / k=3 / 22) stops matching;
  - an elbow stops being readable (the drop ratio after the true k creeps up), so "click the elbow"
    becomes a guess;
  - a scaling trap collapses — raw k-means stops grouping by duration (A) or haul (B), and the boss
    stops teaching "put the measures on an equal footing";
  - THE TWO BOSSES STOP BEING INDEPENDENT. A's answer must be a crew-5 job that left through a
    DIFFERENT channel and B's a channel-III job done by a DIFFERENT crew. A job that is a mate on
    BOTH axes (e.g. Halesworth Court, crew 5 AND channel III) hands one player the other's boss
    answer for free and silently kills the two-player design;
  - a boss option set gains a second true mate, or loses its raw-band decoy (skipped until wired);
  - a `reveal` sneaks into a wired hotspot, or the decoder key drifts (skipped until wired).
"""
import csv, json, os, re, sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "data", "case_file.csv")
SCEN = os.path.join(HERE, "scenario.json")
DECODER = os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R")
SCENARIO_ID = 20

ENTRY = ["entry_height_m", "tool_score", "approach_min", "entry_hour"]
DISPOSAL = ["days_to_surface", "lot_size", "recut_score", "ports_used"]
A_SCALE_TRAP = "minutes_inside"     # runs to hundreds; unscaled it swamps the entry block
B_SCALE_TRAP = "haul_value_gbp"     # runs to tens of thousands; unscaled it swamps the disposal block
BOSS_JOB = "Ardsley Strongroom"

fails = []
skips = []


def check(cond, msg):
    print(("  ok    " if cond else "FAIL    ") + msg)
    if not cond:
        fails.append(msg)


def skip(msg):
    print("  skip  " + msg)
    skips.append(msg)


def scale(X):
    return (X - X.mean(0)) / X.std(0, ddof=1)


def km(X, k):
    return KMeans(n_clusters=k, n_init=50, random_state=0).fit(X).labels_


def wss(X, k):
    return KMeans(n_clusters=k, n_init=50, random_state=0).fit(X).inertia_


def ari(a, b):
    from sklearn.metrics import adjusted_rand_score
    return adjusted_rand_score(a, b)


def elbow_is_readable(X, k_true, label):
    """The elbow is only clickable if the drop AFTER k_true is small next to the drop INTO it."""
    w = [wss(X, k) for k in range(1, 9)]
    into = w[k_true - 2] - w[k_true - 1]
    after = w[k_true - 1] - w[k_true]
    ratio = after / into if into else 1.0
    check(ratio < 0.25, f"{label}: elbow at k={k_true} is readable (drop after / drop into = {ratio:.2f})")
    print("        WSS k=1..8 = " + " / ".join(f"{v:.0f}" for v in w))


def main():
    df = pd.read_csv(CSV)
    check(len(df) == 60, f"the case file holds 60 jobs (found {len(df)})")
    check(BOSS_JOB in set(df.job), f"the boss job '{BOSS_JOB}' is in the file")

    # ---- truth, re-derived from the data itself (the scaled clusterings ARE the design's truth) ----
    crew = km(scale(df[ENTRY].values), 5)
    chan = km(scale(df[DISPOSAL].values), 3)
    raw_a = km(df[ENTRY + [A_SCALE_TRAP]].values, 5)
    raw_b = km(df[DISPOSAL + [B_SCALE_TRAP]].values, 3)
    t = int(df.index[df.job == BOSS_JOB][0])

    print("\nBRANCH A — the entry evidence (5 crews)")
    sizes_a = pd.Series(crew).value_counts().sort_values(ascending=False)
    check(sorted(sizes_a.values, reverse=True) == [18, 13, 11, 10, 8],
          f"the five crews are 18/13/11/10/8 (found {sorted(sizes_a.values, reverse=True)})")
    check(int(sizes_a.iloc[0]) == 18 and sizes_a.iloc[0] / sizes_a.iloc[1] > 1.15,
          f"A-S1 busiest crew = 18, single winner (runner-up {int(sizes_a.iloc[1])}, "
          f"+{100 * (sizes_a.iloc[0] / sizes_a.iloc[1] - 1):.0f}%)")
    elbow_is_readable(scale(df[ENTRY].values), 5, "A-S2")
    h = df.groupby(crew).entry_height_m.mean().sort_values(ascending=False)
    hi_crew, hi_size = h.index[0], int((crew == h.index[0]).sum())
    check(h.iloc[0] / h.iloc[1] > 1.15,
          f"A-S3 one crew went in clearly highest ({h.iloc[0]:.2f} m vs {h.iloc[1]:.2f} m, "
          f"+{100 * (h.iloc[0] / h.iloc[1] - 1):.0f}%) -> its size = {hi_size}")
    check(hi_size == 10, f"A-S3 answer is 10 (found {hi_size})")
    check(hi_crew != crew[t], "A-S3 does not answer the same entity the boss does")

    print("\nBRANCH B — the disposal evidence (3 channels)")
    sizes_b = pd.Series(chan).value_counts().sort_values(ascending=False)
    check(sorted(sizes_b.values, reverse=True) == [29, 22, 9],
          f"the three channels are 29/22/9 (found {sorted(sizes_b.values, reverse=True)})")
    check(int(sizes_b.iloc[0]) == 29 and sizes_b.iloc[0] / sizes_b.iloc[1] > 1.15,
          f"B-S1 busiest channel = 29, single winner (runner-up {int(sizes_b.iloc[1])}, "
          f"+{100 * (sizes_b.iloc[0] / sizes_b.iloc[1] - 1):.0f}%)")
    elbow_is_readable(scale(df[DISPOSAL].values), 3, "B-S2")
    d = df.groupby(chan).days_to_surface.mean().sort_values(ascending=False)
    slow_chan, slow_size = d.index[0], int((chan == d.index[0]).sum())
    check(d.iloc[0] / d.iloc[1] > 1.15,
          f"B-S3 one channel clearly sat longest ({d.iloc[0]:.0f} d vs {d.iloc[1]:.0f} d, "
          f"+{100 * (d.iloc[0] / d.iloc[1] - 1):.0f}%) -> its size = {slow_size}")
    check(slow_size == 22, f"B-S3 answer is 22 (found {slow_size})")
    check(slow_chan != chan[t], "B-S3 does not answer the same entity the boss does")

    print("\nTHE SCALING TRAPS — raw k-means must group by the big column, not by the truth")
    dur_band = pd.qcut(df[A_SCALE_TRAP], 5, labels=False)
    haul_band = pd.qcut(df[B_SCALE_TRAP], 3, labels=False)
    check(ari(raw_a, dur_band) > ari(raw_a, crew),
          f"A: raw k=5 groups by DURATION not crew (ARI dur {ari(raw_a, dur_band):.2f} "
          f"vs crew {ari(raw_a, crew):.2f})")
    check(ari(raw_b, haul_band) > ari(raw_b, chan),
          f"B: raw k=3 groups by HAUL not channel (ARI haul {ari(raw_b, haul_band):.2f} "
          f"vs channel {ari(raw_b, chan):.2f})")

    print("\nTHE TWO BOSSES — each answer must be invisible from the OTHER player's block")
    true_a = set(df.job[(crew == crew[t]) & (df.index != t)])
    true_b = set(df.job[(chan == chan[t]) & (df.index != t)])
    raw_mates_a = set(df.job[(raw_a == raw_a[t]) & (df.index != t)])
    raw_mates_b = set(df.job[(raw_b == raw_b[t]) & (df.index != t)])

    both = sorted(true_a & true_b)
    check(len(true_a - true_b) > 0,
          f"A has at least one hand-mate that is NOT also a channel-mate (the only legal answers)")
    check(len(true_b - true_a) > 0,
          f"B has at least one channel-mate that is NOT also a hand-mate")
    print(f"        mates on BOTH axes — ILLEGAL as either boss answer: {both}")
    legal_a = sorted(true_a - raw_mates_a - true_b)
    legal_b = sorted(true_b - raw_mates_b - true_a)
    check(bool(legal_a), f"A has a legal boss answer (true mate, not a raw-band mate, not B's): {legal_a}")
    check(bool(legal_b), f"B has a legal boss answer: {legal_b}")
    check(not (set(legal_a) & set(legal_b)), "no job is a legal answer for BOTH bosses")
    check(bool(sorted(raw_mates_a - true_a)), "A has a clean decoy (raw duration-band mate, not a true mate)")
    check(bool(sorted(raw_mates_b - true_b)), "B has a clean decoy (raw haul-band mate, not a true mate)")

    # ---- wiring lockstep: skipped until the rooms carry live hotspots ----
    print("\nWIRING LOCKSTEP")
    doc = json.load(open(SCEN, encoding="utf-8"))
    wired = [r for r in doc["rooms"] if r.get("hotspots")]
    if not wired:
        skip("no room carries live hotspots yet — MCQ options, no-reveal and sfx checks deferred")
    else:
        blob = json.dumps(doc)
        check('"reveal"' not in blob, "no hotspot leaks a `reveal`")
        for who, legal, decoys, true_set in (("A", legal_a, raw_mates_a - true_a, true_a),
                                             ("B", legal_b, raw_mates_b - true_b, true_b)):
            opts = _boss_options(doc, who)
            if opts is None:
                skip(f"{who}: boss MCQ not wired yet")
                continue
            hits = [o for o in opts if o in true_set]
            check(len(hits) == 1, f"{who}: exactly one true mate among the {len(opts)} offered options ({hits})")
            check(hits and hits[0] in legal, f"{who}: the offered answer is a LEGAL answer (invisible to the partner)")
            check(len(opts) >= 6, f"{who}: at least 6 options offered (found {len(opts)})")
            check(any(o in decoys for o in opts), f"{who}: the taught trap's decoy is on the board")

    print("\nDECODER LOCKSTEP")
    src = open(DECODER, encoding="utf-8").read() if os.path.exists(DECODER) else ""
    registered = bool(re.search(r"scenario_id\s*=\s*%d\b" % SCENARIO_ID, src))
    if not wired:
        skip(f"scenario id {SCENARIO_ID} not registered in decode_codes.R — correct while unwired"
             if not registered else f"scenario id {SCENARIO_ID} is registered ahead of wiring")
    else:
        check(registered, f"scenario id {SCENARIO_ID} is registered in decode_codes.R")

        # THE TWO-PLAYER INVARIANT. Each student mints FOUR steps and `grade_one` compares them
        # positionally, so one key can only serve both branches while the branches' correct indices
        # agree element by element. Re-ordering one branch's options without the other silently
        # mis-grades every student of the other branch — no other check in the corpus catches it.
        vec_a, vec_b = [], []
        for r in doc["rooms"]:
            for h in r.get("hotspots", []):
                if h.get("type") == "puzzle" and h.get("question"):
                    (vec_a if r["key"].startswith("a_") else vec_b).append(h["question"]["correct"])
        check(vec_a == vec_b,
              f"both branches' correct-index vectors agree — A {vec_a} vs B {vec_b}")
        m = re.search(r"FLAT_CLUSTERING_HEIST_KEY.*?correct\s*=\s*c\(([^)]*)\)", src, re.S)
        key_vec = [int(x) for x in m.group(1).replace(" ", "").split(",")] if m else []
        check(key_vec == vec_a + vec_b,
              f"the decoder key is the two branch vectors end to end — key {key_vec}")
        check(len(set(vec_a)) > 1, f"the correct index is varied across rooms (not all the same): {vec_a}")

    print()
    if fails:
        print(f"RESULT: {len(fails)} FAILURE(S)")
        for f in fails:
            print("   - " + f)
        return 1
    print(f"RESULT: ALL CHECKS PASS ({len(skips)} deferred until wiring)")
    return 0


def _boss_options(doc, who):
    """Return the boss room's MCQ option labels for branch A or B, or None if not wired."""
    key = "a_vault" if who == "A" else "b_stateroom"
    for r in doc["rooms"]:
        if r.get("key") != key:
            continue
        for h in r.get("hotspots", []):
            p = h.get("question") or {}
            opts = p.get("options")
            if opts:
                return [o.get("label", o) if isinstance(o, dict) else o for o in opts]
    return None


if __name__ == "__main__":
    sys.exit(main())
