#!/usr/bin/env python3
"""scene_states.py — enumerate a scenario's (room, WORLD-STATE) pairs. The art pipeline's unit of work.

WHY THIS EXISTS (2026-08-31). A room is not one picture. `scenario.json`'s room-level `panorama` is only
the room's BASE state; a second (third, …) state hangs off a **carrier hotspot** as
`hotspots[].variants[].panorama`. Egypt's seven day rooms each carry a full-scene night variant on an
`ambient` carrier called `night_wash`, gated `when: {solved: "library"}` — so the scenario visibly goes
dark for its whole second half.

Anything that iterates `room.panorama` therefore animates the base states and **silently ships a
half-dead second act**. That is not hypothetical: it is exactly the mistake made by hand on 2026-08-31,
when the "night deck" cinemagraph turned out to be the daytime image because the render walked
`room.panorama` and never looked at the variant carrier. Lucas caught it by eye. One function, used
everywhere, is the fix.

WHAT IT ADDS OVER `art_cli.py status`, which already lists variants:
  * **base states are first-class**, so callers get one uniform list to iterate rather than
    "the room, plus separately its variants";
  * it reads **`plannedHotspots` as well as `hotspots`**, so an authored-but-unbuilt scenario
    (canyon: nine rooms, no art, everything still on `plannedHotspots`) enumerates correctly —
    `art_cli status` reads committed hotspots only and reports nothing for one;
  * it carries each state's **art prompt**, and flags a variant that has none. Both inputs matter when
    writing a motion prompt: the image says what is *there*, the prompt says what it *is* and, for a
    variant, what CHANGED. Found this way: `quay`'s night variant has no prompt recorded at all, so that
    state's art cannot be regenerated from the scenario.

Pure and dependency-free (stdlib only) so it can be imported by the harness, the CLI and the validators
without dragging in the server.
"""
import json
import os

# A carrier's variant entry is a state iff it actually supplies art. `variants[]` is also used for
# non-art purposes (a switch-door's `to`/`when` routing carries no panorama), and those are NOT states.
_ART_KEY = "panorama"


def _is_full_scene(box):
    """A variant repaints the WHOLE backdrop iff its box is [0,0,1,1] — the same rule the engine's
    `fullSceneState` uses. This distinction is what stops the pipeline exploding combinatorially:

      * FULL-SCENE states (base, night) each need their own full-frame cinemagraph.
      * BOX variants (a door swung open, a beam laid across the water) are composited OVER whichever
        full-scene clip is playing, exactly as `pickActiveVariants` + `compositeVariants` already do
        for stills. They do NOT need a render per combination.

    So a room with 2 full-scene states and 2 independent box variants costs 2 clips + 2 small
    composites, NOT the 8 renders the cross-product would imply. Combinations are composed at runtime,
    never pre-rendered."""
    return (isinstance(box, (list, tuple)) and len(box) == 4
            and box[0] == 0 and box[1] == 0 and box[2] == 1 and box[3] == 1)


def scene_states(doc, base=None):
    """Every (room, state) pair in a scenario, in room order, base state first within each room.

    `doc`  — the parsed scenario.json.
    `base` — the scenario directory, so `exists` can be resolved on disk. Optional; None leaves it None.

    Returns a list of dicts:
        room      room key
        state     "base" for the room's own panorama, else the variant's `state` name
        carrier   None for base; the carrier hotspot's id for a variant
        source    "hotspots" | "plannedHotspots" (where the carrier was found); None for base
        scope     "full-scene" (its own full-frame render) | "box" (composited over a full-scene clip)
        box       the variant's composite region, or the carrier hotspot's box as fallback
        panorama  path as written in scenario.json (relative to play.html)
        exists    True/False/None — is the art actually on disk (None when `base` not given)
        prompt    the art prompt for THIS state: room.authoring.scenePrompt for base,
                  else the variant's own `prompt` (a day->night delta, not a whole scene)
        when      the variant's gate condition (None for base)
        built     the room's `built` flag, carried through for convenience
    """
    out = []
    for r in doc.get("rooms") or []:
        key = r.get("key")
        pano = r.get("panorama")
        out.append({
            "room": key, "state": "base", "carrier": None, "source": None,
            "scope": "full-scene", "box": [0, 0, 1, 1],
            "panorama": pano,
            "exists": (os.path.isfile(os.path.join(base, pano)) if (base and pano) else None),
            "prompt": ((r.get("authoring") or {}).get("scenePrompt") or ""),
            "when": None, "built": bool(r.get("built")),
        })
        # Both lists: a built room carries `hotspots`, an authored-but-unbuilt one carries only
        # `plannedHotspots`. Reading just one silently under-reports a whole scenario.
        for src in ("hotspots", "plannedHotspots"):
            for h in (r.get(src) or []):
                for v in (h.get("variants") or []):
                    p = v.get(_ART_KEY)
                    if not p:
                        continue          # routing-only variant (switch-door `to`/`when`) — not a state
                    box = v.get("box") if isinstance(v.get("box"), list) else h.get("box")
                    out.append({
                        "room": key, "state": v.get("state") or "?", "carrier": h.get("id"),
                        "source": src,
                        "scope": "full-scene" if _is_full_scene(box) else "box",
                        "box": box,
                        "panorama": p,
                        "exists": (os.path.isfile(os.path.join(base, p)) if base else None),
                        "prompt": (v.get("prompt") or ""),
                        "when": v.get("when"), "built": bool(r.get("built")),
                    })
    return out


def state_gaps(states):
    """Problems worth surfacing before an art or cinemagraph run. Returns a list of (level, message).

    `missing-prompt` is the one that bit us: a variant whose art exists but whose prompt was never
    recorded cannot be regenerated, and a motion prompt for it has to be written from the image alone.
    """
    gaps = []
    for s in states:
        where = "%s/%s" % (s["room"], s["state"])
        if s["state"] != "base" and not s["prompt"]:
            gaps.append(("missing-prompt", "%s: variant art with no `prompt` — cannot be regenerated" % where))
        if s["exists"] is False and s["panorama"]:
            gaps.append(("missing-art", "%s: panorama `%s` is not on disk" % (where, s["panorama"])))
        if s["state"] == "base" and s["built"] and not s["panorama"]:
            gaps.append(("built-no-art", "%s: room is built:true but has no panorama" % where))
    return gaps


def _main():
    import argparse
    ap = argparse.ArgumentParser(description="list a scenario's (room, state) pairs")
    ap.add_argument("scenario_json", help="path to a scenario.json")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    a = ap.parse_args()
    base = os.path.dirname(os.path.abspath(a.scenario_json))
    doc = json.load(open(a.scenario_json, encoding="utf-8"))
    st = scene_states(doc, base)
    if a.json:
        print(json.dumps({"states": st, "gaps": state_gaps(st)}, indent=1, ensure_ascii=False))
        return 0
    print("%-16s %-12s %-11s %-12s %-34s %-6s %s" % ("room", "state", "scope", "carrier", "panorama", "art", "prompt"))
    print("-" * 100)
    for s in st:
        print("%-16s %-12s %-11s %-12s %-34s %-6s %s" % (
            s["room"], s["state"], s["scope"], s["carrier"] or "-", s["panorama"] or "-",
            {True: "yes", False: "NO", None: "?"}[s["exists"]],
            "yes" if s["prompt"] else "MISSING"))
    gaps = state_gaps(st)
    full = [s for s in st if s["scope"] == "full-scene"]
    boxv = [s for s in st if s["scope"] == "box"]
    print("\n%d states across %d rooms — %d FULL-SCENE (one cinemagraph each) + %d BOX variants "
          "(composited over a clip, no render of their own)"
          % (len(st), len({s["room"] for s in st}), len(full), len(boxv)))
    if gaps:
        print("\ngaps:")
        for level, msg in gaps:
            print("  [%s] %s" % (level, msg))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
