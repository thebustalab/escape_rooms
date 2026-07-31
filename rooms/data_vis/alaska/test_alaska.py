#!/usr/bin/env python3
"""
test_alaska.py — regression guards for the data_vis/alaska scenario ("Signal in the Cold").

Pins the parts that can silently break WITHOUT a browser: the four room answers staying in lockstep with
the real data + the wired puzzles (room1/room2 MCQ, room3/boss the Type-4 pick-the-point plot-clicks),
the escape keypad code, and the decoder key. Run: python3 test_alaska.py

The dataset is the public sample_data CSV the player fetches at runtime (datasets[].url ->
alaska_lake_data.csv); this test reads the local copy under phylochemistry/sample_data/.
numpy is imported to match the henges pick-room twin and to do the single-winner margin arithmetic; the
rest is stdlib.

Ladder (see notes.md "Ladder REDESIGN", 2026-07-22): room1 MCQ (pH > 8 threshold + distinct/count),
room2 MCQ (compound filter park==NOAT & element==Mg), room3 pick (chloride outlier), boss pick (warmest
water — resist the primed chloride answer). Room order room1, room2, room3, boss.

Failure modes it guards:
  - the CSV changes and a room's verified answer silently stops matching the wired puzzle
    (room1 North_Killeak is the sole pH>8 lake; room2 Feniak is the top-Mg NOAT lake; room3 North_Killeak
     is the chloride outlier; boss Lava_Lake is the warmest — NOT the chloride lake everyone chased);
  - room2's compound filter stops biting — the global Mg max must stay North_Killeak (BELA), the sharp
    distractor, so dropping the NOAT condition gives the wrong lake;
  - the boss trap collapses — North_Killeak (the chloride outlier / where the search party flew) must
    stay a decoy on water_temp, not the warmest;
  - an MCQ's correct index points at the wrong option text (the 2026-07-22 hawaii-room2 duplicate-option
    class of bug), or an option set drops below six / grows a duplicate;
  - the decoder key DATA_VIS_ALASKA_KEY drifts out of lockstep with the built graded rooms — it MUST be
    c(3, 2, 1, 1): the two MCQ rooms encode their 0-based correct index, the two pick rooms encode 1;
  - the escape keypad code drifts off the Secret-of-the-Unicorn mask overlay (surviving cell -> N0KR).

Room 2's MCQ `starterCode` deliberately carries the colleague's BROKEN filter+ggplot pipeline — that's the
in-story "mistakes" the player is meant to notice (Lucas, 2026-07-29), an accepted exception to the
bare-data-starter convention (like hawaii room3's repair puzzle), NOT a bug — so it is not flagged. The
room3/boss pick `feedback.reveal` answer-leak (2026-07-29) has been fixed (blanked, matching henges/hawaii).
Generic content hygiene — no-reveal, >=6 options, no duplicate options, decoder-key lockstep — is enforced
CENTRALLY by `authoring/validate_assets.py` + `decoder/validate_keys.py` across ALL scenarios, so this test
holds only Alaska's BESPOKE answer re-derivation from the CSV (the part that can't be generic).
"""
import csv, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "..", "..", "..", "phylochemistry", "sample_data", "alaska_lake_data.csv")
SCEN = os.path.join(HERE, "scenario.json")
DECODER = os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R")
GRIDS = os.path.join(HERE, "escape_grids", "grids.json")

fails = []
def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond: fails.append(msg)

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))

    # ---- per-lake facts derived straight from the data ----
    park, ph, temp = {}, {}, {}
    mg, cl = {}, {}                                   # per-lake magnesium / chloride
    for r in rows:
        lk = r["lake"]
        park[lk] = r["park"]
        ph[lk] = num(r["pH"]); temp[lk] = num(r["water_temp"])
        if r["element"] == "Mg": mg[lk] = num(r["mg_per_L"])
        if r["element"] == "Cl": cl[lk] = num(r["mg_per_L"])

    # room1: how many / which lakes clear pH > 8 (threshold filter + distinct/count)
    over8 = sorted(l for l, v in ph.items() if v is not None and v > 8)
    room1_ans = over8[0] if len(over8) == 1 else None
    ph_next = max((v for l, v in ph.items() if l not in over8 and v is not None), default=None)

    # room2: among NOAT lakes, the one with the most magnesium (compound filter)
    noat_mg = sorted(((v, l) for l, v in mg.items() if park[l] == "NOAT" and v is not None), reverse=True)
    room2_ans = noat_mg[0][1]
    noat_margin = noat_mg[0][0] / noat_mg[1][0]                     # winner / runner-up
    global_mg = max(mg, key=mg.get)                                 # trap: drop the NOAT filter

    # room3: the chloride outlier across all lakes (plot-pick)
    cl_sorted = sorted(cl.items(), key=lambda kv: kv[1], reverse=True)
    room3_ans = cl_sorted[0][0]
    cl_margin = cl_sorted[0][1] / cl_sorted[1][1]

    # boss: the warmest lake (plot-pick, resisting the primed chloride answer)
    temp_sorted = sorted(((v, l) for l, v in temp.items() if v is not None), reverse=True)
    boss_ans = temp_sorted[0][1]
    temp_margin = temp_sorted[0][0] / temp_sorted[1][0]

    print("== analysis answers vs data ==")
    check(over8 == ["North_Killeak_Lake"], f"room1: North_Killeak_Lake is the SOLE lake with pH>8 (got {over8})")
    check(round(ph[room1_ans], 2) == 8.04, f"room1: North_Killeak pH is 8.04 (got {ph.get(room1_ans)})")
    check(ph_next is not None and ph_next < 8, f"room1: next-highest pH is under 8, single winner (got {ph_next})")
    check(room2_ans == "Feniak_Lake", f"room2: top-Mg NOAT lake is Feniak_Lake (got {room2_ans})")
    check(noat_margin >= 2.5, f"room2: Feniak's Mg margin over the next NOAT lake is >=2.5x (got {noat_margin:.2f}x)")
    check(global_mg == "North_Killeak_Lake" and park[global_mg] == "BELA",
          f"room2 TRAP: global Mg max is North_Killeak_Lake in BELA — the compound filter genuinely bites (got {global_mg}/{park.get(global_mg)})")
    check(room3_ans == "North_Killeak_Lake", f"room3: chloride outlier is North_Killeak_Lake (got {room3_ans})")
    check(cl_margin > 3.0, f"room3: chloride outlier margin > 3x the next lake (got {cl_margin:.2f}x)")
    check(boss_ans == "Lava_Lake", f"boss: warmest lake is Lava_Lake (got {boss_ans})")
    check(temp_margin > 1.0, f"boss: Lava_Lake is a single warmest winner (got {temp_margin:.3f}x, +{(temp_margin-1)*100:.1f}%)")
    check(room3_ans != boss_ans and temp[room3_ans] < temp_sorted[0][0],
          f"boss TRAP: the chloride outlier (North_Killeak, {temp.get(room3_ans)}C) is NOT the warmest — the decoy holds")

    # ---- wired puzzle content matches the data ----
    scen = json.load(open(SCEN, encoding="utf-8"))
    R = {r["key"]: r for r in scen["rooms"]}
    def pz(rk): return [h for h in R[rk]["hotspots"] if h["type"] == "puzzle"][0]
    def lock(rk): return [h for h in R[rk]["hotspots"] if h["type"] == "lock"][0]

    print("== wired puzzles vs data + MCQ hygiene ==")
    # room1 / room2 MCQ — BESPOKE answer checks only (generic hygiene: >=6 options / no dupes / index-in-range
    # is enforced centrally by validate_assets.py + validate_keys.py, not repeated here).
    q1, q2 = pz("room1")["question"], pz("room2")["question"]
    check(q1["correct"] == 3, f"room1 correct index == 3 (got {q1['correct']})")
    check(room1_ans in q1["options"][q1["correct"]] and q1["options"][q1["correct"]].lower().startswith("just one"),
          f"room1 correct option names the sole pH>8 lake (got {q1['options'][q1['correct']]!r})")
    check(q2["correct"] == 2, f"room2 correct index == 2 (got {q2['correct']})")
    check(q2["options"][q2["correct"]] == room2_ans, f"room2 correct option text == Feniak_Lake (got {q2['options'][q2['correct']]!r})")
    check(global_mg in q2["options"], f"room2 keeps North_Killeak as the compound-filter trap distractor (options {q2['options']})")

    # room3 / boss are Type-4 pick-the-point; assert pick.answer matches the data + plot targets the right column
    p3, pb = pz("room3")["pick"], pz("boss")["pick"]
    check(p3["answer"] == room3_ans, f"room3 pick.answer == chloride outlier North_Killeak_Lake (got {p3['answer']!r})")
    check(p3.get("idColumn") == "lake" and 'element == "Cl"' in p3.get("plotCode", ""),
          "room3 pick plots the chloride rows and clicks a lake bar")
    check(pb["answer"] == boss_ans, f"boss pick.answer == warmest Lava_Lake (got {pb['answer']!r})")
    check(pb.get("idColumn") == "lake" and "water_temp" in pb.get("plotCode", ""),
          "boss pick plots water_temp (not the primed chloride variable) and clicks a lake bar")
    check(pb["answer"] != p3["answer"], "boss answer differs from room3 — the setup->subvert pair holds")

    # ---- convention NOT covered by the central validators ----
    print("== starter convention ==")
    # bare-data starter: room1/room3/boss use the bare data object. room2 is DELIBERATELY excluded — it
    # ships the colleague's broken pipeline as the in-story "mistakes" to fix (an accepted repair-puzzle
    # exception, so the central validator doesn't try to police starters). (no-reveal is central now.)
    for rk in ("room1", "room3", "boss"):
        check(pz(rk).get("starterCode") == "alaska_lake_data", f"{rk}: starter is the bare data object")

    # ---- escape: Secret-of-the-Unicorn mask overlay -> N0KR keypad ----
    print("== escape keypad vs mask overlay ==")
    kp = lock("escape1")
    check(kp["answer"] == "N0KR" and kp.get("length") == 4, f"escape1 keypad answer == N0KR, length 4 (got {kp['answer']!r})")
    check(R["escape1"].get("phase") == "escape", "escape1 is phase:escape (ungraded, out of the codec)")
    if os.path.isfile(GRIDS):
        g = json.load(open(GRIDS, encoding="utf-8"))
        masks = [set(tuple(c) for c in cells) for cells in g["mask_open_cells"].values()]
        inter = set.intersection(*masks)
        check(inter == {(g["target_cell"]["row"], g["target_cell"]["col"])},
              f"the three masks intersect in exactly one cell (got {sorted(inter)})")
        r, c = g["target_cell"]["row"], g["target_cell"]["col"]
        idx = (r - 1) * 4 + (c - 1)                                 # 4x4 grid, row-major
        surviving = g["codes_row_major"][idx]
        check(surviving == kp["answer"] == g["winning_code"],
              f"surviving cell ({r},{c}) code {surviving} == keypad answer {kp['answer']} == grids winning_code")

    # ---- decoder lockstep: DATA_VIS_ALASKA_KEY = c(3, 2, 1, 1) (MCQ indices + pick 1) ----
    print("== decoder lockstep ==")
    # build the expected encoded vector straight from the built graded rooms, in room order
    graded = [r for r in scen["rooms"] if r.get("built") and r.get("phase") != "escape"
              and any(h["type"] == "puzzle" for h in r.get("hotspots", []))]
    expected = []
    for r in graded:
        p = [h for h in r["hotspots"] if h["type"] == "puzzle"][0]
        expected.append(p["question"]["correct"] if "question" in p else 1)   # pick/check encode 1 on solve
    check(len(graded) == 4, f"4 built graded rooms (got {len(graded)})")
    check(expected == [3, 2, 1, 1], f"encoded vector from scenario == c(3, 2, 1, 1) (got {expected})")

    dec = open(DECODER, encoding="utf-8").read()
    m = re.search(r"DATA_VIS_ALASKA_KEY\s*<-\s*list\((.*?)\n\)", dec, re.S)
    check(bool(m), "DATA_VIS_ALASKA_KEY present in decode_codes.R")
    if m:
        sid = re.search(r"scenario_id\s*=\s*(\d+)", m.group(1))
        cor = re.search(r"correct\s*=\s*c\(([^)]*)\)", m.group(1))
        vec = [int(x) for x in cor.group(1).replace(" ", "").split(",")] if cor else []
        check(bool(sid) and int(sid.group(1)) == 6, "decoder key scenario_id == 6")
        check(vec == expected, f"decoder key correct == the scenario's encoded vector c(3, 2, 1, 1) (got {vec})")
        check(scen["id"] == 6, "scenario id == 6")

    print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURE(S): " + "; ".join(fails)))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
