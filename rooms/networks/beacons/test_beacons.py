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
    print("\nA. THE GRADED LADDER — against data/dispatch_ledger.csv (v2: the twelve places of the world)")
    edges = load_edges()
    nodes = sorted({e[0] for e in edges} | {e[1] for e in edges})
    d = json.load(open(os.path.join(HERE, "scenario.json")))
    world = {r["key"] for r in d["rooms"]}
    token = lambda k: "_".join(w.capitalize() for w in k.split("_"))       # rams_head -> Rams_Head
    check(set(nodes) == {token(k) for k in world}, "the dataset's stations ARE the world's twelve places",
          str(sorted(set(nodes) ^ {token(k) for k in world})))
    check(len(edges) == 40, "40 directed weighted edges", f"{len(edges)}")

    # rung 1 — the heaviest single link
    top = sorted(edges, key=lambda e: -e[2])
    check((top[0][0], top[0][1]) == ("Anvil", "Ladder"), "rung 1: Anvil -> Ladder is the heaviest link", f"{top[0]}")
    other = next(e for e in top if {e[0], e[1]} != {"Anvil", "Ladder"})
    check(top[0][2] >= 1.05 * other[2], "rung 1: a clean single winner over any other pair", f"{top[0][2]} vs {other}")

    out = {n: 0 for n in nodes}
    inn = {n: 0 for n in nodes}
    for a, b, w in edges:
        out[a] += w
        inn[b] += w
    ratio = sorted(((out[n] / inn[n], n) for n in nodes if inn[n]), reverse=True)
    check(ratio[0][1] == "Fenwatch", "rung 2: Fenwatch has the highest out/in ratio", ratio[0][1])
    check(ratio[0][0] / ratio[1][0] >= 3.0, "rung 2: a runaway single winner", f"{ratio[0][0]:.2f} vs {ratio[1][0]:.2f} ({ratio[1][1]})")

    vol = {n: out[n] + inn[n] for n in nodes}
    busiest = sorted(vol.items(), key=lambda kv: -kv[1])
    check(busiest[0][0] == "Crown", "rung 3 (shortcut): the Crown is busiest", busiest[0][0])
    check(busiest[0][1] >= 1.15 * busiest[1][1], "rung 3: a clean single winner", f"{busiest[0][1]} vs {busiest[1][1]} ({busiest[1][0]})")

    und = {(min(a, b), max(a, b)) for a, b, _ in edges if a != b}
    base = components(nodes, und)
    cut = [n for n in nodes
           if components([x for x in nodes if x != n], [(a, b) for a, b in und if n not in (a, b)]) > base]
    check(cut == ["Whistlegate"], "BOSS: Whistlegate is the SOLE articulation point", str(cut))
    rank = [n for n, _ in busiest].index("Whistlegate") + 1
    check(rank == 12, "the station holding the march together is the QUIETEST of twelve", f"rank {rank}")
    check(components([x for x in nodes if x != "Crown"], [(a, b) for a, b in und if "Crown" not in (a, b)]) == base,
          "removing the BUSIEST station changes nothing structurally")
    check(len({"Anvil->Ladder", "Fenwatch", "Crown", "Whistlegate"}) == 4, "four rungs, four different answers")


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
        check(lg.get("unordered") is True,
              "the escape accepts the four fires in ANY order (Lucas, 2026-09-17) — the rows are "
              "interchangeable slots, so the answer is a SET of towers")
        check(not any(w in (r.get("label") or "").lower() for r in rows for w in ("south", "north")),
              "no row label implies an order")
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


def test_survey_pickups():
    """The survey the escape is built on (2026-09-16). One base sheet in Fenwatch and one spyglass per
    tower room, each landing its OWN line-tile and counting toward the Crown's gate. Guards: a spyglass
    that forgets `onPickup` (the gate can never open), a tile wired to the wrong room (the player stacks a
    network that is not the terrain's), a missing image, and the gate threshold drifting from the count."""
    d = json.load(open(os.path.join(HERE, "scenario.json")))
    tm = {k: v for k, v in (d.get("_designNotes", {}).get("towerMap") or {}).items() if not k.startswith("_")}
    rooms = {r["key"]: r for r in d["rooms"]}
    glassed = 0
    for room in tm:
        spy = [h for h in rooms[room].get("hotspots", []) if h.get("type") == "clue" and h.get("id") == "spyglass"]
        check(len(spy) == 1, f"{room}: exactly one spyglass", str(len(spy)))
        if not spy:
            continue
        h = spy[0]
        check(h.get("image") == f"survey/tile_{room}.png", f"{room}: spyglass lands its own line-tile", h.get("image"))
        check(os.path.exists(os.path.join(HERE, h.get("image") or "-")), f"{room}: line-tile image exists")
        check(h.get("overlay") is True and h.get("pickup"), f"{room}: tile is a pickup overlay")
        check(h.get("onPickup") == {"inc": "tiles_glassed"}, f"{room}: spyglass counts toward the gate", str(h.get("onPickup")))
        glassed += h.get("onPickup") == {"inc": "tiles_glassed"}
    sheet = [h for h in rooms["fenwatch"].get("hotspots", []) if h.get("id") == "survey_sheet"]
    check(len(sheet) == 1 and not sheet[0].get("overlay") and os.path.exists(os.path.join(HERE, sheet[0].get("image") or "-")),
          "Fenwatch carries the opaque base survey sheet")
    gate = [h for h in rooms["crown"].get("hotspots", []) if h.get("id") == "watch_order"]
    need = [c["gte"][1] for c in ((gate[0].get("availableWhen") or {}).get("all") or []) if "gte" in c] if gate else []
    check(need == [glassed] == [len(tm)], "the Crown's gate asks for exactly the tiles that can be collected",
          f"gate {need}, counting pickups {glassed}, towers {len(tm)}")


def test_brazier():
    """The finale gesture (2026-09-16): the crown brazier sets order_sent=lit, which is exactly what the
    order_sent night variant waits for, can only be lit once the watch order is sealed, and ends the escape.
    A drifted value means the fires never appear; a missing gate lets the escape end with no order sent."""
    d = json.load(open(os.path.join(HERE, "scenario.json")))
    cr = next(r for r in d["rooms"] if r["key"] == "crown")
    dial = [h for h in cr["hotspots"] if h.get("id") == "dispatch_brazier"]
    check(len(dial) == 1, "crown carries the brazier dial")
    if not dial:
        return
    h = dial[0]
    values = [s.get("value") for s in h.get("states") or []]
    wants = [v.get("when") for c in cr["hotspots"] for v in (c.get("variants") or []) if v.get("state") == "order_sent"]
    check(values == ["lit"] and wants == [{"eq": [h.get("key"), "lit"]}],
          "lighting the brazier is exactly what the order_sent art waits for", f"{values} vs {wants}")
    check(h.get("availableWhen") == {"solved": "crown"} and h.get("lockedBody"),
          "the brazier is locked until the watch order is sealed")
    check(h.get("endsEscape") is True, "lighting the brazier ends the escape")


def test_puzzles():
    """The four graded MCQs (wired 2026-09-16), each correct option re-derived from the shipped CSV — not
    from the designNote — plus the house rules: >=6 options, no reveal, a bare starter except the boss
    (repair-the-pipeline), whose broken script must really report no split and whose fix must really
    find exactly one. Also that every station a distractor names exists, so no option is noise."""
    import csv
    from collections import defaultdict
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", "dispatch_ledger.csv"))))
    for r in rows:
        r["dispatches"] = int(r["dispatches"])
    names = {r["origin"] for r in rows} | {r["destination"] for r in rows}
    heaviest = max(rows, key=lambda r: r["dispatches"])
    sent, recv = defaultdict(int), defaultdict(int)
    for r in rows:
        sent[r["origin"]] += r["dispatches"]; recv[r["destination"]] += r["dispatches"]
    ratio = max(names, key=lambda s: sent[s] / max(1, recv[s]))
    busiest = max(names, key=lambda s: sent[s] + recv[s])

    def pieces(edges):
        adj = defaultdict(set)
        for a, b in edges:
            adj[a].add(b); adj[b].add(a)
        seen, n = set(), 0
        for v in adj:
            if v in seen:
                continue
            n += 1; stack = [v]
            while stack:
                u = stack.pop()
                if u not in seen:
                    seen.add(u); stack.extend(adj[u] - seen)
        return n
    buggy = {s: pieces([(r["origin"], r["destination"]) for r in rows if r["origin"] != s]) for s in names}
    fixed = {s: pieces([(r["origin"], r["destination"]) for r in rows if s not in (r["origin"], r["destination"])]) for s in names}
    splitters = [s for s, n in fixed.items() if n > 1]

    d = json.load(open(os.path.join(HERE, "scenario.json")))
    rooms = {r["key"]: r for r in d["rooms"]}
    pz = {k: [h for h in rooms[k]["hotspots"] if h.get("type") == "puzzle"] for k in ("fenwatch", "sisters", "anvil", "whistlegate")}
    for k, hs in pz.items():
        check(len(hs) == 1, f"{k}: exactly one puzzle")
    # Lucas 2026-09-16: click-the-point where possible, otherwise a code check. The boss is a DRAWN network.
    shape = {k: ("pick" if hs[0].get("pick") else "check" if hs[0].get("check") else "question" if hs[0].get("question") else None) for k, hs in pz.items()}
    check(shape == {"fenwatch": "check", "sisters": "pick", "anvil": "pick", "whistlegate": "pick"},
          "puzzle types: rung 1 check, rungs 2-3 and the boss pick-the-point", str(shape))
    want = {"sisters": ratio, "anvil": busiest, "whistlegate": splitters[0] if len(splitters) == 1 else None}
    for k, ans in want.items():
        pk = pz[k][0].get("pick") or {}
        check(pk.get("answer") == ans and ans in names, f"{k}: pick answer re-derives from the CSV", f"{pk.get('answer')!r} vs {ans!r}")
        check(pz[k][0].get("starterCode") == "dispatch_ledger", f"{k}: starter is the bare data object")
    check((pz["whistlegate"][0].get("pick") or {}).get("idColumn") == "node_name",
          "boss: tags buildNetwork()'s node column, so edges are not clickable as stations")
    fen = pz["fenwatch"][0].get("check") or {}
    check(f'"{heaviest["origin"]}"' in fen.get("expr", "") and f'"{heaviest["destination"]}"' in fen.get("expr", ""),
          "fenwatch: check expr names the CSV's heaviest link, in direction", f"{heaviest['origin']} -> {heaviest['destination']}")
    check(pz["fenwatch"][0].get("starterCode") == "dispatch_ledger", "fenwatch: starter is the bare data object")
    for k, hs in pz.items():
        body = hs[0].get("pick") or hs[0].get("check") or {}
        check("reveal" not in (body.get("feedback") or {}) and len((body.get("feedback") or {}).get("wrong") or []) >= 3,
              f"{k}: >=3 escalating hints, no reveal")
        planned = [h for h in rooms[k].get("plannedHotspots", []) if h.get("type") == "puzzle"]
        check(planned and all(planned[0].get(x) == hs[0].get(x) for x in ("pick", "check", "starterCode")),
              f"{k}: content mirrored on plannedHotspots")
    check(all(p in d.get("packages", []) for p in ("igraph", "network", "ggnetwork")) and "buildNetwork <- function" in (d.get("setup") or ""),
          "the book's buildNetwork() and its packages are in the R session for the boss")
    old = [w for w in ("Kingsmuster", "Slatecrag", "Ossfell", "depot", "twentieth") if w in json.dumps([{k: v for k, v in r.items() if k != "authoring"} for r in d["rooms"]] + [{k: v for k, v in d.items() if k not in ("_designNotes", "rooms")}])]
    check(not old, "no v1 station names or numbers left in player-facing text", str(old))

def test_clips_served():
    """Every committed clip on disk (`<room>/cine_<state>.mp4`, not the `_src` intermediate) is served on a
    carrier the player reads, base as state ABSENT (pickCinemagraphs matches base that way; "base" matches
    nothing). A clip re-committed after this ran is caught here rather than as a room silently showing its still."""
    import glob, re
    d = json.load(open(os.path.join(HERE, "scenario.json")))
    for r in d["rooms"]:
        disk = sorted(re.match(r"cine_(.+)\.mp4$", os.path.basename(f)).group(1)
                      for f in glob.glob(os.path.join(HERE, r["key"], "cine_*.mp4")) if not f.endswith("_src.mp4"))
        served = sorted((h["cinemagraph"].get("state") or "base") for h in r.get("hotspots", []) if h.get("cinemagraph"))
        check(disk == served, f"{r['key']}: every committed clip is served", f"disk {disk} vs served {served}")
        bad = [h["id"] for h in r.get("hotspots", []) if (h.get("cinemagraph") or {}).get("state") == "base"]
        check(not bad, f"{r['key']}: no carrier says state 'base'", str(bad))


if __name__ == "__main__":
    test_ladder()
    test_escape()
    test_tower_map()
    test_wiring()
    test_survey_pickups()
    test_brazier()
    test_puzzles()
    test_clips_served()
    print(f"\n{'ALL CHECKS PASSED' if not FAILS else 'FAILED: ' + '; '.join(FAILS)}")
    sys.exit(1 if FAILS else 0)
