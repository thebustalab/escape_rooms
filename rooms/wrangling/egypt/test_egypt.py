#!/usr/bin/env python3
"""
test_egypt.py — regression guards for the wrangling/egypt scenario ("The Manifest").

Pins the parts that can silently break WITHOUT a browser: the four group_by/summarise answers staying in
lockstep with the real cargo data + the wired puzzles, the Simpson's-paradox FLIP (the whole teaching
point), the DATA-FREE escape's uniquely-solvable grid key, the room/door graph (a hub with a gated skiff),
the nine collectable seals, and the decoder key. Run: python3 test_egypt.py   (stdlib only.)

Failure modes it guards:
  - wine_cargo.csv changes and a room's verified winner (red / Argitis / Chios / Thasos) silently stops
    matching the wired option text;
  - the FLIP collapses — the count-weighted shortcut (market_boast) and the varietal-balanced regroup
    (library) stop landing on DIFFERENT islands, so the Simpson's-paradox lesson quietly dies;
  - the escape's seal cards drift so the queue (max 17 / n 5 / min 10) no longer has the UNIQUE solution
    [size, shape, colour] — or a verb row stops having three distinct values, so a target is ambiguous;
  - a gateless room's onward door reverts to `forward` (it would lock forever — no primary gate), or a
    room loses the back door that makes an opt-in seal pickup retrievable (Lucas: NO auto-pickup);
  - the skiff loses its `availableWhen` gate and the lighthouse becomes reachable before the boss;
  - a `reveal` sneaks back in, or a starter leaks the solution (the boss starter is deliberately buggy);
  - the Pharos finale regresses: the grid re-takes `endsEscape` from the dial, the dial reverts to an inert
    `switch`, loses its gate, or its beam-on-ship variant stops matching the state the dial actually sets;
  - the decoder key WRANGLING_EGYPT_KEY drifts out of lockstep with the four graded rooms.
"""
import csv, itertools, json, os, re, sys
from collections import defaultdict
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "data", "wine_cargo.csv")
SCEN = os.path.join(HERE, "scenario.json")
DECODER = os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R")

fails = []
def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond: fails.append(msg)

def group_mean(rows, key, val):
    d = defaultdict(list)
    for r in rows:
        d[r[key]].append(float(r[val]))
    return {k: mean(v) for k, v in d.items()}

def winner(d):
    return max(d.items(), key=lambda kv: kv[1])[0]


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    doc = json.load(open(SCEN, encoding="utf-8"))
    rooms = {r["key"]: r for r in doc["rooms"]}
    planned = {k: (r.get("plannedHotspots") or []) for k, r in rooms.items()}
    def one(rk, typ):
        m = [h for h in planned[rk] if h["type"] == typ]
        return m[0] if m else None

    print("== answers re-derived from the data ==")
    s1 = group_mean(rows, "type", "sulphates")
    s2 = group_mean(rows, "varietal", "alcohol")
    s3 = group_mean(rows, "region", "quality_score")
    cell = defaultdict(list)
    for r in rows:
        cell[(r["region"], r["varietal"])].append(float(r["quality_score"]))
    per = defaultdict(list)
    for (reg, var), v in cell.items():
        per[reg].append(mean(v))
    boss = {reg: mean(ms) for reg, ms in per.items()}

    check(winner(s1) == "red", f"S1 winner == red (got {winner(s1)})")
    check(round(s1["red"], 2) == 0.66 and round(s1["white"], 2) == 0.49,
          f"S1 means red 0.66 / white 0.49 (got {s1['red']:.3f} / {s1['white']:.3f})")
    check(winner(s2) == "Argitis", f"S2 winner == Argitis (got {winner(s2)})")
    check(round(s2["Argitis"], 1) == 13.8, f"S2 Argitis mean 13.8 (got {s2['Argitis']:.2f})")
    check(winner(s3) == "Chios", f"S3 shortcut winner == Chios (got {winner(s3)})")
    check(round(s3["Chios"], 2) == 7.28, f"S3 Chios 7.28 (got {s3['Chios']:.2f})")
    check(winner(boss) == "Thasos", f"BOSS balanced winner == Thasos (got {winner(boss)})")
    check(round(boss["Thasos"], 2) == 7.43, f"BOSS Thasos 7.43 (got {boss['Thasos']:.2f})")

    print("== the Simpson's-paradox FLIP (the teaching point) ==")
    check(winner(s3) != winner(boss), "shortcut and regroup land on DIFFERENT islands")
    order = sorted(boss, key=lambda k: -boss[k])
    check(order[-1] == "Chios", f"Chios falls to LAST under the balanced regroup (got {order})")
    prem = {"Aminean", "Apian", "Eugenia"}
    mix = {}
    for reg in s3:
        sub = [r for r in rows if r["region"] == reg]
        mix[reg] = 100.0 * sum(1 for r in sub if r["varietal"] in prem) / len(sub)
    check(mix["Chios"] > 80 and mix["Thasos"] < 20,
          f"the confound survives: Chios premium-heavy, Thasos common-heavy ({mix['Chios']:.0f}% / {mix['Thasos']:.0f}%)")

    print("== wired option text matches the data ==")
    for rk, want in (("deck", "red — averaging 0.66"),
                     ("market_boast", "Chios — 7.28"),
                     ("library", "Thasos — 7.43")):
        p = one(rk, "puzzle"); q = p["question"]
        check(q["options"][q["correct"]] == want,
              f"{rk} correct option == {want!r} (got {q['options'][q['correct']]!r})")
        check(len(q["options"]) >= 6, f"{rk} has >=6 options (got {len(q['options'])})")
        check("reveal" not in q.get("feedback", {}), f"{rk} has no `reveal`")
    pick = one("market_price", "puzzle")["pick"]
    check(pick["answer"] == "Argitis" and pick["idColumn"] == "varietal",
          "market_price pick answers Argitis on the varietal column")
    check("reveal" not in pick.get("feedback", {}), "market_price pick has no `reveal`")
    # starters: bare object name everywhere except the boss (deliberately buggy repair code)
    for rk in ("deck", "market_boast", "market_price"):
        check(one(rk, "puzzle")["starterCode"].strip() == "wine_cargo",
              f"{rk} starterCode is the bare data object")
    bstart = one("library", "puzzle")["starterCode"]
    check("group_by(region)" in bstart and "varietal" not in bstart,
          "boss starter is the NAIVE (buggy) pipeline and does not contain the fix")

    print("== the data-free escape ==")
    grid = one("pharos", "grid")
    seals = [h for hs in planned.values() for h in hs if str(h.get("pickup", "")).startswith("Seal ")]
    check(len(seals) == 9, f"nine collectable seals across the scenario (got {len(seals)})")
    cards = []
    for s in seals:
        m = re.match(r"Seal (\d+) — (\w+) · (\w+) · (\w+) · numeral (\d+)", s["pickup"])
        check(bool(m), f"seal pickup line parses: {s.get('pickup')!r}")
        if m:
            cards.append((m.group(2), m.group(3), m.group(4), int(m.group(5))))
    TRAIT = {"colour": 0, "shape": 1, "size": 2}
    def piles(t):
        d = defaultdict(list)
        for c in cards:
            d[c[TRAIT[t]]].append(c[3])
        return list(d.values())
    VERB = {"n": lambda t: max(len(p) for p in piles(t)),
            "max": lambda t: max(sum(p) for p in piles(t)),
            "min": lambda t: min(sum(p) for p in piles(t))}
    for v in VERB:
        vals = [VERB[v](t) for t in ("colour", "shape", "size")]
        check(len(set(vals)) == 3, f"verb {v!r} gives 3 DISTINCT values across traits ({vals})")
    queue = [("max", 17), ("n", 5), ("min", 10)]
    sols = [c for c in itertools.product(("colour", "shape", "size"), repeat=3)
            if all(VERB[v](c[i]) == tgt for i, (v, tgt) in enumerate(queue))]
    check(sols == [("size", "shape", "colour")], f"the queue has the UNIQUE solution [size, shape, colour] (got {sols})")
    check(grid["answer"] == {"step1": "size", "step2": "shape", "step3": "colour"},
          "the wired grid answer matches that derivation")
    check("endsEscape" not in grid, "the grid does NOT end the escape — it opens the door (the dial is the finale)")
    check(grid.get("availableWhen") == {"solved": "library"}, "the grid can't be keyed before the boss")
    # the ceremonial finale: the player's own hand turns the beam onto their ship
    dial = one("pharos", "dial")
    check(bool(dial), "the lamp dial is a real engine `dial` (not an inert `switch`)")
    check(dial.get("endsEscape") is True, "the DIAL ends the escape")
    check(dial.get("availableWhen") == {"solved": "pharos"},
          "the dial is gated until the lantern door's grid is solved")
    check(bool(dial.get("lockedBody")), "the gated dial has a diegetic lockedBody")
    check(bool(dial.get("sfx")), "turning the dial plays a sound")
    check(len(dial.get("states") or []) == 1, "one dial, ONE target, one motion — never a second puzzle")
    check(rooms["pharos"].get("onSolve") == [{"set": "lantern_open", "to": "yes"}],
          "solving the grid records that the lantern door is open")
    # the payoff ART: a state-variant that fires on the dial's own key
    ph_els = {e["id"]: e for e in rooms["pharos"]["authoring"]["sceneSpec"]["elements"]}
    beam = (ph_els.get("harbour_below") or {}).get("variants") or []
    check(len(beam) == 1 and beam[0].get("state") == "beam_on_ship",
          "the harbour-below view declares the beam-on-ship variant")
    check(beam and beam[0].get("when") == {"eq": [dial.get("key"), dial["states"][0]["value"]]},
          "that variant fires on exactly the state the dial sets")
    check(bool(beam and beam[0].get("reveal")), "the beam variant carries a reveal prompt (so its art gets generated)")
    labels = " ".join(i["label"] for i in grid["items"])
    check("17" in labels and "5" in labels and "10" in labels, "the grid columns show the queue targets")

    print("== room + door graph ==")
    WANT = {("deck", "hold"), ("deck", "quay"), ("quay", "deck"), ("quay", "boat"), ("boat", "pharos"),
            ("quay", "emporion"), ("emporion", "market_price"), ("market_price", "market_boast"),
            ("market_boast", "canopic"), ("canopic", "library")}
    doors = defaultdict(list)
    for rk, r in rooms.items():
        for e in r["authoring"]["sceneSpec"]["elements"]:
            if e.get("door"):
                doors[rk].append((e["door"].get("to"), e["door"].get("direction", "forward")))
    have = {(a, to) for a, ds in doors.items() for to, _ in ds}
    for a, b in sorted(WANT):
        check((a, b) in have, f"door {a} -> {b} exists")
    graded = {"deck", "market_price", "market_boast", "library"}
    for rk, ds in doors.items():
        if rk in graded:
            continue
        for to, d in ds:
            check(d != "forward",
                  f"{rk} is gateless so its {to} door must not be `forward` (would lock forever) — got {d}")
    for rk in rooms:
        if rk == "deck":
            continue
        check(any(d == "back" for _, d in doors[rk]),
              f"{rk} has a back door (an opt-in seal must stay retrievable)")
    skiff = [h for h in planned["quay"] if h["type"] == "door"]
    check(bool(skiff) and skiff[0].get("availableWhen") == {"solved": "library"},
          "the skiff is gated on the boss")
    check(bool(skiff and skiff[0].get("lockedBody")), "the gated skiff has a diegetic lockedBody")
    check(rooms["pharos"].get("phase") == "escape", "pharos is the escape-phase room")
    check(bool(rooms["library"].get("deliverable")), "the boss carries a deliverable")
    check("entry" not in rooms["deck"], "the first room has no entry card")
    for rk in rooms:
        if rk != "deck":
            check(bool(rooms[rk].get("entry")), f"{rk} has an entry card")

    print("== decoder lockstep ==")
    txt = open(DECODER, encoding="utf-8").read()
    m = re.search(r"WRANGLING_EGYPT_KEY\s*<-\s*list\((.*?)\n\)", txt, re.S)
    check(bool(m), "WRANGLING_EGYPT_KEY exists in decode_codes.R")
    if m:
        body = m.group(1)
        sid = re.search(r"scenario_id\s*=\s*(\d+)", body)
        vec = re.search(r"correct\s*=\s*c\(([^)]*)\)", body)
        check(sid and int(sid.group(1)) == doc["id"], f"decoder scenario_id == {doc['id']}")
        got = [int(x.strip()) for x in vec.group(1).split(",")] if vec else []
        want = []
        for rk in ("deck", "market_price", "market_boast", "library"):
            p = one(rk, "puzzle")
            want.append(1 if p.get("pick") else p["question"]["correct"])
        check(got == want, f"decoder correct vector == {want} (got {got})")
        check(len(set(want)) > 1, f"the correct index is VARIED across rooms, not a tell ({want})")

    print()
    if fails:
        print(f"{len(fails)} FAILURE(S)")
        for f in fails: print("  -", f)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
