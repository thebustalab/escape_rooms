#!/usr/bin/env python3
"""
test_beacons.py — regression guards for the networks/beacons scenario (stdlib only; python3).

Beacons grades Part 2 of the networks chapter — RELATIONAL networks, edges as observed facts — against
`data/dispatch_ledger.csv`. Its ungraded escape is a separate, data-free COVERAGE puzzle over a
line-of-sight network derived from real elevation: which four watchtowers, lit, put a fire in sight of
every village.

This file guards the parts that can silently break WITHOUT a browser, and there are two independent
halves because the scenario has two networks about different entities:

  A. THE GRADED LADDER, against the shipped CSV — the four rung answers plus the boss staying in
     lockstep with the data. The scenario's whole argument is that volume is not importance, so the
     guards are: the busiest station is removable with no structural effect, and the sole articulation
     point is the twentieth-busiest of twenty.

  B. THE ESCAPE, against the verified placement in `_scratch/tianshan_coverage.json` — the four fires
     and every village's `seen_by`. The ledger's `answer` fields are authored by hand from that
     placement, so they can drift from the terrain the moment anyone re-runs the search with different
     parameters. That is exactly the class of bug the two retired escapes died of.

Failure modes it guards:
  - the CSV changes and a rung's verified answer stops being the single clean winner;
  - the shortcut (busiest = Kingsmuster) and the boss (articulation point = Whistlegate) stop being
    DIFFERENT stations, which is the entire taught trap;
  - the placement is re-searched and the four fires change, but the wired ledger answers do not;
  - a village appears that no fire reaches, or a second set of four also covers everything, or one of
    the four becomes redundant — any of which makes the escape unsolvable or multiply-solvable;
  - the ANVIL stops being the trap: it is the highest walked tower overlooking almost the most villages
    and it must NOT be lit, because that is the boss's argument performed rather than retold;
  - the ledger loses `allOrNothing`, which with unlimited attempts lets a player solve the escape one
    dropdown at a time (~36 submits) with no survey done. See shared/ledger_rule.js -> confirmAll.

Run: python3 test_beacons.py
"""
import csv
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []


def check(ok, label, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILS.append(label)
    return ok


# ---------------------------------------------------------------- A. the graded ladder

def load_edges():
    with open(os.path.join(HERE, "data", "dispatch_ledger.csv")) as f:
        return [(r["origin"], r["destination"], int(r["dispatches"])) for r in csv.DictReader(f)]


def components(nodes, undirected_edges):
    """Connected-component count by union-find — the boss's actual operation."""
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in undirected_edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return len({find(n) for n in nodes})


def test_ladder():
    print("\nA. THE GRADED LADDER — against data/dispatch_ledger.csv")
    edges = load_edges()
    nodes = sorted({e[0] for e in edges} | {e[1] for e in edges})
    check(len(nodes) == 20, "20 stations", f"{len(nodes)}")
    check(len(edges) == 184, "184 directed weighted edges", f"{len(edges)}")

    # rung 2 — direction/asymmetry: the station that sends far more than it receives
    out = {n: 0 for n in nodes}
    inn = {n: 0 for n in nodes}
    for a, b, w in edges:
        out[a] += w
        inn[b] += w
    ratio = sorted(((out[n] / inn[n], n) for n in nodes if inn[n]), reverse=True)
    check(ratio[0][1] == "Fenwatch", "rung 2: Fenwatch has the highest out/in ratio", ratio[0][1])
    check(ratio[0][0] / ratio[1][0] >= 3.0,
          "rung 2: Fenwatch's ratio is a runaway single winner",
          f"{ratio[0][0]:.2f} vs {ratio[1][0]:.2f} ({ratio[1][1]})")

    # rung 3 — THE SHORTCUT: busiest overall by total volume
    vol = {n: out[n] + inn[n] for n in nodes}
    busiest = sorted(vol.items(), key=lambda kv: -kv[1])
    check(busiest[0][0] == "Kingsmuster", "rung 3 (shortcut): Kingsmuster is busiest", busiest[0][0])
    check(busiest[0][1] >= 2.0 * busiest[1][1],
          "rung 3: the shortcut answer is a clean single winner",
          f"{busiest[0][1]} vs {busiest[1][1]} ({busiest[1][0]})")

    # BOSS — components under node removal: the sole articulation point
    und = {(min(a, b), max(a, b)) for a, b, _ in edges if a != b}
    base = components(nodes, und)
    cut = [n for n in nodes
           if components([x for x in nodes if x != n],
                         [(a, b) for a, b in und if n not in (a, b)]) > base]
    check(cut == ["Whistlegate"], "BOSS: Whistlegate is the SOLE articulation point", str(cut))

    # THE TAUGHT TRAP, and it is the whole scenario: volume is not importance
    rank = [n for n, _ in busiest].index("Whistlegate") + 1
    check(rank == 20, "the articulation point ranks 20th of 20 by volume", f"rank {rank}")
    check(components([x for x in nodes if x != "Kingsmuster"],
                     [(a, b) for a, b in und if "Kingsmuster" not in (a, b)]) == base,
          "removing the BUSIEST station changes nothing structurally")


# ---------------------------------------------------------------- B. the escape

def test_escape():
    print("\nB. THE ESCAPE — against _scratch/tianshan_coverage.json")
    path = os.path.join(HERE, "_scratch", "tianshan_coverage.json")
    if not os.path.exists(path):
        # _scratch is gitignored, so a fresh clone legitimately has no placement to check against.
        print("  SKIP  placement not present (_scratch is gitignored); escape guards not run")
        return None
    P = json.load(open(path))
    fires = set(P["answer_fires"])
    n_t = len(P["towers"])
    sig = [set(v["seen_by"]) for v in P["villages"]]
    covers = lambda S: all(s & set(S) for s in sig)

    check(len(fires) == P["n_fires"] == 4, "four fires", str(sorted(fires)))
    check(covers(fires), "the four fires reach every village")
    winners = [c for c in itertools.combinations(range(n_t), 4) if covers(c)]
    check(len(winners) == 1 and set(winners[0]) == fires,
          "exactly ONE set of four covers everything", f"{len(winners)} sets cover")
    check(not [c for c in itertools.combinations(range(n_t), 3) if covers(c)],
          "no set of three covers everything, so the fuel budget is honest")
    check(not [f for f in fires if covers(fires - {f})], "no fire is redundant")
    check(all(len(s) >= 2 for s in sig),
          "no village sees only one tower (which would give that tower away)")

    per_tower = [sum(1 for v in P["villages"] if t in v["seen_by"]) for t in range(n_t)]
    check(min(per_tower) >= 3,
          "every tower overlooks >= 3 villages, so none can be dismissed at a glance",
          str(per_tower))

    # THE TRAP: the most commanding tower is not lit. This is the boss's argument performed.
    elevs = [t["elev"] for t in P["towers"]]
    highest = max(range(n_t), key=lambda t: elevs[t])
    fattest = max(range(n_t), key=lambda t: per_tower[t])
    check(highest not in fires,
          "the HIGHEST tower is not one of the four",
          f"t{highest} at {elevs[highest]:.0f} m overlooking {per_tower[highest]} villages")
    print(f"  ....  (informational) the tower overlooking the most villages is t{fattest} "
          f"({per_tower[fattest]} villages), {'lit' if fattest in fires else 'NOT lit'}")
    check(min(per_tower[f] for f in fires) <= 4,
          "at least one of the four overlooks very few villages and is still indispensable",
          f"{ {f: per_tower[f] for f in sorted(fires)} }")

    crown = P["crown"]
    check(crown.get("reaches_towers") == n_t,
          "the Crown sees every watchtower, so the order can be given from it",
          f"{crown.get('reaches_towers')}/{n_t}")


# ---------------------------------------------------------------- C. wiring invariants

def test_tower_map():
    """The story's tower NAMES must stay bound to the placement's tower INDICES.

    The placement states the answer as indices (light 3, 5, 6, 7); the ledger will be authored with names
    (the Broken Tooth, the Spindle, the Hood, the Ladder). scenario.json's _designNotes.towerMap is the
    join between them, and it is exactly the thing that silently rots when someone re-runs the search:
    the maths stays right, the fiction stays readable, and they quietly stop describing each other.
    """
    print("\nD. TOWER NAMES <-> PLACEMENT")
    d = json.load(open(os.path.join(HERE, "scenario.json")))
    tm = {k: v for k, v in (d.get("_designNotes", {}).get("towerMap") or {}).items()
          if not k.startswith("_")}
    path = os.path.join(HERE, "_scratch", "tianshan_coverage.json")
    if not tm or not os.path.exists(path):
        print("  SKIP  no tower map or no placement")
        return
    P = json.load(open(path))
    n_t = len(P["towers"])
    check(sorted(tm.values()) == list(range(n_t)),
          f"every one of the {n_t} placement towers is named exactly once",
          str(sorted(tm.values())))

    room_keys = {r["key"] for r in d.get("rooms", [])}
    missing = [k for k in tm if k not in room_keys]
    check(not missing, "every named tower has a room", str(missing))

    named_fires = sorted(k for k, v in tm.items() if v in set(P["answer_fires"]))
    check(len(named_fires) == P["n_fires"],
          "exactly four named towers are the fires", ", ".join(named_fires))
    # the trap, by name: the highest tower must not be a fire
    elevs = [t["elev"] for t in P["towers"]]
    highest_idx = max(range(n_t), key=lambda t: elevs[t])
    highest_name = next(k for k, v in tm.items() if v == highest_idx)
    check(highest_idx not in set(P["answer_fires"]),
          f"the highest tower ({highest_name}) is NOT lit — the trap, by name")


def test_wiring():
    print("\nC. WIRING — scenario.json")
    d = json.load(open(os.path.join(HERE, "scenario.json")))
    check(d.get("id") == 19, "codec id is 19", str(d.get("id")))
    for k in ("title", "subtitle", "story", "enterLabel", "done", "escapeDone"):
        check(bool(d.get(k)), f"story-map field present: {k}")
    blob = json.dumps(d).lower()
    for word in ("garrison", "muster the", "relief column", "had already burned"):
        check(word not in blob,
              f"no martial vocabulary: {word!r} absent (the raid became the flood)")

    # THE ESCAPE LEDGER. Look in BOTH places: content is authored onto `plannedHotspots` pre-art and
    # only moves to `hotspots` when the art is committed, so a guard that checks only committed hotspots
    # sleeps through the entire authoring phase — which is exactly when the answers are being typed.
    ledgers = [hs for r in d.get("rooms", [])
               for hs in ((r.get("hotspots") or []) + (r.get("plannedHotspots") or []))
               if hs.get("type") == "ledger"]
    if not ledgers:
        print("  SKIP  no ledger authored yet")
    for lg in ledgers:
        rows = lg.get("rows") or []
        distinct = len({r.get("answer") for r in rows})
        check(bool(rows), "the escape ledger has rows", f"{len(rows)}")
        if rows and distinct == len(rows):
            check(lg.get("allOrNothing") is True,
                  "the escape ledger sets allOrNothing (every row holds a different answer, so the "
                  "stock group rule would confirm one row at a time)",
                  f"{len(rows)} rows, {distinct} distinct answers")
        check(not lg.get("maxAttempts"),
              "attempts are unlimited (maxAttempts unset), so the ungraded escape cannot dead-end")
        opts = {o["key"] if isinstance(o, dict) else o for o in (lg.get("options") or [])}
        bad = [r["answer"] for r in rows if r.get("answer") not in opts]
        check(not bad, "every ledger answer is one of the offered options", str(bad))

        # AND the answers must still be the placement's fires, by name.
        tm = {k: v for k, v in (d.get("_designNotes", {}).get("towerMap") or {}).items()
              if not k.startswith("_")}
        path = os.path.join(HERE, "_scratch", "tianshan_coverage.json")
        if tm and os.path.exists(path):
            P = json.load(open(path))
            wired = {tm.get(r["answer"]) for r in rows}
            check(wired == set(P["answer_fires"]),
                  "the wired ledger answers ARE the placement's four fires",
                  f"wired {sorted(x for x in wired if x is not None)} vs placement {sorted(P['answer_fires'])}")


if __name__ == "__main__":
    test_ladder()
    test_escape()
    test_tower_map()
    test_wiring()
    print(f"\n{'ALL CHECKS PASSED' if not FAILS else 'FAILED: ' + '; '.join(FAILS)}")
    sys.exit(1 if FAILS else 0)
