#!/usr/bin/env python3
"""seam_stage.py — the SEAM STAGE of the art pipeline, as four gated steps.

WHY THIS IS A STAGE AND NOT A TECHNIQUE (Lucas, 2026-09-02). Seam repair was documented in three places
and required by none, so beacons committed twelve stills nobody had checked. The art phase sat between
`escape_room_scene_spec` and `escape_room_wiring` as "the human bit": no skill owned it, no stage list
gated it, and `run_all_tests.py` never touched it. This file makes the seam a stage with a RECORDED
VERDICT per room, so it can be gated instead of remembered.

That gap is now closed on both ends (kept here because this paragraph is quoted elsewhere as if it
still described the present): the `escape_room_stills` skill owns the phase, `preflight.py` gates its
entry, and since 2026-09-05 the `stills_iterate` long_agent loop runs these three steps automatically
over every committed base each cycle. What did NOT change is the last step — `accepted` is still only
ever written by a human, now through the gallery's accept button (`POST /api/accept-still`) rather
than by hand-editing scenario.json.

THE FOUR STEPS, each gating the next:

  1. SCREEN   `seam_check` every committed base. Rooms that pass are done — do not touch a clean seam.
  2. BLUR     Apply the local `gradient` op to every flagged room and re-measure. It is in-process, uses
              no model and cannot degrade the art, so trying it first costs nothing and needs no
              prediction. beacons' spindle went 3.3x/10.9 -> 0.0/0.0 this way.
  3. OCCLUDE  Only rooms still flagged after the blur. Plants the spec's authored `seamOccluder`.
  4. ACCEPT   Compare against the pre-repair image and LOOK. Revert from the undo stack if worse.

TWO ORDERING RULES, both learned the hard way, both enforced here:

  * BLUR BEFORE OCCLUDER, NEVER AFTER. The gradient averages across the seam column, so it smears
    whatever stands there. Run on beacons' already-occluded hood and ladder it dragged visible streaks
    across both masts. This module refuses to blur a room that has been occluded.
  * SEAM-FIX BEFORE ANYTHING IS BAKED FROM THE BASE. Variants, cinemagraphs and door-opens are all
    generated from `scene.png`. Repairing it afterwards does not repair them, and repairing a variant
    separately plants a DIFFERENT object at the same spot, so day and night disagree. beacons generated
    thirteen night variants from unfixed bases and threw all thirteen away.

WHY THE OCCLUDER'S OWN EDGES FAIL, and the lever that fixes it. The crop sent to the model is `--crop`
of the width; the EDITABLE band inside it is `--edit-frac` of that crop. At the defaults (0.34/0.34 on a
3072-wide pano) the band is ~355 px while the planted mast is ~130 px — so ~220 px of real scenery sits
inside the band and gets REDRAWN, and the feather (auto = band/8, ~44 px) cross-fades between two
different snowlines rather than hiding the join. Feather cures a TONAL step; it cannot cure a CONTENT
mismatch. The fix is to shrink the band toward the object's own width: beacons' anvil failed at 0.34 and
came out clean at 0.16. Hence EDIT_FRAC below.

IT RUNS ON FULL-SCENE VARIANTS TOO — `--state night` acts on `scene_night.png`. A variant is an
unmasked AI re-light of the base, so it can BREAK a seam the base had already had repaired: across
egypt's six night variants FIVE came out with a worse ratio than their base (quay 0.00 -> 6.25). That
makes it the normal case, not an edge case, and a variant is not finished when the art looks right. Each
image keeps its own stage record (`seam.states.<state>`), its own undo stack (keyed by filename stem in
`room_target`) and its own human accept — a night accept must never certify the day scene.

  seam_stage.py --chapter networks --scenario beacons --step screen|blur|occlude|status [--state night]
"""
import argparse
import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seam_check as SC                                                    # noqa: E402

EDIT_FRAC = 0.16          # see the module docstring: 0.34 redraws scenery beside the object
GRADIENT_SPAN = 96


def _load(base):
    return json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))


def worst_band(path):
    """(band, ratio, delta) for the band most in need of attention — ratio weighted by a capped delta so
    a huge ratio on an invisible step cannot win."""
    m = {n: SC.seam_ratio(path, b) for n, b in SC.BAND.items()}
    n = max(m, key=lambda k: m[k][0] * min(m[k][1], 20))
    return n, m[n][0], m[n][1]


def flagged(path, threshold, min_delta):
    _b, r, d = worst_band(path)
    return r >= threshold and d >= min_delta


def scene_file(state=None):
    """The image this stage acts on: the committed base, or a full-scene state VARIANT.

    A variant is an unmasked AI re-light of the base, and it can BREAK a seam the base had already had
    repaired — measured across egypt's six night variants, five came out worse than their base, so this
    is the normal case and not an edge case (authoring_v2/AGENTS.md). The variant therefore needs the
    same four gated steps, on its own file and its own undo stack.
    """
    return "scene.png" if not state else "scene_%s.png" % state


def stage_is_stale(path, rec):
    """True when the recorded verdict predates the image it claims to describe.

    THE STAGE RECORD SURVIVES THE FILE BEING REPLACED, and that is a trap the accept flag had already
    been bitten by (ten of beacons' day scenes carried a 09-02 accept for a 09-03 image). The same hole
    exists one level down: `screen` deliberately refuses to rewind the stage, so that re-measuring after
    a repair does not undo it — but it had no way to tell "repaired" from "regenerated since". So a room
    that was blurred, then re-generated from scratch, still read `blurred` and would refuse a blur it had
    never actually had. Hit on beacons/hood, 2026-09-03: a 50-level seam was blurred (leaving a visible
    smear the metric scored 0.0), then fixed properly by re-firing the variant, and the record still
    claimed a blur that no longer existed anywhere in the file's history.

    Compare the file's mtime against the verdict's own timestamp. Records written before `at` existed
    have no timestamp and are treated as stale, which is the safe direction: it costs a re-measure.
    """
    at = rec.get("at")
    if not at:
        return True
    try:
        return os.path.getmtime(path) > datetime.datetime.fromisoformat(at).timestamp() + 1
    except (ValueError, OSError):
        return True


def seam_state(room, state=None):
    """What the seam stage has done to this room, recorded on the node so it survives a restart and can
    be read by the gallery and by run_all_tests.

    A VARIANT's verdict is nested under `seam.states.<state>` rather than overwriting the base's. They
    are separate images with separate undo stacks and separate human accepts, and collapsing them would
    let a night accept certify a day scene (or the reverse) with nothing to show the swap happened.
    """
    s = ((room.get("authoring") or {}).get("seam") or {})
    return s if not state else ((s.get("states") or {}).get(state) or {})


def record(base, key, state=None, **fields):
    doc = _load(base)
    node = next(r for r in doc["rooms"] if r.get("key") == key)
    s = node.setdefault("authoring", {}).setdefault("seam", {})
    if state:
        s = s.setdefault("states", {}).setdefault(state, {})
    fields.setdefault("at", datetime.datetime.now().isoformat(timespec="seconds"))
    s.update(fields)
    json.dump(doc, open(os.path.join(base, "scenario.json"), "w", encoding="utf-8"), indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--step", required=True, choices=["screen", "blur", "occlude", "status"])
    ap.add_argument("--state", default=None,
                    help="act on a full-scene state VARIANT (e.g. --state night -> scene_night.png) "
                         "instead of the committed base. The variant keeps its own stage record, its own "
                         "undo stack and its own human accept.")
    ap.add_argument("--threshold", type=float, default=3.0)
    ap.add_argument("--min-delta", dest="min_delta", type=float, default=4.0)
    a = ap.parse_args()

    base = os.path.join(SC.ROOMS, a.chapter, a.scenario)
    doc = _load(base)
    fname = scene_file(a.state)
    rooms = [r for r in doc.get("rooms", []) if os.path.isfile(os.path.join(base, r["key"], fname))]
    if not rooms:
        print("no %s found — %s" % (fname, "generate the variants first" if a.state
                                    else "commit the bases first")); return 1

    if a.step == "status":
        # In --state mode the BASE's number is printed beside the variant's, because the question canon
        # actually asks is "did the re-light break a seam the base had clean?" — a variant's ratio in
        # isolation cannot answer it.
        head = f"{'room':16}{'stage':12}{'worst':>18}  accepted"
        print(head + ("      base (for comparison)" if a.state else ""))
        for r in rooms:
            s = seam_state(r, a.state)
            b, ra, d = worst_band(os.path.join(base, r["key"], fname))
            line = (f"{r['key']:16}{s.get('stage', '—'):12}"
                    f"{b + ' ' + format(ra, '.1f') + 'x/' + format(d, '.1f'):>18}"
                    f"  {'yes' if s.get('accepted') else 'NO'}")
            if a.state:
                bp = os.path.join(base, r["key"], "scene.png")
                if os.path.isfile(bp):
                    bb, bra, bd = worst_band(bp)
                    line += f"      {bb} {bra:.1f}x/{bd:.1f}"
            print(line)
        return 0

    import harness_server as H                       # imported late: only the acting steps need it

    for r in rooms:
        k = r["key"]
        p = os.path.join(base, k, fname)
        s = seam_state(r, a.state)
        b, ra, d = worst_band(p)

        if a.step == "screen":
            need = ra >= a.threshold and d >= a.min_delta
            # SCREEN MUST NOT REWIND THE STAGE (2026-09-02). Re-screening after a repair — the obvious way
            # to check the repair worked — used to write stage="screened" unconditionally, which made the
            # NEXT step refuse with "run --step blur first" even though the blur had already run. Screening
            # is a measurement; it is not an undo. Keep whatever stage the room actually reached, and never
            # downgrade a human's `accepted` verdict back to False either.
            # SCREEN NEVER SETS `accepted` (2026-09-03). It used to write accepted=(not need), which
            # contradicts this module's own closing line — "nothing is `accepted` until a human looks" —
            # and silently re-accepted rooms whose accepts had been deliberately cleared for review after
            # their art was replaced. A measurement cannot certify; only a human accept may set this flag.
            prev = s.get("stage")
            stale = stage_is_stale(p, s)
            fields = dict(band=b, ratio=round(ra, 2), delta=round(d, 2), needsWork=need)
            if prev not in ("blurred", "occluded") or stale:
                # A repair is not rewound by re-measuring — but a repair recorded against an image that
                # has since been REPLACED describes nothing, so it is reset. See `stage_is_stale`.
                fields["stage"] = "screened"
                if stale and prev in ("blurred", "occluded"):
                    fields["accepted"] = False
                    fields["humanNote"] = ((s.get("humanNote") or "") + " | STAGE RESET: recorded '%s' "
                                           "predates this image file, so it described a version that no "
                                           "longer exists." % prev).strip()
            record(base, k, a.state, **fields)
            kept = prev in ("blurred", "occluded") and not stale
            print(f"  {k:16}{b} {ra:.1f}x/{d:.1f}  ->  {'needs work' if need else 'clean, done'}"
                  f"{'  (stage kept: %s)' % prev if kept else ''}"
                  f"{'  (stage RESET from %s — file is newer)' % prev if stale and prev else ''}")

        elif a.step == "blur":
            if s.get("stage") == "occluded":
                print(f"  {k:16}SKIP — already occluded; blurring now would smear the planted object")
                continue
            if not s.get("needsWork"):
                print(f"  {k:16}skip — screened clean"); continue
            H._seam_local(p, "gradient", {"span": GRADIENT_SPAN})
            nb, nr, nd = worst_band(p)
            cleared = not (nr >= a.threshold and nd >= a.min_delta)
            record(base, k, a.state, stage="blurred", band=nb, ratio=round(nr, 2), delta=round(nd, 2),
                   needsWork=not cleared, accepted=False)
            print(f"  {k:16}{b} {ra:.1f}x/{d:.1f}  ->  {nb} {nr:.1f}x/{nd:.1f}  "
                  f"{'CLEARED' if cleared else 'still flagged -> occlude'}")

        elif a.step == "occlude":
            if not s.get("needsWork"):
                print(f"  {k:16}skip — not flagged"); continue
            if s.get("stage") != "blurred":
                print(f"  {k:16}REFUSED — run --step blur first (cheap fix must be tried before the model)")
                continue
            occl = ((r.get("authoring") or {}).get("sceneSpec") or {}).get("seamOccluder")
            if not occl:
                print(f"  {k:16}SKIP — no seamOccluder authored on the spec"); continue
            t = time.time()
            H._start("seam", "seamfix",
                     lambda k=k, o=occl, f=fname: H._run_seamfix_room("seam", base, k, crop=0.34,
                                                                      occluder=o, edit_frac=EDIT_FRAC,
                                                                      file=f), 1)
            while H.JOBS["seam"]["active"]:
                time.sleep(3)
            j = H.JOBS["seam"]
            if j.get("error"):
                print(f"  {k:16}ERROR {j['error']}"); continue
            nb, nr, nd = worst_band(p)
            record(base, k, a.state, stage="occluded", band=nb, ratio=round(nr, 2), delta=round(nd, 2),
                   needsWork=False, accepted=False)
            print(f"  {k:16}{b} {ra:.1f}x/{d:.1f}  ->  {nb} {nr:.1f}x/{nd:.1f}  ({time.time()-t:.0f}s)"
                  f"  — LOOK at it, then accept or revert")

    if a.step in ("blur", "occlude"):
        print("\nNothing is `accepted` until a human looks. Accept in the gallery's stills tab, or revert "
              "from the room's undo stack — the metric screens, it cannot certify.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
