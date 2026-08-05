#!/usr/bin/env python3
"""
test_hospital.py — regression guards for the data_vis2/hospital scenario (stdlib only; python3).

Covers the parts that can silently break WITHOUT a browser: the four analysis MCQ answers staying in
lockstep with the real data + the decoder key, the v3 facet-collage escape keypad staying the code the
combinatorics prove (729, from escape2_facets.py), the escape's clue/lock structure, the scenario graph
shape, and a static presence-check of two 2026-07-18 player bug-fixes. Run: python3 test_hospital.py

The scenario was re-themed from Alaska lake chemistry to a hospital METABOLOMICS panel (2026-07-30):
Elias's case, dataset metabolomics_hospital.csv (LONG: patient × metabolite × concentration) + Elias's
own panel in metabolomics_hospital_unknown.csv. The engine, escape and codec are untouched; only the
analysis-room DATA and wording changed. This file re-derives each answer from the two CSVs.

Failure modes it guards:
  - a CSV changes and a room's verified answer (Choline~2-AIB proxy / Elias's nearest patient / the
    Simpson pair / Elias's most-elevated marker) silently stops matching the wired correct option;
  - a correct-index drifts out of lockstep with decode_codes.R's DATA_VIS2_HOSPITAL_KEY = c(3,1,4,0);
  - the escape keypad code drifts from the facet combinatorics (escape2_facets.py -> 729);
  - the escape loses its lock/collage/postcard wiring or its phase/gate wiring;
  - an option set drops below six, a `reveal` sneaks back in, or a starter leaks the plotting pipeline;
  - a refactor drops the analysis-finish idempotency guard or the music position-restore.
"""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import escape2_facets  # the escape's verified combinatorics (keypad code 729)

SITE = HERE
for _ in range(8):
    if os.path.exists(os.path.join(SITE, "phylochemistry", "sample_data", "metabolomics_hospital.csv")):
        break
    SITE = os.path.dirname(SITE)
CSV = os.path.join(SITE, "phylochemistry", "sample_data", "metabolomics_hospital.csv")
UNK = os.path.join(SITE, "phylochemistry", "sample_data", "metabolomics_hospital_unknown.csv")
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
    # --- load the cohort (LONG -> per-patient dict) + Elias's own panel ---
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    patients, status, val = [], {}, {}
    for r in rows:
        p = r["patient_number"]
        if p not in val:
            val[p] = {}; status[p] = r["patient_status"]; patients.append(p)
        val[p][r["metabolite"]] = float(r["concentration"])
    metabolites = sorted({r["metabolite"] for r in rows})
    elias = {r["metabolite"]: float(r["concentration"]) for r in csv.DictReader(open(UNK, encoding="utf-8"))}

    scen = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
    R = {r["key"]: r for r in scen["rooms"]}
    def puzzle(rk):
        return next(h for h in R[rk]["hotspots"] if h.get("type") == "puzzle")

    def zstats(names, ids):
        st = {}
        for m in names:
            xs = [val[p][m] for p in ids]; mu = sum(xs) / len(xs)
            sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / len(xs))
            st[m] = (mu, sd)
        return st

    print("== analysis answers vs data (each correct option is the verified answer) ==")
    # room1 — choline is a strong proxy for 2-aminoisobutyric acid (r > 0.99, holds within group too)
    ch = [val[p]["Choline"] for p in patients]; aib = [val[p]["2-Aminoisobutyric acid"] for p in patients]
    r1 = pearson(ch, aib)
    q1 = puzzle("room1")["question"]
    check(r1 > 0.97, "Choline~2-AIB correlation is very strong (%.4f) — room1's 'strong proxy' answer holds" % r1)
    check(q1["correct"] == 3 and "rises clearly with choline" in q1["options"][3],
          "room1 correct = idx 3 (the strong-positive proxy option)")

    # room2 — Elias's nearest patient over the SCALED panel EXCLUDING Creatinine (the pending assay) == patient 54
    heat = [m for m in metabolites if m != "Creatinine"]
    st = zstats(heat, patients)
    z = lambda v, m: (v - st[m][0]) / st[m][1] if st[m][1] else 0.0
    ez = {m: z(elias[m], m) for m in heat}
    dist = sorted((math.sqrt(sum((z(val[p][m], m) - ez[m]) ** 2 for m in heat)), p) for p in patients)
    q2 = puzzle("room2")["question"]
    check(dist[0][1] == "54", "Elias's nearest patient (scaled, excl. Creatinine) is 54 (got %s)" % dist[0][1])
    check(dist[1][0] - dist[0][0] > 0.5, "patient 54 is a clear single match (margin %.2f)" % (dist[1][0] - dist[0][0]))
    check(q2["correct"] == 1 and q2["options"][1] == "Patient 54", "room2 correct = idx 1 = Patient 54")

    # room3 — Simpson: Indoxyl~p-Cresyl strong POOLED, near-zero WITHIN each patient group
    ix = [val[p]["Indoxyl_Sulfate"] for p in patients]; pc = [val[p]["p_Cresyl_Sulfate"] for p in patients]
    pooled = pearson(ix, pc)
    def grp_r(g):
        pp = [p for p in patients if status[p] == g]
        return pearson([val[p]["Indoxyl_Sulfate"] for p in pp], [val[p]["p_Cresyl_Sulfate"] for p in pp])
    rh, rk = grp_r("healthy"), grp_r("kidney_disease")
    q3 = puzzle("room3")["question"]
    check(pooled > 0.9, "Indoxyl~p-Cresyl pooled correlation is strong (%.2f)" % pooled)
    check(abs(rh) < 0.5 and abs(rk) < 0.5,
          "within-group correlation collapses — Simpson's paradox (healthy %.2f, kidney %.2f)" % (rh, rk))
    check(q3["correct"] == 4 and "all but vanishes" in q3["options"][4], "room3 correct = idx 4 (the Simpson conclusion)")

    # boss — Elias's most abnormal (z-score) marker among the five candidates is Creatinine -> Nephrocidin
    cand = {"Creatinine": "Nephrocidin", "Methylmalonate": "Cobalatide",
            "Hydroxyphenylpyruvic acid": "Tyrostat", "1-Methyladenosine": "Adenoquel", "myoinositol": "Inositex"}
    bst = zstats(list(cand), patients)
    ez_boss = {m: (elias[m] - bst[m][0]) / bst[m][1] for m in cand}
    topm = max(cand, key=lambda m: ez_boss[m])
    q4 = puzzle("boss")["question"]
    check(topm == "Creatinine", "Elias's most elevated candidate marker is Creatinine (got %s, z=%.1f)" % (topm, ez_boss[topm]))
    check(elias["Creatinine"] > max(val[p]["Creatinine"] for p in patients),
          "Elias's Creatinine exceeds every patient in the cohort (unambiguous 'runs highest')")
    check(q4["correct"] == 0 and q4["options"][0] == "Nephrocidin", "boss correct = idx 0 = Nephrocidin")

    print("== MCQ hygiene + decoder lockstep ==")
    correct = [puzzle(rk)["question"]["correct"] for rk in ("room1", "room2", "room3", "boss")]
    check(correct == [3, 1, 4, 0], "correct indices == DATA_VIS2_HOSPITAL_KEY c(3,1,4,0): %s" % correct)
    for rk in ("room1", "room2", "room3", "boss"):
        q = puzzle(rk)["question"]
        check(len(q["options"]) >= 6, "%s has >= 6 options (%d)" % (rk, len(q["options"])))
        check("reveal" not in q.get("feedback", {}), "%s has no feedback.reveal" % rk)
    for rk in ("room1", "room2", "room3"):   # practice starters may shape data but must not draw the plot (boss exempt)
        sc = puzzle(rk).get("starterCode", "")
        check("ggplot(" not in sc and "geom_" not in sc, "%s starterCode has no plotting pipeline" % rk)
    # Regression (2026-07-30 playtest): Elias's patient_number is the string "Elias" while the cohort's are
    # bare numbers, so readr types the two CSVs' patient_number differently (character vs double) and
    # bind_rows() aborts with "Can't combine ... <double> and ... <character>". Any starter that binds the
    # unknown to the cohort must first coerce patient_number to a common type, or R fails before plotting.
    for rk in ("room1", "room2", "room3", "boss"):
        sc = puzzle(rk).get("starterCode", "")
        if "bind_rows" in sc and "metabolomics_hospital_unknown" in sc:
            check("as.character(patient_number)" in sc,
                  "%s binds the unknown to the cohort and coerces patient_number to character" % rk)

    print("== re-theme hygiene: no stale Alaska/v1 text in player-facing fields ==")
    # Regression (2026-07-30 audit): re-themed off alaska_lake_data, residual Alaska/v1 terms leaked into
    # player-facing narrative (escapeDone said "the pilot's stable, the infection's named"; the escape
    # debrief/technique still described the retired geom_text map puzzle; the subtitle said "filter,
    # count"). Guard the narrative surfaces the player actually reads (scene/design/plannedHotspots are
    # authoring-only and intentionally excluded — the decorative lake-print / parks-map residues live there).
    STALE = ["pilot", "north killeak", "chlorocidin", "white_fish", "white fish", "geom_text",
             "unlabelled plot", "unlabeled plot", "highest sodium", "most lakes", "filter, count",
             "flight-data recorder", "flight recorder"]
    surfaces = [("subtitle", scen.get("subtitle", "")), ("story", scen.get("story", "")),
                ("done.body", scen.get("done", {}).get("body", "")),
                ("escapeDone.body", scen.get("escapeDone", {}).get("body", "")),
                ("escape.enterLabel", scen.get("escape", {}).get("enterLabel", ""))]
    for rk, r in R.items():
        surfaces += [(rk + ".debrief", r.get("debrief", "")), (rk + ".technique", r.get("technique", "")),
                     (rk + ".entry.text", (r.get("entry") or {}).get("text", ""))]
        for h in r.get("hotspots", []):
            q = h.get("question")
            if q:
                surfaces.append((rk + "/" + h.get("id", "") + ".prompt", q.get("prompt", "")))
                fb = q.get("feedback", {})
                surfaces.append((rk + ".feedback.correct", fb.get("correct", "")))
                surfaces += [(rk + ".feedback.wrong[%d]" % i, w) for i, w in enumerate(fb.get("wrong", []))]
            if h.get("type") == "clue" and h.get("body"):
                surfaces.append((rk + "/" + h.get("id", "") + ".body", h["body"]))
    for name, s in surfaces:
        hit = next((t for t in STALE if t in s.lower()), None)
        check(hit is None, "%s: no stale Alaska/v1 term%s" % (name, "" if hit is None else " (found '%s')" % hit))

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
    check(len(notes) == 1 and all(n.get("pickup") and (n.get("body") or "").strip() and not n.get("image") for n in notes),
          "one pickup editorial-note clue (non-empty text body, no image)")
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
    # scenario points at the metabolomics datasets, not the retired lake data
    dsn = [d.get("name") for d in scen.get("datasets", [])]
    check(dsn == ["metabolomics_hospital", "metabolomics_hospital_unknown"],
          "datasets are the metabolomics cohort + Elias's unknown panel: %s" % dsn)
    # forward doors chain room1->room2->room3->boss->escape1; the way out is gated on the keypad
    fwd = {rk: next((h.get("to") for h in R[rk]["hotspots"]
                     if h.get("type") == "door" and (h.get("direction") or "forward") == "forward"), None)
           for rk in ("room1", "room2", "room3", "boss")}
    check(fwd == {"room1": "room2", "room2": "room3", "room3": "boss", "boss": "escape1"},
          "forward doors chain room1->room2->room3->boss->escape1: %s" % fwd)
    # back doors step back exactly one room (linear): each returns to its immediate predecessor
    back = {rk: next((h.get("to") for h in R[rk]["hotspots"]
                      if h.get("type") == "door" and h.get("direction") == "back"), None)
            for rk in ("room2", "room3", "boss", "escape1")}
    check(back == {"room2": "room1", "room3": "room2", "boss": "room3", "escape1": "boss"},
          "back doors step back one room escape1->boss->room3->room2->room1: %s" % back)
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
