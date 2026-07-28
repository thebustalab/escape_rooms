#!/usr/bin/env python3
"""
test_hospital.py — regression guards for the data_vis2/hospital scenario (stdlib only; python3).

Covers the parts that can silently break WITHOUT a browser: the four analysis MCQ answers staying in
lockstep with the real data + the decoder key, the v3 facet-collage escape keypad staying the code the
combinatorics prove (729, from escape2_facets.py), the escape's clue/lock structure, the scenario graph
shape, and a static presence-check of two 2026-07-18 player bug-fixes. Run: python3 test_hospital.py

Failure modes it guards:
  - the CSV changes and a room's verified answer (Na~Cl proxy / nearest lake / weakest park / max element)
    silently stops matching the wired correct option;
  - a correct-index drifts out of lockstep with decode_codes.R's DATA_VIS2_HOSPITAL_KEY = c(3,1,4,2);
  - the escape keypad code drifts from the facet combinatorics (escape2_facets.py -> 729);
  - the escape loses its lock/collage/postcard wiring or its phase/gate wiring;
  - a starter leaks the solving pipeline, an option set drops below six, or a `reveal` sneaks back in;
  - a refactor drops the analysis-finish idempotency guard or the music position-restore.

History: the v1 `map`-puzzle escape (click Imuruk on a pH×Ca chart) was retired for the v3 facet-collage
keypad; this file's old map-asset/Imuruk guards were replaced 2026-07-21 to match.
"""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import escape2_facets  # the escape's verified combinatorics (keypad code 729)

SITE = HERE
for _ in range(8):
    if os.path.exists(os.path.join(SITE, "phylochemistry", "sample_data", "alaska_lake_data.csv")):
        break
    SITE = os.path.dirname(SITE)
CSV = os.path.join(SITE, "phylochemistry", "sample_data", "alaska_lake_data.csv")
PLAYER = os.path.join(SITE, "escape_rooms", "shared", "pano-player.js")

fails = []
def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)

def pearson(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs)); sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (sx * sy)

def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    num = lambda x: float(x) if x not in ("", "NA") else None
    lakes = sorted(set(r["lake"] for r in rows))
    elements = sorted(set(r["element"] for r in rows))
    park = {r["lake"]: r["park"] for r in rows}
    val = {l: {} for l in lakes}
    for r in rows:
        val[r["lake"]][r["element"]] = num(r["mg_per_L"])

    scen = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
    R = {r["key"]: r for r in scen["rooms"]}
    def puzzle(rk):
        return next(h for h in R[rk]["hotspots"] if h.get("type") == "puzzle")

    print("== analysis answers vs data (each correct option is the verified answer) ==")
    # room1 — chloride is a strong proxy for sodium (Na~Cl r ~ 0.999)
    na = [val[l]["Na"] for l in lakes]; cl = [val[l]["Cl"] for l in lakes]
    r_nacl = pearson(na, cl)
    q1 = puzzle("room1")["question"]
    check(r_nacl > 0.99, "Na~Cl correlation is very strong (%.4f) — room1's 'strong proxy' answer holds" % r_nacl)
    check(q1["correct"] == 3 and "0.999" in q1["options"][3], "room1 correct = idx 3 (the strong-positive proxy option)")

    # room2 — nearest chemical match to North_Killeak == White_Fish_Lake
    nk = "North_Killeak_Lake"
    dist = sorted(((math.sqrt(sum((val[l][e] - val[nk][e]) ** 2 for e in elements
                                   if val[l][e] is not None and val[nk][e] is not None)), l)
                   for l in lakes if l != nk))
    q2 = puzzle("room2")["question"]
    check(dist[0][1] == "White_Fish_Lake", "nearest lake to North_Killeak is White_Fish_Lake (got %s)" % dist[0][1])
    check(q2["correct"] == 1 and q2["options"][1] == "White_Fish_Lake", "room2 correct = idx 1 = White_Fish_Lake")

    # room3 — NOAT is the weakest per-park Na~Cl
    def park_r(pk):
        ll = [l for l in lakes if park[l] == pk]
        return pearson([val[l]["Na"] for l in ll], [val[l]["Cl"] for l in ll])
    weakest = min(["BELA", "GAAR", "NOAT"], key=park_r)
    q3 = puzzle("room3")["question"]
    check(weakest == "NOAT", "NOAT has the weakest per-park Na~Cl relationship (got %s)" % weakest)
    check(q3["correct"] == 4 and "NOAT" in q3["options"][4], "room3 correct = idx 4 (the NOAT-weakest option)")

    # boss — chlorine is the max element in North_Killeak among the five candidates -> Chlorocidin
    cand = {"S": "Sulfomycin", "N": "Nitroflavin", "Cl": "Chlorocidin", "Br": "Bromostatin", "Ca": "Calcihexin"}
    top = max(cand, key=lambda e: val[nk][e])
    q4 = puzzle("boss")["question"]
    check(top == "Cl", "chlorine is the most abundant of the five candidate elements in North_Killeak (got %s)" % top)
    check(q4["correct"] == 2 and q4["options"][2] == "Chlorocidin", "boss correct = idx 2 = Chlorocidin")

    print("== MCQ hygiene + decoder lockstep ==")
    correct = [puzzle(rk)["question"]["correct"] for rk in ("room1", "room2", "room3", "boss")]
    check(correct == [3, 1, 4, 2], "correct indices == DATA_VIS2_HOSPITAL_KEY c(3,1,4,2): %s" % correct)
    for rk in ("room1", "room2", "room3", "boss"):
        q = puzzle(rk)["question"]
        check(len(q["options"]) >= 6, "%s has >= 6 options (%d)" % (rk, len(q["options"])))
        check("reveal" not in q.get("feedback", {}), "%s has no feedback.reveal" % rk)
    for rk in ("room1", "room2", "room3"):   # practice starters give nothing away (boss = the assessed plot, exempt)
        sc = puzzle(rk).get("starterCode", "")
        check("ggplot(" not in sc and "filter(" not in sc, "%s starterCode has no solving pipeline" % rk)

    print("== escape v3: facet-collage keypad ==")
    # the combinatorics module still proves the intended pairing -> 729, and all six codes are distinct
    codes = escape2_facets.all_codes()
    check(len(set(codes.values())) == len(codes), "the six facet pairings give six distinct codes")
    check(codes[escape2_facets.INTENDED] == "729", "intended pairing (season × remoteness) -> 729")
    esc = R.get("escape1", {})
    hs = esc.get("hotspots", [])
    lock = next((h for h in hs if h.get("type") == "lock"), None)
    check(lock is not None and lock.get("answer") == "729", "escape keypad lock answer == 729")
    check(lock and str(lock.get("length")) == "3", "keypad length is 3")
    collage = [h for h in hs if h.get("type") == "clue" and h.get("image") == "postcards/collage_door.png"]
    check(len(collage) == 1 and not collage[0].get("pickup"), "one non-pickup started-collage clue (the format key)")
    notes = [h for h in hs if h.get("type") == "clue" and h.get("id", "").startswith("editor_s_note")]
    check(len(notes) == 2 and all(n.get("pickup") and not n.get("image") for n in notes),
          "two pickup editorial-note clues (text, no image)")
    # nine postcards total, all pickup + image, across the whole scenario
    cards = [h for r in scen["rooms"] for h in r.get("hotspots", [])
             if h.get("type") == "clue" and str(h.get("image", "")).startswith("postcards/postcard_")]
    check(len(cards) == 9 and all(c.get("pickup") and c.get("image") for c in cards),
          "nine pickup postcard clues (image + notebook caption)")
    check(not any(isinstance(h.get("map"), dict) for r in scen["rooms"] for h in r.get("hotspots", [])),
          "no `map`-puzzle hotspot remains (v1 map escape retired)")

    print("== scenario graph ==")
    check(scen.get("id") == 8, "scenario id is 8")
    check(scen.get("boardCols") == 3, "boardCols is 3 (the 3x3 collage board)")
    check({"dplyr", "ggplot2", "readr", "tidyr"}.issubset(scen.get("packages", [])), "packages include tidyr + ggplot2 + dplyr + readr")
    check(esc.get("phase") == "escape", "escape1 is phase:escape (ungraded, out of codec)")
    check(esc.get("unlockedWhen") == {"solved": "boss"}, "escape1 unlocks on solving the boss")
    check(bool(scen.get("escapeDone")), "scenario has an escapeDone finish screen")
    check(R.get("boss", {}).get("isBoss") is True, "boss is flagged isBoss")
    # forward doors chain room1->room2->room3->boss->escape1; the way out is gated on the keypad
    fwd = {rk: next((h.get("to") for h in R[rk]["hotspots"]
                     if h.get("type") == "door" and (h.get("direction") or "forward") == "forward"), None)
           for rk in ("room1", "room2", "room3", "boss")}
    check(fwd == {"room1": "room2", "room2": "room3", "room3": "boss", "boss": "escape1"},
          "forward doors chain room1->room2->room3->boss->escape1: %s" % fwd)
    wayout = next((h for h in hs if h.get("type") == "door" and (h.get("direction") or "forward") == "forward"), None)
    check(wayout and wayout.get("requires") == "the_keypad_on_the_door" and not wayout.get("to"),
          "the way-out door is gated on the keypad and has no `to` (fires the escape finish)")

    print("== player bug-fix guards (static; behaviour is manual-verify, no JS runner) ==")
    js = open(PLAYER, encoding="utf-8").read()
    check("if (analysisFinished) return;" in js and "analysisComplete()" in js,
          "analysis-finish is idempotent + completion-triggered (2026-07-18 fix)")
    check("musicBaseVol" in js and "music.currentTime = musicPos" in js,
          "music position-restore across viewer rebuilds (2026-07-18 fix)")
    check('addEventListener("pause"' in js, "music resume-on-unintended-pause guard present")

    print("\n%d failure(s)" % len(fails))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
