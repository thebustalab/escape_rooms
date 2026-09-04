#!/usr/bin/env python3
"""test_canyon.py — regression guards for hierarchical_clustering/canyon.

The four graded rungs are re-derived from the CSV by `_scratch/verify_canyon_data.py` and the escape's
cut by `_scratch/verify_escape_topology.py`. This file guards the SEAM between those and the SHIPPED
scenario — the places where a correct answer and a correct board can still ship a broken room.
Run: python3 test_canyon.py   (stdlib only.)

Failure modes it guards:
  - a puzzle's `correct` index stops pointing at the option the DATA supports. The option list is prose,
    so a reorder during editing silently re-keys the room while every validator stays green;
  - the decoder drifts from `question.correct` — graded submissions then mis-score in silence;
  - a BENCHMARK's carved number stops matching the elevmap node the player copies it onto. The numbers
    are authored in two places (the clue body and the node `answer`) and only agree by hand;
  - a benchmark's `onPickup` key stops matching the node's `requires` — the node then never unlocks and
    the escape can never reach 7 placed heights, which strands the player with no error message;
  - the escape code stops being what the panel's own rule produces from those heights;
  - the TAUGHT TRAP decays: the carved wall-map must stay tempting BEFORE the answer, so it must exist,
    must be referred to by the boss's "the map is right" distractor, and must NOT name either outlier.
"""
import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)


doc = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
rooms = {r["key"]: r for r in doc["rooms"]}
COLS = ["carbonate", "sulfate", "chloride", "silica", "iron_oxide", "salts"]
springs = list(csv.DictReader(open(os.path.join(HERE, "data", "canyon_water_chem.csv"))))
unknown = list(csv.DictReader(open(os.path.join(HERE, "data", "unknown_spring.csv"))))[0]
vec = lambda r: [float(r[c]) for c in COLS]
by = {r["spring"]: r for r in springs}


def gate(room, kind="puzzle"):
    return next(h for h in rooms[room]["hotspots"] if h.get("type") == kind)


def chosen(room):
    q = gate(room)["question"]
    return q["options"][q["correct"]]


print("\n-- the answer the DATA supports is the option the room keys to --")

# rung 1: nearest neighbour of Dripstone
d = sorted((math.dist(vec(r), vec(by["Dripstone"])), r["spring"]) for r in springs if r["spring"] != "Dripstone")
check(chosen("j_c1") == d[0][1], "j_c1 keys to Dripstone's nearest kin (%s, d=%.2f; runner-up %s d=%.2f)"
      % (d[0][1], d[0][0], d[1][1], d[1][0]))
check(d[1][0] / d[0][0] > 1.10, "j_c1 has a single clean winner (margin %.0f%%, needs >10%%)"
      % (100 * (d[1][0] - d[0][0]) / d[0][0]))

# rung 2: the unknown lands among the North Branch silica springs
near = sorted((math.dist(vec(r), vec(unknown)), r["spring"], r["fork"]) for r in springs)
check(near[0][2] == "North_Branch" and by[near[0][1]]["silica"] > "50",
      "j_c2: Unmarked_Spring's nearest neighbours are North Branch silica springs (%s d=%.2f)" % (near[0][1], near[0][0]))
check("silica" in chosen("j_c2").lower() and "North Branch" in chosen("j_c2"),
      "j_c2 keys to the silica / North Branch family — %r" % chosen("j_c2"))

# rung 3: the k=4 sulfate family, and it must INCLUDE Bitterwell (that is the whole point)
FAMILIES = {"carbonate": ["Dripstone", "Palegate", "Lime_Hollow", "Chalkseep"],
            "sulfate": ["Bitterwell", "Brimstone_Font", "Sulphur_Step", "Cinderpool", "Matchhead_Spring"],
            "silica": ["Glasswater", "Flintrun", "Obsidian_Weep", "Silverglass"],
            "saline": ["Saltglass", "Brineseep", "Saltmouth", "Tidewell", "Pillar_Brine"]}
means = {k: sum(float(by[m]["sulfate"]) for m in v) / len(v) for k, v in FAMILIES.items()}
top = max(means, key=means.get)
check(top == "sulfate", "j_c4: the sulfate family has the highest mean sulfate (%.1f vs next %.1f)"
      % (means["sulfate"], sorted(means.values())[-2]))
check("Bitterwell" in chosen("j_c4"), "j_c4's keyed option NAMES Bitterwell — the cluster-vs-fork distinction")
fork_east = [r for r in springs if r["fork"] == "East_Fork"]
check(any("East Fork" in o and "Bitterwell" not in o for o in gate("j_c4")["question"]["options"]),
      "j_c4 offers the group-by-fork mistake as a distractor (East Fork alone, mean %.1f — nearly identical)"
      % (sum(float(r["sulfate"]) for r in fork_east) / len(fork_east)))

# boss: the two springs whose fork and chemistry disagree
fam_of = {m: k for k, v in FAMILIES.items() for m in v}
FORK_FAM = {"West_Fork": "carbonate", "East_Fork": "sulfate", "North_Branch": "silica", "South_Branch": "saline"}
outliers = sorted(r["spring"] for r in springs if fam_of[r["spring"]] != FORK_FAM[r["fork"]])
check(outliers == ["Bitterwell", "Saltglass"], "boss: the data's outliers are %s" % outliers)
check(all(o in chosen("j_c7") for o in outliers), "j_c7 keys to the option naming BOTH outliers — %r" % chosen("j_c7"))

print("\n-- decoder lockstep --")
expected = [gate(k)["question"]["correct"] for k in ("j_c1", "j_c2", "j_c4", "j_c7")]
rsrc = open(os.path.join(HERE, "..", "..", "..", "decoder", "decode_codes.R"), encoding="utf-8").read()
block = rsrc[rsrc.index("HIERARCHICAL_CLUSTERING_CANYON_KEY"):][:400]
key_vec = [int(x) for x in re.search(r"correct = c\(([^)]*)\)", block).group(1).split(",")]
check(key_vec == expected, "decode_codes.R correct = c(%s) matches scenario.json %s"
      % (", ".join(map(str, key_vec)), expected))
check(int(re.search(r"scenario_id = (\d+)", block).group(1)) == doc["id"],
      "decoder key scenario_id matches the scenario's id (%s)" % doc["id"])
check(len(set(expected)) > 1, "the correct index is not the same slot in every room (%s)" % expected)

print("\n-- the benchmarks the player copies onto the map --")
elev = next(h for h in rooms["works"]["hotspots"] if h.get("type") == "elevmap")
nodes = {n["id"]: n for n in elev["nodes"]}
for rk, room in rooms.items():
    for h in (room.get("hotspots") or []):
        m = re.fullmatch(r"bm_(c\d)", h.get("id") or "")
        if not m:
            continue
        cid = m.group(1)
        carved = re.search(r"(\d{3,4})", h.get("body") or "")
        check(carved and int(carved.group(1)) == nodes[cid]["answer"],
              "%s: benchmark reads %s and node %s expects %s" % (rk, carved and carved.group(1), cid, nodes[cid]["answer"]))
        check((h.get("onPickup") or {}).get("set") == nodes[cid]["requires"],
              "%s: benchmark sets %r, node %s requires %r"
              % (rk, (h.get("onPickup") or {}).get("set"), cid, nodes[cid]["requires"]))

print("\n-- the escape code is what the panel's own rule produces --")
# leaves pair at c1/c2/c4/c5; c3 joins the left pair-groups, c6 the right, c7 the two halves.
MERGE = {"c1": 1400, "c2": 1380, "c4": 1420, "c5": 1390, "c3": 1050, "c6": 1200, "c7": 850}
def cut(water):
    """Group sizes left to right at a waterline: a confluence BELOW the line is severed, above it holds."""
    def grp(node):
        kids = {"c7": ("c3", "c6"), "c3": ("c1", "c2"), "c6": ("c4", "c5")}.get(node)
        if kids is None:
            return [2] if MERGE[node] > water else [1, 1]      # a leaf pair holds or splits
        left, right = (grp(k) for k in kids)
        return (left + right) if MERGE[node] <= water else [sum(left + right)]
    return grp("c7")
check(cut(1300) == [2, 2, 2, 2], "panel's lit row 1300 -> %s" % cut(1300))
check(cut(950) == [4, 4], "panel's lit row 950 -> %s" % cut(950))
lock = gate("works", "lock")
check("".join(map(str, cut(1125))) == lock["answer"],
      "the dark row 1125 -> %s, and the lock answer is %r" % (cut(1125), lock["answer"]))
check(lock.get("length") == len(lock["answer"]), "lock length %s matches its answer" % lock.get("length"))
check(str(cut(1300)[0]) in (rooms["undercroft"]["hotspots"][0].get("body") or "") or
      any("1300" in (h.get("body") or "") for h in rooms["undercroft"]["hotspots"]),
      "the control panel clue states the lit rows the player generalises from")

print("\n-- the hall is a one-visit prologue, so what it teaches must travel --")
edges = {k: [h["to"] for h in (r.get("hotspots") or []) if h.get("type") == "door" and h.get("to")]
         for k, r in rooms.items()}
def reach(start):
    seen, stack = {start}, [start]
    while stack:
        for t in edges.get(stack.pop(), []):
            if t not in seen:
                seen.add(t); stack.append(t)
    return seen
check(reach("undercroft") == set(rooms), "every room is reachable from the drowned hall")
check(not any(k != "undercroft" and "undercroft" in reach(k) for k in rooms),
      "nothing reaches the hall again — the ladder breaks behind the player, by design")
panel = next(h for h in rooms["undercroft"]["hotspots"] if h.get("id") == "control_panel")
check(bool(panel.get("pickup")),
      "the control panel is a PICKUP — the player can never return to re-read it, and the lock renders "
      "no instructions, so its rows have to travel in the field notebook or the escape is unsolvable")
for n in ("1300", "950", "1125"):
    check(n in str(panel.get("pickup")), "the notebook entry carries the %s row" % n)

print("\n-- the taught trap stays a trap --")
wallmap = next((h for h in rooms["j_c7"]["hotspots"] if h.get("id") == "carved_wall_map"), None)
check(wallmap is not None and bool(wallmap.get("body")), "j_c7 still carries the carved wall-map clue, with a body")
check(not any(o in (wallmap.get("body") or "") for o in outliers),
      "the carved wall-map does NOT name either outlier — a trap must tempt BEFORE the answer")
check(any(re.search(r"map is right", o) for o in gate("j_c7")["question"]["options"]),
      "the boss offers 'the carved map is right' — the distractor the wall-map exists to make tempting")

print("\n-- shipped-content invariants --")
for rk in ("j_c1", "j_c2", "j_c4", "j_c7"):
    q = gate(rk)["question"]
    check(len(q["options"]) >= 6, "%s has >=6 options (%d)" % (rk, len(q["options"])))
    check(len(set(q["options"])) == len(q["options"]), "%s has no duplicate option text" % rk)
    check(0 <= q["correct"] < len(q["options"]), "%s correct index in range" % rk)
    check("reveal" not in q.get("feedback", {}), "%s has no reveal" % rk)
    starter = gate(rk).get("starterCode", "")
    check(all(ln.strip() in ("canyon_water_chem", "unknown_spring") for ln in starter.splitlines() if ln.strip()),
          "%s starterCode is bare data-object names only (%r)" % (rk, starter))
    check(not re.search(r"cutree|dist\(|hclust|group_by|filter\(", q["prompt"]),
          "%s prompt leaks no method" % rk)

print("\n%s — %d check(s), %d failure(s)" % ("FAILED" if fails else "ALL PASS", 0, len(fails)))
sys.exit(1 if fails else 0)
