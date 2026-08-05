#!/usr/bin/env python3
"""
test_airship.py — regression guards for the data_vis2/airship scenario (stdlib only; python3).

The airship is the POST-test twin of hospital: same chapter (Data Visualization II), same question
*shape* (read a relationship / group / region / within-group split off a multi-aesthetic plot), on the
`solvents` dataset instead of `alaska_lake_data`. This file guards the parts that can silently break
WITHOUT a browser: the four analysis MCQ answers staying in lockstep with the real solvents data + the
decoder key, and the dial/mapview/lock escape staying in lockstep with the regenerated map codes.
Run: python3 test_airship.py

Failure modes it guards:
  - solvents.csv changes and a room's verified answer (won't-mix -> higher polarity / densest family =
    chlorinated / the within-alcohol polarity-vs-density TRAP / the nearest-0.6 immiscible-light solvent
    = 1-butanol) silently stops matching the wired correct option;
  - a correct-index drifts out of lockstep with decode_codes.R's DATA_VIS2_AIRSHIP_KEY = c(1,3,2,4);
  - `nest/make_starchart.py` is re-run, the invariant star changes, and the captain's helm-lock answer
    is not updated to match — the escape becomes unsolvable (or gains two answers);
  - the room-3 taught trap is weakened (polarity no longer overlaps within the alcohols, or density no
    longer separates them cleanly), so the "density not polarity" answer stops being the true one;
  - a starter leaks the solving pipeline, an option set drops below six, or a `reveal` sneaks back in;
  - the escape gating (nest unlocks on boss, captain on nest) or the codec `id`/packages drift.

History: room 3 was reworked 2026-07-22 from a region-combine read to the alcohol facet TAUGHT TRAP
(polarity overlaps within the alcohols; density/chain-length is the real separator; the cure, 1-butanol,
is itself one of the polar-but-immiscible exceptions). Correct index stayed 2, so the decoder key is
unchanged. See notes.md.
"""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

SITE = HERE
for _ in range(8):
    if os.path.exists(os.path.join(SITE, "phylochemistry", "sample_data", "solvents.csv")):
        break
    SITE = os.path.dirname(SITE)
CSV = os.path.join(SITE, "phylochemistry", "sample_data", "solvents.csv")

fails = []
def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)

def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    def num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None
    for r in rows:
        r["_pol"] = num(r["relative_polarity"])
        r["_den"] = num(r["density"])
        r["_mix"] = str(r["miscible_with_water"]).strip().upper() == "TRUE"

    scen = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
    R = {r["key"]: r for r in scen["rooms"]}
    # Pre-art the authored content lives on `plannedHotspots` (boxes placed + content attached at the
    # harness commit, which populates `hotspots`); post-art it lives on `hotspots`. Read whichever is
    # present so this guard holds across the room's whole lifecycle.
    def spots(rk):
        return R[rk].get("hotspots") or R[rk].get("plannedHotspots") or []
    def puzzle(rk):
        return next(h for h in spots(rk) if h.get("type") == "puzzle")

    print("== analysis answers vs data (each correct option is the verified answer) ==")

    # room1 — solvents that mix with water sit at HIGHER relative polarity
    mix_pol = [r["_pol"] for r in rows if r["_mix"] and r["_pol"] is not None]
    non_pol = [r["_pol"] for r in rows if not r["_mix"] and r["_pol"] is not None]
    mean = lambda xs: sum(xs) / len(xs)
    q1 = puzzle("room1")["question"]
    check(mean(mix_pol) > mean(non_pol) + 0.1,
          "water-mixers sit at higher polarity (%.3f vs %.3f)" % (mean(mix_pol), mean(non_pol)))
    check(q1["correct"] == 1 and "HIGHER" in q1["options"][1].upper(),
          "room1 correct = idx 1 (the HIGHER-polarity option)")

    # room2 — most solvents denser than water are chlorinated
    dense = [r for r in rows if r["_den"] is not None and r["_den"] > 1]
    cats = {}
    for r in dense:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    top_cat = max(cats, key=cats.get)
    q2 = puzzle("room2")["question"]
    check(top_cat == "chlorinated" and cats["chlorinated"] > sorted(cats.values())[-2] if len(cats) > 1 else True,
          "the densest-than-water family is chlorinated (%s of %d dense; counts %s)" % (cats.get("chlorinated"), len(dense), cats))
    check(q2["correct"] == 3 and q2["options"][3] == "chlorinated",
          "room2 correct = idx 3 = chlorinated")

    # room3 — TAUGHT TRAP: within the alcohols, polarity does NOT separate mixers from non-mixers,
    # but density (chain length) does, cleanly. So the "density not polarity" answer is the true one.
    alc = [r for r in rows if r["category"] == "alcohol" and r["_pol"] is not None and r["_den"] is not None]
    amix = [r for r in alc if r["_mix"]]
    anon = [r for r in alc if not r["_mix"]]
    check(len(amix) >= 2 and len(anon) >= 2, "alcohols split into mixers and non-mixers (%d / %d)" % (len(amix), len(anon)))
    # polarity OVERLAPS: some non-mixer is MORE polar than some mixer (2-propanol mixes < 1-butanol doesn't)
    pol_overlap = min(r["_pol"] for r in amix) < max(r["_pol"] for r in anon)
    check(pol_overlap,
          "polarity does NOT separate the alcohols (a mixer is less polar than a non-mixer: %.3f < %.3f)"
          % (min(r["_pol"] for r in amix), max(r["_pol"] for r in anon)))
    # density SEPARATES cleanly: every mixer lighter than every non-mixer, no overlap
    den_clean = max(r["_den"] for r in amix) < min(r["_den"] for r in anon)
    check(den_clean,
          "density DOES separate the alcohols cleanly (mixers max %.3f < non-mixers min %.3f)"
          % (max(r["_den"] for r in amix), min(r["_den"] for r in anon)))
    q3 = puzzle("room3")["question"]
    check(q3["correct"] == 2 and "density" in q3["options"][2].lower() and "polarity" in q3["options"][2].lower(),
          "room3 correct = idx 2 (the 'density not polarity' trap answer)")

    # boss — immiscible + density < 1 + relative_polarity nearest 0.6 -> 1-butanol (single winner)
    cand = [r for r in rows if not r["_mix"] and r["_den"] is not None and r["_den"] < 1 and r["_pol"] is not None]
    cand.sort(key=lambda r: abs(r["_pol"] - 0.6))
    winner = cand[0]["solvent"]
    margin = abs(cand[1]["_pol"] - 0.6) - abs(cand[0]["_pol"] - 0.6)
    q4 = puzzle("boss")["question"]
    check(winner == "1-butanol",
          "nearest-0.6 immiscible light solvent is 1-butanol (got %s; runner-up gap %.3f)" % (winner, margin))
    check(margin > 0.02, "1-butanol wins the boss by a comfortable margin (%.3f)" % margin)
    check(q4["correct"] == 4 and q4["options"][4].lower().replace(" ", "").startswith("1-butanol".replace(" ", "")),
          "boss correct = idx 4 = 1-Butanol")

    print("== MCQ hygiene + decoder lockstep ==")
    correct = [puzzle(rk)["question"]["correct"] for rk in ("room1", "room2", "room3", "boss")]
    check(correct == [1, 3, 2, 4], "correct indices == DATA_VIS2_AIRSHIP_KEY c(1,3,2,4): %s" % correct)
    for rk in ("room1", "room2", "room3", "boss"):
        q = puzzle(rk)["question"]
        check(len(q["options"]) >= 6, "%s has >= 6 options (%d)" % (rk, len(q["options"])))
        check("reveal" not in q.get("feedback", {}), "%s has no feedback.reveal" % rk)
    for rk in ("room1", "room2", "room3"):   # practice starters give nothing away (boss = the assessed read)
        sc = str(puzzle(rk).get("starterCode", ""))
        check("ggplot(" not in sc and "filter(" not in sc and "facet" not in sc,
              "%s starterCode has no solving pipeline (bare data object)" % rk)

    print("== escape lockstep: star-astrolabe (dial -> mapview -> lock) ==")
    codes = json.load(open(os.path.join(HERE, "nest", "codes.json"), encoding="utf-8"))
    ans = codes["answer_star"]
    lock = next(h for h in spots("room2") if h.get("type") == "lock")  # moved onto the deck 2026-07-31 — it now gates the bridge door
    check(str(lock.get("answer", "")).upper() == ans.upper(),
          "bridge-hatch keypad answer (%s) == the invariant star from make_starchart.py (%s)" % (lock.get("answer"), ans))
    # all star names the same length, and the lock length matches (fixed-length lock — Lucas's constraint)
    name_lens = {len(n) for n in codes["stars"]}
    check(name_lens == {codes["name_length"]},
          "all star names are the same length (%s); name_length=%d" % (sorted(name_lens), codes["name_length"]))
    check(str(lock.get("length")) == str(codes["name_length"]) == str(len(ans)),
          "lock length (%s) == star-name length (%d)" % (lock.get("length"), codes["name_length"]))
    # exactly one star holds the Anchor across all three plates, and each plate has >=2 (drift)
    pp = codes["per_plate_in_house"]
    invariant = set.intersection(*[set(v) for v in pp.values()]) if pp else set()
    check(invariant == {ans}, "exactly one star holds the Anchor on all three plates == %s (got %s)" % (ans, invariant or "none"))
    check(len(pp) == 3 and all(len(v) >= 2 for v in pp.values()),
          "three plates, each with >=2 stars in the Anchor (the drift): %s" % {k: len(v) for k, v in pp.items()})
    for f in ("map_m1.png", "map_m2.png", "map_m3.png"):
        check(os.path.exists(os.path.join(HERE, "nest", f)), "star plate %s exists" % f)
    dial = next(h for h in spots("nest") if h.get("type") == "dial")  # co-located with the astrolabe
    mapview = next(h for h in spots("nest") if h.get("type") == "mapview")
    check(dial.get("key") == mapview.get("key") == "mapping",
          "plate-dial and astrolabe share the `mapping` gameState key (co-located in the nest)")
    check(len(dial.get("states", [])) == 3, "the astrolabe plate-dial has three states (%d)" % len(dial.get("states", [])))
    check(set((mapview.get("images") or {}).keys()) == {s["value"] for s in dial.get("states", [])},
          "mapview has one plate image per dial state")
    # the engine's openClue renders `h.body`, NOT `h.text` — a clue authored under `text` shows blank
    starlog = next(h for h in spots("nest") if h.get("type") == "clue")
    check(bool(starlog.get("body")) and not starlog.get("text"),
          "the star-log clue carries `body` (the field openClue renders), not `text`")

    print("== scenario graph ==")
    check(scen.get("id") == 9, "scenario id is 9")
    check({"dplyr", "ggplot2", "readr"}.issubset(scen.get("packages", [])),
          "packages include ggplot2 + dplyr + readr")
    check(R.get("boss", {}).get("isBoss") is True, "boss is flagged isBoss")
    check(R.get("nest", {}).get("phase") == "escape",
          "nest is phase:escape (ungraded, out of codec)")
    check("bridge" not in R, "the bridge room was removed — the escape ends on the weather deck (2026-08-05)")
    check(all(R[k].get("unlockedWhen") is True for k in R),
          "open world: every room is freely enterable (unlockedWhen True)")
    check(bool(scen.get("escapeDone")), "scenario has an escapeDone finish screen")

    print("== nav graph: re-locked doors (2026-07-31) + puzzle-gated order ==")
    DOORS = {}
    for r in scen["rooms"]:
        for h in spots(r["key"]):
            if h.get("type") == "door" and h.get("to"):
                DOORS[(r["key"], h["to"])] = h
    # (a) the two interior progression doors are LOCKED forward doors gated on their own room's puzzle
    for (frm, to, who) in [("room1", "room3", "apothecary->hold hatch"),
                           ("room3", "boss", "hold->engine bulk-door")]:
        d = DOORS.get((frm, to), {})
        check(d.get("direction") == "forward" and not d.get("requires"),
              "%s is a forward door gated on its own room's puzzle" % who)
    # (b) the mast to the nest: an open passage, but sealed on the CURE (too queasy until boss solved)
    mast = DOORS.get(("room2", "nest"), {})
    check(mast.get("availableWhen") == {"solved": "boss"} and bool(mast.get("lockedBody")),
          "the mast to the nest is gated on the cure (boss) with a diegetic lockedBody: %s" % (mast.get("availableWhen"),))
    # (c) the escape now ENDS on the weather deck: the former forward-to-bridge door is the 'take the
    #     wheel' door — forward, gated on the deck bearing-keypad, no `to`, fires escapeDone (2026-08-05).
    wheel = next((h for h in spots("room2") if h.get("type") == "door" and h.get("endsEscape")), None)
    check(wheel is not None and wheel.get("direction") == "forward"
          and wheel.get("requires") == "the_bridge_hatch_keypad" and not wheel.get("to"),
          "room2 'take the wheel' door: forward, requires the bridge-hatch keypad, no target, fires escapeDone")
    # everything else stays an open passage
    for edge in [("room1", "room2"), ("room2", "room1"), ("room3", "room1"),
                 ("boss", "room3"), ("nest", "room2")]:
        check(DOORS.get(edge, {}).get("direction") == "open", "%s->%s stays an open passage" % edge)
    # the weather deck is still the hub — reaches the apothecary and the crow's nest (bridge removed)
    deck = {h.get("to") for h in spots("room2") if h.get("type") == "door"}
    check({"room1", "nest"} <= deck, "weather-deck hub reaches apothecary + nest: %s" % deck)
    check(not any(h.get("to") == "nest" for h in spots("boss")), "crow's nest is NOT hung off the engine-room boss")
    # progression is ALSO enforced on the PUZZLES via availableWhen
    def gate(rk, t="puzzle"):
        return next((h.get("availableWhen") for h in spots(rk) if h.get("type") == t), "NO-HOTSPOT")
    check(gate("room1") is None, "room1 puzzle is available from the start")
    check(gate("room2") == {"solved": "room1"}, "room2 puzzle gated on room1: %s" % (gate("room2"),))
    check(gate("room3") == {"solved": "room2"}, "room3 puzzle gated on room2: %s" % (gate("room3"),))
    check(gate("boss") == {"allSolved": ["room1", "room2", "room3"]},
          "boss puzzle gated to the engine room on all three readings: %s" % (gate("boss"),))
    for rk in ("room2", "room3", "boss"):
        check(bool(next((h.get("lockedBody") for h in spots(rk) if h.get("type") == "puzzle"), None)),
              "%s gated puzzle has a diegetic lockedBody" % rk)
    # the escape lock now lives ON THE DECK (room2), gating the bridge door; dead until cured
    check(gate("room2", "lock") == {"solved": "boss"},
          "the bridge-hatch keypad (on the deck) is gated on the cure (boss solved): %s" % (gate("room2", "lock"),))

    print("\n%d failure(s)" % len(fails))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
