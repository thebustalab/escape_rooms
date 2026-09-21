#!/usr/bin/env python3
"""
water_states.py — author the shaft's WATER VIEWS into the specs, generated from the router.

WHY (Lucas, 2026-09-20). Now that the water gates the doors (`wire_maze.py`), the art has to be honest
about it: **no closed door may look dry, and no open door may look flooded.** A room therefore needs one
view per distinct picture of the water ON THE SPANS IT CAN SEE, across the configurations the player can
stand there in — 19 views over the 8 rooms, of which 8 are the base art and the basin's 2 extra are
already authored by hand. This writes the remaining 9 (station1 +2, station2 +5, station3 +1,
spillway +1) the same way the basin does, and it derives which span is wet in which view from the SAME
router that reproduces Lucas's hand-authored puzzle, so the art cannot disagree with the gates.

Per non-base view it writes, on the room's `sceneSpec`:
  * `states.<name>` — a KEEP-the-scene overlay changing only the water on the ways out: a `change` line,
    hard `constraints` naming every span as curtained or clear, and a per-door `look` clause;
and on the room's `plannedHotspots`:
  * one full-scene `ambient` carrier ("The water on the ways out") whose `variants[].when` conditions are
    the lever configurations that produce each view — the pattern the basin already proves works.

THE BASE VIEW IS THE ARRIVAL VIEW. Whichever configuration the player FIRST reaches a room in gets the
base art, and every other view is a variant. That way the fallback (no variant matching) is never a lie.

Run: python3 water_states.py            # dry run: the plan, writes nothing
     python3 water_states.py --write    # applies to ../scenario.json (timestamped backup first)
"""
import collections
import json
import os
import shutil
import sys
import time

from router import present_bridges, cuts_for, diverter_events
import reach_art as ra
import wire_maze as wm

HERE = os.path.dirname(os.path.abspath(__file__))
SCEN = os.path.join(HERE, "..", "scenario.json")
PJSON = os.path.join(HERE, "..", "puzzle.json")
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "authoring_v2"))
import scene_spec  # noqa: E402

CARRIER = "The water on the ways out"

# ROUND 2 (respec_review_round2.md N1/N4/N5, 2026-09-21). A span can be in FOUR situations relative to the
# base (arrival) view, and each needs its own wording — giving "the curtain moved away" to a span that was
# never wet made the edit model PAINT a curtain beside a dry ladder, and three such clauses described three
# falls in a two-stream world. Moved water goes OUT OF SIGHT, and the count covers the whole picture.
STAYS_DRY = "unchanged — it stays exactly as it is, dry, with no water on or near it"
STAYS_WET = "keeps its curtain exactly as it is"


def DRIES(parts):
    return (f"its curtain is GONE — the stream has been turned aside into the tangle and out of sight — and its "
            f"{parts} run dry")


def WETS(parts):
    return ("a curtain of water — one of the well's 2 streams — now drops out of the tangle overhead and comes "
            f"down THROUGH it, so its {parts} are plainly BEHIND the water and nothing could cross it")


# the noun each curtain is named by in its motion phrase (a motion prompt has no antecedent for "it")
NOUN = {("station1", "down_ladder"): "the gap over the ladder going down", ("station1", "across_bridge"): "the bridge",
        ("station2", "up_ladder"): "the ladder going up", ("station2", "descent"): "the long descent",
        ("station2", "across_bridge"): "the bridge", ("station3", "back_bridge"): "the bridge to the junction",
        ("station3", "on_bridge"): "the bridge to the hall", ("spillway", "down_ladder"): "the hatch in the floor"}
PARTS = {"up_ladder": "rungs", "down_ladder": "rungs", "descent": "rungs and planks"}   # everything else: planks

# N5: a view with NO curtain left still needs a big, near, room-specific mover — never a small chute.
ALL_CLEAR_HERO = {
    # motion-ONLY: a state-only element always injects its desc into the edit prompt as something to CHANGE,
    # which would paint new cressets into the gap the removed curtain leaves (round-3 review).
    "station1": {"up_ladder": {"motion": {"moves": True, "phrase": ("the cresset flames beside the ladder going up "
                 "flickering and leaning, their light wavering on the wet stone")}}},
    "station2": {"font": {"motion": {"moves": True, "phrase": ("the water spilling from spout to spout down the "
                 "stepped settling troughs and turning the small overshot wheel")}}},
}


def curtain_phrase(room, eid):
    return f"the curtain of water pouring steadily down through {NOUN.get((room, eid), 'the crossing')}, its edges shifting"


def arrival_order():
    """(room, config) states in the order the player can first reach them — BFS from the start."""
    pj = json.load(open(PJSON, encoding="utf-8"))
    present = present_bridges(set(pj["absentBridges"]))
    divs = diverter_events()
    start = ((0, 0), (0, 0, 0, 0))
    seen, order, q = {start}, [start], collections.deque([start])
    while q:
        pos, bits = q.popleft()
        passable = present - cuts_for(ra.SOURCES, bits, present, divs)
        nxt = [(nb, bits) for nb in ra.neighbors(pos, passable)]
        if pos in ra.SWITCHES:
            _, idx = ra.SWITCHES[pos]
            f = list(bits)
            f[idx] = 1 - f[idx]
            nxt.append((pos, tuple(f)))
        for s in nxt:
            if s not in seen:
                seen.add(s)
                order.append(s)
                q.append(s)
    return order, present, divs


def plan():
    doc, doors = wm.plan()
    by_room = collections.defaultdict(list)
    for (rk, eid), d in doors.items():
        by_room[rk].append((eid, d))
    order, present, divs = arrival_order()

    out = {}
    for rk, pos in wm.ROOM_AT.items():
        spans = [(eid, d) for eid, d in by_room[rk]]
        views = collections.OrderedDict()                 # view-key -> list of configs, arrival order
        for p, bits in order:
            if p != pos:
                continue
            cuts = cuts_for(ra.SOURCES, bits, present, divs)
            key = tuple(sorted(eid for eid, d in spans if d["bridge"] in cuts))
            views.setdefault(key, []).append(bits)
        out[rk] = (spans, views)
    return doc, out


def name_for(wet_ids, spans):
    if not wet_ids:
        return "all_clear"
    return "wet_" + "_".join(sorted(wet_ids))


def cond_for(configs):
    """A condition true exactly on this view's configurations, over d1..d4."""
    terms = []
    for b in configs:
        terms.append({"all": [{"eq": [wm.KEYS[i], wm.VAL[v]]} for i, v in enumerate(b)]})
    return terms[0] if len(terms) == 1 else {"any": terms}


def build(doc, plan_):
    rooms = {r["key"]: r for r in doc["rooms"]}
    written = []
    for rk, (spans, views) in plan_.items():
        if len(views) < 2:
            continue                                        # one picture: the base art is the whole story
        node = rooms[rk]
        spec = node["authoring"]["sceneSpec"]
        labels = {eid: d["label"] for eid, d in spans}
        keys = list(views)
        base, extras = keys[0], keys[1:]                    # base = the ARRIVAL view
        spec.setdefault("states", {})
        variants = []
        for key in extras:
            st = name_for(key, spans)
            clauses, elements = [], {}
            for eid, d in spans:
                was, now = eid in base, eid in key
                parts = PARTS.get(eid, "planks")
                if was and now:
                    txt = STAYS_WET                                   # inherits the base hero's motion
                elif was and not now:
                    txt = DRIES(parts)
                    elements[eid] = {"motion": None}                   # retire its curtain
                elif now:
                    txt = WETS(parts)
                    elements[eid] = {"motion": {"moves": True, "phrase": curtain_phrase(rk, eid)}}
                else:
                    txt = STAYS_DRY
                clauses.append("%s: %s." % (labels[eid], txt))
            n = len(key)
            if n == 0:
                elements.update(ALL_CLEAR_HERO.get(rk, {}))
                count = "NO water falls free through open air anywhere in this picture."
            else:
                what = ", ".join("the curtain through " + NOUN.get((rk, e), labels[e]) for e in key)
                count = ("EXACTLY %d %s of water %s free through open air in this picture — %s — and NO OTHERS."
                         % (n, "fall" if n == 1 else "falls", "drops" if n == 1 else "drop", what))
            spec["states"][st] = {
                "change": "where the falling water lands on the ways off this landing",
                "constraints": (" ".join(clauses) + " " + count + " Nothing else in the picture moves, "
                                "changes, is added or is taken away — same scene, same camera, same objects, "
                                "same light."),
                "elements": elements,
                "_why": "lever configurations %s (cave_engine/water_states.py — regenerate, do not hand-edit)"
                        % ", ".join("".join(map(str, b)) for b in views[key]),
            }
            variants.append({"state": st, "box": [0, 0, 1, 1], "when": cond_for(views[key])})
            written.append((rk, st))
        node["authoring"]["scenePrompt"] = scene_spec.render_prompt(spec)
        ph = node.setdefault("plannedHotspots", [])
        ph[:] = [h for h in ph if h.get("label") != CARRIER]
        ph.insert(0, {"type": "ambient", "label": CARRIER, "noElement": True, "box": [0, 0, 1, 1],
                      "variants": variants,
                      "note": ("Full-scene water-state carrier, generated by cave_engine/water_states.py. "
                               "The BASE art is the view the player ARRIVES in (%s wet); each variant is "
                               "another picture of the same landing with the water moved. Keep in lockstep "
                               "with the door gates — both come from the router."
                               % (", ".join(base) if base else "nothing"))})
        # the doorPrompt predates states and can only describe ONE span changing — it is now misleading
        node["authoring"].pop("doorPrompt", None)
    return doc, written


def main():
    doc, plan_ = plan()
    print("WATER VIEWS per room (base = the view the player ARRIVES in)\n")
    total = 0
    for rk, (spans, views) in plan_.items():
        total += len(views)
        print("  %-9s %d view(s)   spans: %s" % (rk, len(views), ", ".join(eid for eid, _ in spans)))
        for i, (key, cfgs) in enumerate(views.items()):
            print("      %-5s %-22s wet: %-24s configs: %s"
                  % ("BASE" if i == 0 else "var", name_for(key, spans),
                     ", ".join(key) or "nothing",
                     " ".join("".join(map(str, b)) for b in cfgs)))
    print("\nTOTAL views: %d  (stills %d + clips %d = %d renders)" % (total, total, total, total * 2))
    doc2, written = build(json.loads(json.dumps(doc)), plan_)
    print("states this run would write: %d -> %s" % (len(written), written))
    if "--write" in sys.argv:
        shutil.copy2(SCEN, SCEN + ".bak_%s_water_states" % time.strftime("%Y%m%d_%H%M%S"))
        json.dump(doc2, open(SCEN, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("\nwrote", os.path.relpath(SCEN, HERE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
