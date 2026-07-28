#!/usr/bin/env python3
"""
test_henges.py — regression guards for the dimensionality_reduction/henges scenario ("The Drowned Henges").

Pins the parts that can silently break WITHOUT a browser: the four PCA answers staying in lockstep with
the real data + the wired puzzles, the two-gate door wiring (forward arch requires its keypad lock), the
stone-cipher escape code, and the decoder key. Run: python3 test_henges.py

Needs numpy (PCA/eigendecomposition); numpy is available on this box. The rest is stdlib.

Failure modes it guards:
  - the CSV changes and a room's verified answer (PC1 outlier / scree % / PC1 driver / PC2 mushroom marker)
    silently stops matching the wired puzzle;
  - the PC1-fixation trap collapses (mushrooms stop being mid-pack on PC1 / extreme on PC2);
  - a forward arch loses its `requires` (the keypad lock) and reverts to opening on the puzzle — bypassing
    the two-gate portal;
  - the escape stone-code drifts from the four patterns in scree order;
  - the decoder key DATA_VIS_HENGES_KEY drifts out of lockstep with the built graded rooms;
  - a `reveal` sneaks back in, or a non-repair starter leaks the pipeline.
"""
import csv, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "data", "druid_ingredients.csv")
SCEN = os.path.join(HERE, "scenario.json")
DECODER = os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R")
NUMCOLS = ["potency","bitterness","aroma_intensity","volatility","luminance","pigment","resin_content","moisture","ash_weight"]

fails = []
def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond: fails.append(msg)

def pca(rows):
    X = np.array([[float(r[c]) for c in NUMCOLS] for r in rows])
    n = len(X)
    Z = (X - X.mean(0)) / X.std(0, ddof=1)          # prcomp(scale.=TRUE)
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    eig = S**2 / (n - 1)
    ve = 100 * eig / eig.sum()
    scores = U * S                                   # = Z @ Vt.T
    load = Vt.T                                       # rows=properties, cols=PCs
    return scores, load, ve

def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    names = [r["ingredient"] for r in rows]
    kinds = [r["kind"] for r in rows]
    scores, load, ve = pca(rows)

    # ---- answers derived from the data ----
    outlier = names[int(np.argmax(np.abs(scores[:, 0])))]
    pc1_pct = round(ve[0], 1)
    pc1_driver = NUMCOLS[int(np.argmax(np.abs(load[:, 0])))]
    pc2_driver = NUMCOLS[int(np.argmax(np.abs(load[:, 1])))]
    mush = np.array([k == "mushroom" for k in kinds])
    mush_pc1 = scores[mush, 0].mean()
    mush_pc2 = scores[mush, 1].mean()

    check(outlier == "Deathwatch Scarab", f"PC1 outlier is Deathwatch Scarab (got {outlier})")
    check(abs(pc1_pct - 25.0) <= 0.6, f"PC1 variance ~25% (got {pc1_pct})")
    check(pc1_driver == "potency", f"PC1 driver is potency (got {pc1_driver})")
    check(pc2_driver == "luminance", f"PC2 driver is luminance (got {pc2_driver})")
    check(abs(mush_pc1) < 0.5, f"TRAP: mushrooms mid-pack on PC1 (mean {mush_pc1:.2f})")
    check(mush_pc2 > 1.0, f"TRAP: mushrooms extreme on PC2 (mean {mush_pc2:.2f})")

    # ---- wired puzzle content matches the data ----
    scen = json.load(open(SCEN, encoding="utf-8"))
    R = {r["key"]: r for r in scen["rooms"]}
    def pz(rk): return [h for h in R[rk]["hotspots"] if h["type"] == "puzzle"][0]
    def lock(rk): return [h for h in R[rk]["hotspots"] if h["type"] == "lock"][0]
    def door(rk, hid): return [h for h in R[rk]["hotspots"] if h["id"] == hid][0]

    check(pz("mountain").get("pick", {}).get("answer") == "Deathwatch Scarab", "mountain pick answer == Deathwatch Scarab")
    check("25" in pz("plains")["check"]["expr"], "plains check targets 25%")
    check('"potency"' in pz("saltflat")["check"]["expr"], "saltflat check targets potency")
    check('"luminance"' in pz("boss")["check"]["expr"], "boss check targets luminance")
    # boss is repair: broken starter reads PC1, must be fixable to PC2
    bstart = pz("boss")["starterCode"]
    check('"PC1"' in bstart, "boss starterCode (broken) reads PC1")

    # ---- no reveal leaked; non-repair starters are the bare data object ----
    for rk in ("mountain", "plains", "saltflat", "boss"):
        eng = pz(rk).get("pick") or pz(rk).get("check")
        check(not eng.get("feedback", {}).get("reveal"), f"{rk}: no reveal")
    for rk in ("plains", "saltflat"):
        check(pz(rk)["starterCode"] == "druid_ingredients", f"{rk}: starter is the bare data object")

    # ---- two-gate doors: forward arch requires its keypad lock ----
    for rk, lk in (("beach","the_mark_stone"),("mountain","the_mark_stone"),
                   ("plains","the_mark_stone"),("saltflat","the_mark_stone")):
        check(door(rk, "the_star_filled_arch").get("requires") == lk, f"{rk} forward arch requires {lk}")
    wh = door("boss", "the_way_home")
    check(wh.get("requires") == "the_heart_stone" and wh.get("endsEscape") is True,
          "boss way-home requires the heart-stone + endsEscape")

    # ---- stone-cipher: per-room patterns + escape code (scree ascending: saltflat,mountain,plains,beach) ----
    pat = {"beach":"|_|","mountain":"||_","plains":"__|","saltflat":"_|_"}
    for rk, p in pat.items():
        check(lock(rk)["answer"] == p and lock(rk).get("mode") == "stones", f"{rk} lock = stones '{p}'")
    escape_code = pat["saltflat"] + pat["mountain"] + pat["plains"] + pat["beach"]
    check(lock("boss")["answer"] == escape_code, f"escape code == {escape_code} (scree ascending)")
    check(lock("boss").get("mode") == "stones" and lock("boss").get("length") == 12, "heart-stone: stones, len 12")

    # ---- decoder lockstep: DATA_VIS_HENGES_KEY = c(1,1,1,1), 4 graded rooms ----
    graded = [r for r in scen["rooms"] if r.get("built") and r.get("phase") != "escape"
              and any(h["type"] == "puzzle" for h in r.get("hotspots", []))]
    check(len(graded) == 4, f"4 built graded rooms (got {len(graded)})")
    dec = open(DECODER, encoding="utf-8").read()
    m = re.search(r"DATA_VIS_HENGES_KEY\s*<-\s*list\((.*?)\)\s*\n", dec, re.S)
    check(bool(m), "DATA_VIS_HENGES_KEY present in decode_codes.R")
    if m:
        sid = re.search(r"scenario_id\s*=\s*(\d+)", m.group(1))
        cor = re.search(r"correct\s*=\s*c\(([^)]*)\)", m.group(1))
        check(sid and int(sid.group(1)) == 11, "decoder key scenario_id == 11")
        vec = [int(x) for x in cor.group(1).replace(" ", "").split(",")] if cor else []
        check(vec == [1, 1, 1, 1], f"decoder key correct == c(1,1,1,1) (got {vec})")
        check(scen["id"] == 11, "scenario id == 11")

    print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURE(S): " + "; ".join(fails)))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
