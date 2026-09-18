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
elev = next(h for h in rooms["undercroft"]["hotspots"] if h.get("id") == "lit_canyon_map")
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
# Heights come from the escape map ITSELF (one source of truth), not a copy kept here.
_map = next(h for h in rooms["undercroft"]["hotspots"] if h.get("id") == "lit_canyon_map")
MERGE = {n["id"]: n["answer"] for n in _map["nodes"]}
def cut(water):
    """Group sizes left to right at a waterline: a confluence BELOW the line is severed, above it holds."""
    def grp(node):
        kids = {"c7": ("c3", "c6"), "c3": ("c1", "c2"), "c6": ("c4", "c5")}.get(node)
        if kids is None:
            return [2] if MERGE[node] > water else [1, 1]      # a leaf pair holds or splits
        left, right = (grp(k) for k in kids)
        return (left + right) if MERGE[node] <= water else [sum(left + right)]
    return grp("c7")
# The panel's three rows, read from its own text (Lucas, 2026-09-18: rows sit ON the map's dotted lines,
# and heights on the drag step — 1125/950/1300 and junctions at 10s did neither).
panel_txt = next(h for h in rooms["undercroft"]["hotspots"] if h.get("id") == "control_panel")["body"]
ROWS = [int(x) for x in re.findall(r"(\d{3,4}) =", panel_txt)]
check(len(ROWS) == 3, "the panel states three rows (%s)" % ROWS)
HIGH, MID, LOW = ROWS
check(cut(HIGH) == [2, 2, 2, 2], "panel's lit top row %s -> %s" % (HIGH, cut(HIGH)))
check(cut(LOW) == [4, 4], "panel's lit bottom row %s -> %s" % (LOW, cut(LOW)))
ax = _map["axis"]
LINES = [ax["min"] + i * (ax["max"] - ax["min"]) / 4 for i in range(5)]   # widgets.js: five even gridlines
for r in ROWS:
    check(r in LINES, "panel row %s lies on one of the map's dotted lines %s" % (r, LINES))
    check((r - ax["min"]) % ax["step"] == 0, "panel row %s is reachable by the waterline's %s step" % (r, ax["step"]))
for m in (_map, next(h for h in rooms["undercroft"]["hotspots"] if h.get("id") == "map_table")):
    for n in m["nodes"]:
        check((n["answer"] - m["axis"]["min"]) % m["axis"]["step"] == 0,
              "%s: junction %s at %s sits on the %s drag step" % (m["id"], n["id"], n["answer"], m["axis"]["step"]))
check(_map["waterline"]["start"] == MID, "the waterline starts at the dark row, %s" % MID)
# The escape is a GRID over the dark row's four cells (Lucas, 2026-09-18): each cell takes a group size,
# or stays dark when the cut leaves fewer groups than cells — exactly as the lit bottom row shows 4 4 and two
# dark cells. Four cells for three groups also means the panel no longer gives away the group count.
panel_grid = next(h for h in rooms["undercroft"]["hotspots"] if h.get("id") == "calibration_panel")
check(panel_grid.get("type") == "grid", "the escape panel is a grid, not a code lock")
def as_cells(sizes, n=4):
    return [str(x) for x in sizes] + ["dark"] * (n - len(sizes))
items = [it["key"] for it in panel_grid["items"]]
check(len(items) == 4, "the grid has the panel's four cells")
check([panel_grid["answer"][k] for k in items] == as_cells(cut(MID)),
      "the dark row %s -> %s, and the grid answer reads %s"
      % (MID, as_cells(cut(MID)), [panel_grid["answer"][k] for k in items]))
buckets = {b["key"] for b in panel_grid["buckets"]}
check(set(panel_grid["answer"].values()) <= buckets, "every answer value is a column the player can pick")
check({"dark", "1", "2", "3", "4"} <= buckets, "the columns offer every size the panel could need, plus dark")
check(HIGH > MID > LOW, "the panel lists its rows by height, so the dark row %s is the MIDDLE one" % MID)
check(any(str(HIGH) in (h.get("body") or "") for h in rooms["undercroft"]["hotspots"]),
      "the control panel clue states the lit rows the player generalises from")

print("\n-- the hall is ONE room in two states: dry cold open, flooded escape --")
# Merged 2026-09-18 (Lucas): the old `works` escape room was this hall after the boss, and showed up as a
# second node in the door graph. Now the dry state is a one-visit prologue (the ladder breaks behind the
# player), and the ONLY way back in is j_c7's stair, gated on the boss — which is also what floods it.
check("works" not in rooms, "there is no separate `works` room any more")
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
into = [(k, h) for k, r in rooms.items() if k != "undercroft"
        for h in (r.get("hotspots") or []) if h.get("type") == "door" and h.get("to") == "undercroft"]
check([k for k, _ in into] == ["j_c7"], "the only door back into the hall is j_c7's (%s)" % [k for k, _ in into])
check(all(h.get("direction") == "forward" and h.get("requires") == "table_c7" for _, h in into),
      "j_c7's stair is a forward door gated on the boss, so the hall is never re-entered dry")
hall = {h["id"]: h for h in rooms["undercroft"]["hotspots"]}
DRY, WET = {"not": {"solved": "j_c7"}}, {"solved": "j_c7"}
for i in ("control_panel", "map_table", "hall_ladder", "trunk_arch", "flood_door"):
    check(hall[i].get("shownWhen") == DRY, "%s shows only in the DRY hall" % i)
for i in ("lit_canyon_map", "calibration_panel", "emergency_tunnel", "back_arch", "empty_shaft"):
    check(hall[i].get("shownWhen") == WET, "%s shows only in the FLOODED hall" % i)
wash = hall["flood_wash"]["variants"][0]
check(wash["when"] == WET and wash["box"] == [0, 0, 1, 1], "the flood is a full-scene variant switched on by the boss")
check(hall["clip_flooded"]["cinemagraph"].get("state") == wash["state"],
      "the flooded clip is tagged with the flooded state, so it only plays over the flooded art")
check(not hall["clip_base"]["cinemagraph"].get("state"), "the dry clip stays base-only")
# A full-frame clip is drawn OVER every variant, so a door-open patch that is only a BOX would sit under the
# flooded clip and the opened door would never be seen (introduced and caught 2026-09-18). It must be a
# full-scene state, which stops the flooded clip because clips follow the backdrop's state.
opened = [v for v in hall["emergency_tunnel"].get("variants", []) if v.get("state") == "open"]
check(len(opened) == 1 and opened[0].get("box") == [0, 0, 1, 1] and opened[0].get("when") == {"solved": "undercroft"},
      "the door-open art is a FULL-SCENE state switched on by the panel, so the flooded clip cannot hide it")
door = hall["emergency_tunnel"]
check(door.get("endsEscape") and door.get("requires") == "calibration_panel",
      "the bronze door ends the escape and opens only on the panel's 224")
check(ids.index("flood_wash") < ids.index("emergency_tunnel") if (ids := [h["id"] for h in rooms["undercroft"]["hotspots"]]) else False,
      "the flood carrier precedes the door, so the door-open patch composites OVER the flooded art")
panel = next(h for h in rooms["undercroft"]["hotspots"] if h.get("id") == "control_panel")
check(bool(panel.get("pickup")),
      "the control panel is a PICKUP — the player can never return to re-read it, and the lock renders "
      "no instructions, so its rows have to travel in the field notebook or the escape is unsolvable")
for n in map(str, ROWS):
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
