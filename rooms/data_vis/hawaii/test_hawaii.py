#!/usr/bin/env python3
"""
test_hawaii.py — regression guards for the data_vis/hawaii scenario ("Saltwater Intrusion").

Pins the parts that can silently break WITHOUT a browser: the four room answers staying in lockstep
with the real data + the wired puzzles (room1/room2/boss MCQ, room3 the repair-the-broken-filter
console-check), and the decoder key. Run: python3 test_hawaii.py  (stdlib only — no numpy needed.)

The dataset is the public sample_data CSV the player fetches at runtime; this test reads the local
copy under phylochemistry/sample_data/.

Failure modes it guards (added 2026-07-28 when room3 was upgraded MCQ -> console-check):
  - the CSV changes and a room's verified answer silently stops matching the wired puzzle
    (room1 aquifer_1 top analyte; room2 aquifer_1 SO4 top well; room3 aquifer_6 Cl sole >250 well;
     boss KEEI_B sodium vs 150);
  - room3's console-check expr drifts off KEEI_B, or room3 silently reverts to an MCQ (which would
    re-encode an option index instead of the console-check's answer=1);
  - an MCQ's correct index points at the wrong option text (the 2026-07-22 room2 duplicate-option bug);
  - the decoder key DATA_VIS_HAWAII_KEY drifts out of lockstep with the built graded rooms — it MUST be
    c(3, 5, 1, 2): MCQ rooms encode their correct index, the console-check room encodes 1.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "..", "..", "..", "phylochemistry", "sample_data", "hawaii_aquifers.csv")
SCEN = os.path.join(HERE, "scenario.json")
DECODER = os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R")

fails = []
def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond: fails.append(msg)

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))

    # ---- answers derived straight from the data ----
    a1 = [r for r in rows if r["aquifer_code"] == "aquifer_1"]
    # room1: within aquifer_1, the analyte reaching the highest abundance
    a1_max = {}
    for r in a1:
        v = num(r["abundance"])
        if v is not None:
            a1_max[r["analyte"]] = max(a1_max.get(r["analyte"], float("-inf")), v)
    room1_ans = max(a1_max, key=a1_max.get)
    # room2: within aquifer_1, the SO4 well with the most sulfate
    a1_so4 = [(r["well_name"], num(r["abundance"])) for r in a1
              if r["analyte"] == "SO4" and num(r["abundance"]) is not None]
    room2_ans = max(a1_so4, key=lambda x: x[1])[0]
    # room3: aquifer_6 chloride wells over the 250 alarm line (the console-check answer)
    a6_cl_over = [r["well_name"] for r in rows if r["aquifer_code"] == "aquifer_6"
                  and r["analyte"] == "Cl" and (num(r["abundance"]) or 0) > 250]
    # boss: KEEI_B sodium vs the 150 line
    keeib_na = [num(r["abundance"]) for r in rows if r["well_name"] == "KEEI_B" and r["analyte"] == "Na"]

    check(room1_ans == "dissolved_solids", f"room1: aquifer_1 top analyte is dissolved_solids (got {room1_ans})")
    check(room2_ans == "Moanalua_Wells_Pump_3", f"room2: aquifer_1 top-SO4 well is Moanalua_Wells_Pump_3 (got {room2_ans})")
    check(a6_cl_over == ["KEEI_B"], f"room3: KEEI_B is the ONLY aquifer_6 Cl well over 250 (got {a6_cl_over})")
    check(keeib_na == [180.0], f"boss: KEEI_B sodium is 180, above 150 (got {keeib_na})")

    # ---- wired puzzle content matches the data ----
    scen = json.load(open(SCEN, encoding="utf-8"))
    R = {r["key"]: r for r in scen["rooms"]}
    def pz(rk): return [h for h in R[rk]["hotspots"] if h["type"] == "puzzle"][0]
    def mcq_text(rk):
        q = pz(rk)["question"]
        return q["options"][q["correct"]]

    check("question" in pz("room1"), "room1 is an MCQ")
    check(mcq_text("room1") == "dissolved_solids", f"room1 correct option text == dissolved_solids (got {mcq_text('room1')!r})")
    check("question" in pz("room2"), "room2 is an MCQ")
    check(mcq_text("room2") == "Moanalua_Wells_Pump_3", f"room2 correct option text == Moanalua_Wells_Pump_3 (got {mcq_text('room2')!r})")
    # room3 must be the console-check (NOT an MCQ) targeting KEEI_B
    r3 = pz("room3")
    check("check" in r3 and "question" not in r3, "room3 is a console-check (not an MCQ)")
    check("KEEI_B" in r3.get("check", {}).get("expr", ""), f"room3 check expr targets KEEI_B (got {r3.get('check',{}).get('expr','')!r})")
    check(r3.get("check", {}).get("requires") == ["answer"], "room3 check requires `answer`")
    check("filter" in r3.get("starterCode", ""), "room3 keeps its broken repair-the-filter starterCode")
    check("question" in pz("boss"), "boss is an MCQ")
    check("180" in mcq_text("boss") and "intrusion" in mcq_text("boss").lower(),
          f"boss correct option is the Na=180 intrusion-confirmed verdict (got {mcq_text('boss')!r})")

    # no `reveal` leaked into any graded engine
    for rk in ("room1", "room2", "room3", "boss"):
        eng = pz(rk).get("question") or pz(rk).get("check")
        check(not eng.get("feedback", {}).get("reveal"), f"{rk}: no reveal")

    # ---- decoder lockstep: DATA_VIS_HAWAII_KEY = c(3, 5, 1, 2) (MCQ indices + console-check 1) ----
    dec = open(DECODER, encoding="utf-8").read()
    m = re.search(r"DATA_VIS_HAWAII_KEY\s*<-\s*list\((.*?)\n\)", dec, re.S)
    check(bool(m), "DATA_VIS_HAWAII_KEY present in decode_codes.R")
    if m:
        sid = re.search(r"scenario_id\s*=\s*(\d+)", m.group(1))
        cor = re.search(r"correct\s*=\s*c\(([^)]*)\)", m.group(1))
        check(bool(sid) and int(sid.group(1)) == 7, "decoder key scenario_id == 7")
        vec = [int(x) for x in cor.group(1).replace(" ", "").split(",")] if cor else []
        check(vec == [3, 5, 1, 2], f"decoder key correct == c(3, 5, 1, 2) (got {vec})")
        check(scen["id"] == 7, "scenario id == 7")

    print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURE(S): " + "; ".join(fails)))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
