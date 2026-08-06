#!/usr/bin/env python3
"""
test_trees.py — regression guards for the wrangling/trees scenario ("The Collector's Vault").

Pins the parts that can silently break WITHOUT a browser: the four group_by/summarise answers staying in
lockstep with the real data + the wired console-check puzzles, the Simpson's-paradox FLIP (the whole
teaching point) surviving a data change, the monorail switch-door navigation graph, the vault grid escape
mapping, and the decoder key. Run: python3 test_trees.py   (stdlib only.)

Failure modes it guards:
  - forest_census.csv changes and a station's verified winner (widest species / brightest vigour class /
    most-vigorous grove) silently stops matching the wired puzzle;
  - the FLIP collapses — the count-weighted shortcut (station3) and the species-balanced regroup (boss)
    stop landing on DIFFERENT groves, so the Simpson's-paradox lesson quietly dies;
  - a monorail car's switch-door loses a variant or mis-targets, breaking backtracking / the ride graph;
  - the vault escape grid's shape->trait answer mapping drifts;
  - a `reveal` sneaks back in, a starter leaks more than the bare data object, or a per-room entry card
    creeps back (Lucas dropped them 2026-08-05);
  - the decoder key WRANGLING_TREES_KEY drifts out of lockstep with the four graded rooms.
"""
import csv, json, os, re, sys
from collections import defaultdict
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "data", "forest_census.csv")
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

    # ---- answers derived straight from the data ----
    s1 = winner(group_mean(rows, "species", "trunk_girth_cm"))            # widest species
    s2 = winner(group_mean(rows, "vigor", "bark_glow"))                   # brightest vigour class
    s3 = winner(group_mean(rows, "canopy_zone", "vitality_index"))        # SHORTCUT: grand mean per zone
    # BOSS regroup: mean over (zone, species) means -> species-balanced zone
    zs = defaultdict(list)
    for r in rows:
        zs[(r["canopy_zone"], r["species"])].append(float(r["vitality_index"]))
    zsp = defaultdict(list)
    for (z, sp), v in zs.items():
        zsp[z].append(mean(v))
    boss = winner({z: mean(ms) for z, ms in zsp.items()})

    check(s1 == "Bloomspire", f"station1 widest species == Bloomspire (got {s1})")
    check(s2 == "Radiant", f"station2 brightest vigour class == Radiant (got {s2})")
    check(s3 == "Cragside", f"station3 shortcut (grand-mean) grove == Cragside (got {s3})")
    check(boss == "Sunspire Heights", f"boss regroup grove == Sunspire Heights (got {boss})")
    # THE FLIP — the whole teaching point: shortcut and regroup MUST disagree
    check(s3 != boss, f"Simpson's flip fires: shortcut ({s3}) != regroup ({boss})")

    # ---- wired console-check puzzles target those answers (expr holds the lowercased name) ----
    scen = json.load(open(SCEN, encoding="utf-8"))
    R = {r["key"]: r for r in scen["rooms"]}
    def pz(rk): return [h for h in R[rk]["hotspots"] if h["type"] == "puzzle"][0]
    wired = {"station1": s1, "station2": s2, "station3": s3, "boss": boss}
    for rk, ans in wired.items():
        expr = pz(rk).get("check", {}).get("expr", "")
        check(f'"{ans.lower()}"' in expr, f"{rk} check.expr targets {ans!r}")
        check(pz(rk)["starterCode"] == "forest_census", f"{rk}: starter is the bare data object")
        check(not pz(rk).get("check", {}).get("feedback", {}).get("reveal"), f"{rk}: no reveal")

    # ---- entry cards dropped everywhere (only the opening scenario `story` survives) ----
    for r in scen["rooms"]:
        check(not r.get("entry"), f"{r['key']}: no per-room entry card")
    check(bool(scen.get("story")), "opening scenario story present (re-readable premise)")

    # ---- monorail switch-doors: each car's single door routes back OR forward by its drive-lever state ----
    cars = {"car_sq": ("car_sq_dir", "station2", "station1"),
            "car_ci": ("car_ci_dir", "station3", "station2"),
            "car_tr": ("car_tr_dir", "boss",     "station3")}
    def variant_for(door, statekey, val):   # the variant whose `when` gates on this lever value
        return next((v for v in door.get("variants", [])
                     if v.get("when", {}).get("eq") == [statekey, val]), {})
    for carkey, (statekey, fwd, back) in cars.items():
        hs = R[carkey]["hotspots"]
        dial = [h for h in hs if h["type"] == "dial"]
        door = [h for h in hs if h["type"] == "door"]
        check(len(dial) == 1 and dial[0].get("key") == statekey, f"{carkey}: one drive-lever dial on {statekey}")
        check(len(door) == 1, f"{carkey}: a single (switch) door")
        fv, bv = variant_for(door[0], statekey, "forward"), variant_for(door[0], statekey, "back")
        check(fv.get("to") == fwd, f"{carkey}: lever=forward variant -> {fwd}")
        check(bv.get("to") == back, f"{carkey}: lever=back variant -> {back}")
        check(bv.get("direction") == "back", f"{carkey}: back variant is a back door")
        check(door[0].get("to") == fwd, f"{carkey}: base `to` (door_graph fallback) == {fwd}")
        # variant STATE names must match the sceneSpec opensOnto so the door-open ART merges onto the nav wiring
        spec_door = next(e for e in R[carkey]["authoring"]["sceneSpec"]["elements"] if e.get("door"))
        oo_states = {ov["state"] for ov in spec_door["door"].get("opensOnto", [])}
        var_states = {v["state"] for v in door[0].get("variants", [])}
        check(var_states == oo_states, f"{carkey}: variant states {var_states} == opensOnto states {oo_states}")
    # each state key defaults to onward
    for statekey in ("car_sq_dir", "car_ci_dir", "car_tr_dir"):
        check(scen.get("state", {}).get(statekey) == "forward", f"state default {statekey} == forward")

    # ---- vault escape: a phase:escape 3x3 grid mapping each shape-line to its hoard's sorting trait ----
    check(R["vault"].get("phase") == "escape", "vault is the escape phase")
    grid = [h for h in R["vault"]["hotspots"] if h["type"] == "grid"][0]
    check(grid.get("endsEscape") is True, "vault grid ends the escape")
    check(grid.get("answer") == {"square": "colour", "circle": "size", "triangle": "shape"},
          "grid answer maps square->colour, circle->size, triangle->shape")
    check({i["key"] for i in grid["items"]} == {"square", "circle", "triangle"}, "grid items are the three shape-lines")
    check({b["key"] for b in grid["buckets"]} == {"colour", "size", "shape"}, "grid buckets are the three traits")

    # ---- decoder lockstep: WRANGLING_TREES_KEY = c(1,1,1,1), 4 graded rooms, id 15 ----
    graded = [r for r in scen["rooms"] if r.get("built") and r.get("phase") != "escape"
              and any(h["type"] == "puzzle" for h in r.get("hotspots", []))]
    check(len(graded) == 4, f"4 built graded rooms (got {len(graded)})")
    check(scen["id"] == 15, "scenario id == 15")
    dec = open(DECODER, encoding="utf-8").read()
    m = re.search(r"WRANGLING_TREES_KEY\s*<-\s*list\((.*?)\)\s*\n", dec, re.S)
    check(bool(m), "WRANGLING_TREES_KEY present in decode_codes.R")
    if m:
        sid = re.search(r"scenario_id\s*=\s*(\d+)", m.group(1))
        cor = re.search(r"correct\s*=\s*c\(([^)]*)\)", m.group(1))
        check(sid and int(sid.group(1)) == 15, "decoder key scenario_id == 15")
        vec = [int(x) for x in cor.group(1).replace(" ", "").split(",")] if cor else []
        check(vec == [1, 1, 1, 1], f"decoder key correct == c(1,1,1,1) (got {vec})")

    print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILURE(S): " + "; ".join(fails)))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
