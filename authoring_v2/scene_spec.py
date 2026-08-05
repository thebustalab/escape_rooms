#!/usr/bin/env python3
"""scene_spec.py — the SCENE SPEC: one structured object per room that the whole art pipeline derives from.

Phase 1 proof (2026-08-03). The unifying abstraction of the automated art pipeline: instead of writing a
gpt-image prompt by hand AND then separately marking cinemagraph hotspots, you author ONE spec per room —
an ordered left-to-right list of placed elements + atmosphere, with each element flagged for whether it
MOVES (a cinemagraph) or is a gameplay object (puzzle/door/clue). From that single spec, three things
derive deterministically:

  1. render_prompt(spec)      -> the gpt-image-2 scene prompt, in the proven left-to-right spatial format.
  2. cinemagraph_jobs(spec)   -> a batch job per animated element (motion prompt + loop already written) —
                                 the cinemagraphs fall out of the art step instead of being reverse-detected.
  3. to_hotspots(spec)        -> the hotspot stubs the room needs (ambient for animated decor, plus
                                 puzzle/door/clue for gameplay) — so the spec seeds the whole room.

You verify the network layout + a description of vibes; an LLM drafts these specs (later phase); the rest
cascades. Continuity (a landmark seen from one room must match when you enter it) is a later phase — it
adds a generation ORDER over the graph + a reference image; the `continuity` field is reserved for it here.

Boxes are deliberately NOT in the spec: an element's pixel box is localized AFTER the art is generated
(the spec says "the lantern on the far left"; a localizer finds the actual box). So cinemagraph_jobs()
emits jobs without a box — the localizer fills it before the batch runs.

This module is pure + dependency-free (stdlib only) so it's trivially testable and callable from the
harness. Run `python3 scene_spec.py <spec.json>` to see the full round-trip for a spec.

--- SPEC SCHEMA -------------------------------------------------------------------------------------------
{
  "room": "<roomKey>",
  "setting": "the centre of the engine room at the heart of a steampunk airship",
  "interior": true,                         # false for open-air / exterior rooms (some scenarios aren't inside)
  "seam": "a plain, continuous stretch of riveted brass bulkhead, uniform and unbroken",  # ALWAYS SET THIS.
                                            #   The calm, low-detail surface directly BEHIND the viewer, split
                                            #   across the extreme L/R edges. Anchoring both edges to ONE named
                                            #   surface is what makes the 360 wrap line up (stated at head AND
                                            #   tail of the prompt). Keep it boring; put interesting objects in
                                            #   the front/sides. Absent -> defaulted from `interior`.
  "elements": [                             # ORDERED; the author (or LLM) lays them out left -> right
    {
      "id": "boiler",                      # becomes the hotspot id
      "at": "on the far left",             # spatial phrase; leads the prose AND fixes L->R order
      "desc": "a riveted boiler, its firebox door ajar",
      # AT MOST ONE role flag:
      "animate": {"motion": "the firebox glowing and flickering", "loop": "boomerang"},  # -> ambient cinemagraph
      # "puzzle": true,                    # gameplay: a GRADED puzzle hotspot (the WebR analysis; wired separately)
      # "switch": true,                    # a world-state CONTROL (lever/dial/valve) — NOT a graded puzzle; wired later
      #                                    #   (kept distinct so real puzzles aren't confused with state switches)
      # "door": {"direction": "back", "to": "cargo",    # a doorway
      #   "opensOnto": [                   # OPTIONAL: >1 open-view for ONE door (e.g. a monorail car whose
      #     {"state": "to_station1", "reveal": "the door open onto the misty lower platform beyond"},
      #     {"state": "to_station2", "reveal": "the door open onto the higher sunlit platform beyond"}]},
      #                                    #   world-state switch picks which station it looks out on. Each
      #                                    #   open-view -> a state-tagged door-open variant on the door
      #                                    #   hotspot (one door BOX; runtime pick-by-state is later wiring).
      # "clue": true                       # a readable clue
    }
  ],
  "atmosphere": "hot amber-and-red furnace glow, brass highlights, heavy haze and steam, film grain, tense",
  "negatives": "no people, no lettering, no captions, no text",
  "continuity": []                          # RESERVED (phase 2): [{"element": "<id>", "landmark": "<name>"}]
}
"""
import sys, json


def _cap(s):
    return s[:1].upper() + s[1:] if s else s


def _period(s):
    s = (s or "").strip()
    return s if not s or s[-1] in ".!?" else s + "."


def _seam_anchor(spec):
    """The surface at the ±180° wrap (directly BEHIND the viewer), split across the extreme L/R edges. Specs
    SHOULD set `seam` to a calm, continuous, low-detail surface; absent, default from `interior` so even
    un-updated specs get an anchor. Returned WITHOUT trailing punctuation for mid-sentence embedding."""
    s = (spec.get("seam") or
         ("a plain, continuous stretch of wall, uniform and unbroken" if spec.get("interior", True)
          else "an open, unbroken stretch of sky and distant horizon"))
    return s.strip().rstrip(".")


def render_prompt(spec):
    """Deterministically render a scene spec into a gpt-image-2 prompt in the house left-to-right format.
    The panorama's L/R wrap is anchored to a NAMED seam surface, stated at BOTH the head and tail of the
    prompt, so the extreme edges depict the SAME thing and line up when wrapped — the biggest lever on seam
    quality. gpt-image describes the far-left and far-right as one surface instead of two clashing objects."""
    setting = spec.get("setting", "the centre of the room")
    seam = _seam_anchor(spec)
    intro = f"This is a seamless 360-degree panorama from {setting}."
    seam_head = (f"Directly behind the viewer, split across the extreme left and extreme right edges, is "
                 f"{seam}: the far-left edge and the far-right edge are the two halves of this one surface "
                 f"and must match exactly in colour, texture, and lighting, joining into a single continuous, "
                 f"unbroken whole when the image wraps left to right.")
    # the left->right sweep: each element as "{at}, {desc}"
    sweep = "; ".join(f"{e.get('at', 'ahead')}, {e['desc']}" for e in spec.get("elements", []) if e.get("desc"))
    sweep = _period(_cap(sweep))
    atmosphere = _period(spec.get("atmosphere", ""))
    negatives = _period(spec.get("negatives") or "no people, no lettering, no captions, no text")
    seam_tail = (f"Again: the extreme left and right edges must align perfectly into {seam}, "
                 f"with no visible seam, join, or repetition.")
    parts = [intro, seam_head, sweep, atmosphere, negatives, seam_tail]
    return " ".join(p for p in parts if p)


def cinemagraph_jobs(spec):
    """Every element flagged `animate` becomes a cinemagraph batch job (box filled later by the localizer)."""
    jobs = []
    for e in spec.get("elements", []):
        a = e.get("animate")
        if a and a.get("motion"):
            jobs.append({"type": "cinemagraph", "hotspotId": e["id"], "prompt": a["motion"],
                         "loop": a.get("loop", "boomerang")})
    return jobs


def dooropen_jobs(spec):
    """Each open-view a door DECLARES (`door.opensOnto`) becomes a state-tagged VARIANT job — a masked
    door-open reveal painted into the door's own box. This lets ONE door look out on more than one place
    (a monorail car whose world-state switch picks which station it opens onto) while staying a SINGLE door
    hotspot / single box in the panorama. Emitted as `variant` jobs because the batch already runs those
    end-to-end (var_<id>_<state>.png -> the door hotspot's variants[]); no new generation primitive. The
    runtime pick-by-world-state is deferred engine wiring — this only guarantees ALL the open-door ART is
    generated in the art step. Box is filled from the door hotspot at apply/run time (like cinemagraphs)."""
    jobs = []
    for e in spec.get("elements", []):
        d = e.get("door")
        if not isinstance(d, dict):
            continue
        for i, ov in enumerate(d.get("opensOnto") or []):
            reveal = (ov.get("reveal") or "").strip()
            if not reveal:
                continue
            job = {"type": "variant", "hotspotId": e["id"],
                   "state": (ov.get("state") or "open%d" % (i + 1)), "prompt": reveal}
            if ov.get("when") is not None:
                job["when"] = ov["when"]   # RESERVED: the wiring pass ties each view to the switch's state
            jobs.append(job)
    return jobs


def to_hotspots(spec):
    """The hotspot stubs the spec implies: ambient for animated decor, plus puzzle/door/clue for gameplay.
    Boxes are filled by the post-gen localizer; gameplay grading/wiring is authored separately as today."""
    out = []
    for e in spec.get("elements", []):
        base = {"id": e["id"], "label": e.get("desc", e["id"])[:60]}
        if e.get("puzzle"):
            out.append({**base, "type": "puzzle"})
        elif e.get("switch"):
            out.append({**base, "type": "switch"})   # world-state control; reclassified to its real mechanic in wiring
        elif e.get("lock"):
            out.append({**base, "type": "lock"})     # ungraded escape gate (keypad / grid-select); wired separately
        elif e.get("door"):
            out.append({**base, "type": "door", **{k: v for k, v in e["door"].items()}})
        elif e.get("clue"):
            out.append({**base, "type": "clue"})
        elif e.get("animate"):
            out.append({**base, "type": "ambient"})   # decoration-only: no player marker, just the cinemagraph
    return out


# Spatial phrase -> approximate x-centre (fraction). Longer phrases first so "left of centre" beats "left".
_POS = [
    ("far left", 0.08), ("far-left", 0.08),
    ("left of centre", 0.36), ("left of center", 0.36), ("centre-left", 0.36), ("center-left", 0.36),
    ("right of centre", 0.64), ("right of center", 0.64), ("centre-right", 0.64), ("center-right", 0.64),
    ("far right", 0.92), ("far-right", 0.92),
    ("centre", 0.50), ("center", 0.50), ("ahead", 0.50), ("middle", 0.50),
    ("left", 0.20), ("right", 0.80),
]


def _x_from_at(at):
    a = (at or "").lower()
    for kw, x in _POS:
        if kw in a:
            return x
    return None


def approx_boxes(spec, width=0.16, top=0.25, bottom=0.80):
    """Deterministic APPROXIMATE box per element from its spatial phrase (falling back to even left-to-right
    distribution by order). NOT pixel-accurate — a nudgeable starting box: auto-localization on stylised
    panoramas proved unreliable (both a vision LLM and Grounding DINO), so for low-stakes ambience we seed a
    rough box from the layout and let the flat editor fix it. Returns {id: [x0,y0,x1,y1]}.

    Sizing (tuned 2026-08-03): a box that reliably CONTAINS the object means every nudge is shrink-only (vs a
    tight box that misses it and has to be hunted), so we bias generous — wider especially, since the x-phrase
    is the coarsest guess. But NOT maximal: a cinemagraph animates its whole crop, so an over-large box
    animates surrounding static wall and lengthens the composite edge. width/top/bottom are the tuning knobs."""
    els = [e for e in spec.get("elements", []) if e.get("id")]
    n = len(els) or 1
    out = {}
    for i, e in enumerate(els):
        x = _x_from_at(e.get("at"))
        if x is None:
            x = (i + 0.5) / n
        out[e["id"]] = [round(max(0.0, x - width / 2), 4), top, round(min(1.0, x + width / 2), 4), bottom]
    return out


def _demo(path):
    spec = json.load(open(path, encoding="utf-8"))
    print("=" * 90)
    print("SCENE SPEC ROUND-TRIP —", spec.get("room"))
    print("=" * 90)
    print("\n--- 1. render_prompt(spec)  → the gpt-image-2 prompt --------------------------------------\n")
    print(render_prompt(spec))
    print("\n--- 2. cinemagraph_jobs(spec)  → batch jobs that fall out for free ------------------------\n")
    for j in cinemagraph_jobs(spec):
        print(f"  • {j['hotspotId']:24} [{j['loop']}]  {j['prompt']}")
    dj = dooropen_jobs(spec)
    if dj:
        print("\n--- 2b. dooropen_jobs(spec)  → per-view door-open art (state-tagged variants) --------------\n")
        for j in dj:
            print(f"  • {j['hotspotId']:24} [{j['state']}]  {j['prompt']}")
    print("\n--- 3. to_hotspots(spec)  → hotspot stubs the spec seeds ----------------------------------\n")
    for h in to_hotspots(spec):
        extra = " ".join(f"{k}={v}" for k, v in h.items() if k not in ("id", "type", "label"))
        print(f"  • {h['type']:8} {h['id']:24} {extra}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python3 scene_spec.py <spec.json>", file=sys.stderr); sys.exit(2)
    _demo(sys.argv[1])
