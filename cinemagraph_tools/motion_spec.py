#!/usr/bin/env python3
"""motion_spec.py — a state's motion prompt as STRUCTURED SUBJECTS, and the per-subject liveness gate.

THE IDEA (Lucas, 2026-08-31, on canopic's night variant): *"it didn't animate the water but it did
animate the little flames/candles everywhere. The pipeline should detect that sort of thing, flag that
region as needing patching."*

A whole-frame liveness number cannot do that. canopic_night scored the LOWEST frame-level liveness of
the twelve night clips (2.4%) — but that figure is the average of "candles working" and "fountain
frozen". It says something is wrong and cannot say what, and it reads the same for a room where
everything moved a little as for one where half the room is perfect and half is dead.

WHAT MAKES IT TRACTABLE: **the motion prompt already IS the list of things that should move.** So the
prompt is not authored as prose — it is authored as SUBJECTS, each with a box, and the prose is
GENERATED from them (`render_prompt`). Prose and subject list therefore cannot drift, and every named
subject is necessarily measurable. After the render, each subject's box is measured; the dead ones are
named objects with known boxes, which is exactly the input the tile-repair pass wants (handoff §6).

MEASURED on canopic_night, which is the worked case:

    shrine candles   p95 13.54  ALIVE
    lion spout        p95 3.26  DEAD  -> repair
    fountain basin    p95 3.81  DEAD  -> repair
    basin rim spill   p95 2.87  DEAD  -> repair

For scale, the daytime library's light shaft — the one region that genuinely needed a repair tile in
the earlier work — sits at p95 3.13. The three water subjects land on that mark; the candles are 4x it.

TWO MEASUREMENT DECISIONS, BOTH FORCED BY DATA
1. **p95, never the mean.** A small bright object in a large box is averaged into nothing: boat's
   crown-fire scored mean 2.40 and lantern's fuel-smoke 3.43 — both read "dead", both plainly animating
   on inspection. Their p95s are 6.25 and 10.63. The mean asks "is this region mostly moving"; the
   question is "is the THING in this region moving".
2. **A flat bar, NOT one scaled by brightness — scaling was tried and rejected.** The physics argues for
   a lower bar in dark regions, but on the labelled set it misclassifies: boat's crown-fire sits in a
   bright box (mean luma 82.9) yet only reaches p95 6.25, so a brightness-scaled bar calls the one
   thing everyone agrees is animating "dead". The flat thresholds below separate every labelled case
   correctly. (The separate `liveW` statistic in `metrics_night.py` — a Weber threshold with a floor —
   is for PIXEL FRACTIONS and is a different question; don't confuse the two.)

THRESHOLDS, against every labelled region we have:
    DEAD  < 4.5   library shaft 3.13 · fountain 3.26 · basin 3.81 · rim 2.87   -> auto tile-repair
    WEAK  < 8.0   library_night shaft 4.81 · crown-fire 6.25                   -> report, don't auto-repair
    ALIVE >= 8.0  fuel-smoke 10.63 · candles 13.54 · quay water 26.88
`WEAK` exists so a genuinely modest but real motion is surfaced for a human rather than silently
re-rendered: repair is cheap but not free, and the handoff's rule stands — metrics screen out, they
cannot certify.
"""
import argparse
import json
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image

DEAD_P95 = 4.5
WEAK_P95 = 8.0

# --- sparse lit subjects -----------------------------------------------------------------------
# A p95 over a box that is almost entirely dark background is BLIND to the subject, as a matter of
# arithmetic rather than calibration: if the lit pixels are f% of the box they occupy percentiles
# (100-f) to 100, so for f < 5 the 95th percentile is *definitionally* sampling the background and
# no amount of lamp motion can move it. The beacons night set is the demonstration — rams_head's
# `village_lamps` is 0.79% lamp pixels, its lamp pixels measure tstd p95 8.09 against dark-flat
# 2.66, and the box reads 2.77; three separate clips burned re-render attempts fighting that number
# before an evaluator worked out it could not be moved (2026-09-06).
#
# NOT the brightness-scaled bar rejected above. The bar stays flat at 4.5. What changes is the
# REGION the statistic is computed over — which is the same argument this module already made once,
# when it moved from mean to p95: "the question is whether the THING in this region is moving".
# For a sparse lit subject the box p95 is still answering the region question. Two consequences
# keep this safe: the sparse path only engages when the lit fraction is small (a bright box like
# boat's crown-fire, mean luma 82.9, never takes it, so the rejected failure mode cannot recur),
# and the effective statistic is a MAX, so this can only ever rescue a subject, never newly kill
# one.
#
# KEEP THE SCOPE HONEST: this rescued 3 of the 14 dead subjects on that set. `unlit` below — a box
# holding no lit subject at all — accounted for 10, and 1 was genuinely quiet. So the bigger win was
# the DIAGNOSTIC, not the rescue; see cinemagraph_tools/AGENTS.md, "A dead subject is one of three
# things".
BRIGHT_LUMA = 80.0     # a lit pixel
SPARSE_FRAC = 0.05     # lit fraction below which the box p95 provably cannot see the subject
MIN_LIT_PX = 50        # below this there is no lit subject in the box to measure — see `unlit`
# ...and a CEILING. The scale above had a floor and no top, so an over-driven subject read as excellent:
# j_c7's `upslot_daylight` measured 47.53 — the highest number in the canyon set — and Lucas's verdict was
# "too intense, clouds dominate with really fast motion, looks odd, full re-render I think" (2026-08-31).
# Calibration is THIN and deliberately loose: braided_pool at 33.90 he called "not bad", undercroft's haze
# at 38.98 was part of the scene he rejected, and 47.53 was plainly wrong. So the bar sits between them
# and is REPORT-ONLY — it never triggers an action, because "too much motion" is a judgement about what
# the thing IS (a slot-canyon sky should be near-still; a waterfall should not) and no threshold knows that.
HOT_P95 = 35.0

# ── THE FLICKER PROBLEM, AND WHY LIVENESS HAD TO BECOME RELATIVE (2026-09-07) ──────────────────────
# Lucas, after watching the beacons set: "a lot of the images have this kind of like flicker in them
# that's part of the loop and ... it's registering in our metrics as the hero motion even though it
# isn't actually that motion ... the pipeline that we have set up is like driving the whole situation
# towards that type of loop."
#
# He was right, and the effect is not marginal. Every bar above this line is ABSOLUTE — a p95 of the
# per-pixel temporal std inside the subject's own box, compared against a fixed number. Nothing
# anywhere asked the only question that separates motion from shimmer: is this box varying MORE THAN
# THE STONE IS? Measured over all 62 named movers in networks/beacons:
#
#   * ONE had real local motion — ladder/base's waterfall, p95 29.58 against a rigid background of
#     8.82, i.e. 3.35x.
#   * 14 were between 1.5x and 3x.
#   * 47 were BELOW 1.5x, and many below 1.0x: fenwatch/base's mist band measured 9.08 while the
#     rigid stone around it measured 12.72 — the stone was varying more than the mist. crown/order_sent
#     was the starkest: beacon_fires 0.44 against a rigid background of 21.10, a clip that is pure
#     frame-wide shimmer with a completely dead hero, and one Lucas had called fine.
#
# The whole-frame p95 and the rigid-region p95 agreed to within a few percent in every clip, which is
# the signature: nothing in particular is moving, everything is boiling gently.
#
# WHY THE PIPELINE SELECTED FOR IT. A dead subject was the only finding that booked a re-render, so
# the loop re-rolled until it got a clip that scored — and a uniform shimmer scores in every box at
# once. STABILISER_TAIL was asking for exactly that ("Continuous gentle ambient motion throughout the
# whole scene", now removed; see below). Metric and prompt were pulling the same way.
#
# AND IT IS LOCAL, NOT A GLOBAL DRIFT — which rules out the tool that looks like the answer. Splitting
# the rigid-region variance into a per-frame global component and a per-pixel local one: global 0.15
# to 0.29, local 2.17 to 4.18. `colour_normalise` is a single gain per frame and its own docstring
# says it "cannot fix the small wiggle in supposedly-static pixels ... LOCAL, per-pixel and
# uncorrelated". The mask is the only thing that removes this, and the prompt is the only thing that
# stops it being generated.
#
# CALIBRATION IS THIN — ONE POSITIVE EXAMPLE — so the bars are deliberately asymmetric and the
# contrast can only ever DEMOTE a verdict, never promote one. The convicting bar is the low one, where
# the evidence is overwhelming (47 subjects, many under 1.0x, none of which Lucas could see moving).
# The 3.0x bar only downgrades `alive` to `weak`, which is report-only everywhere. Per this repo's own
# rule — a metric earns a gate only by reproducing Lucas's call several times — 3.0 is PROVISIONAL and
# wants more accepted clips behind it before anything is allowed to convict on it.
# ⚠️ RETRACTED AS A VERDICT THE SAME DAY IT WAS ADDED (2026-09-07 evening). The contrast is still
# computed and reported; it no longer changes any verdict, because it does not reproduce Lucas's calls.
# egypt/quay's `harbour_water` — a clip he ACCEPTED — measures p95 47.00 against a rigid 37.67, i.e.
# contrast 1.25, which this rule would have demoted to `dead`. The rigid reference is only as good as
# the subject boxes, and egypt's are drawn loosely enough that real water sits outside them, so the
# "rigid" region contains movers. Turn this back on only when a labelled set says it should.
CONTRAST_DECIDES = False
DEAD_CONTRAST = 1.5    # at or under this, the box is not moving more than the rigid frame: not motion
ALIVE_CONTRAST = 3.0   # provisional. below it, `alive` is demoted to `weak` and nothing else happens
MIN_RIGID_PX = 500     # too little declared-rigid area to form a reference; contrast is then unknown


def static_mask(spec, H, W):
    """The part of the frame the spec declares rigid: everything outside every MOVING subject.

    A `still` subject is not carved out — it is declared not to move, so it belongs to the region
    being tested, and carving it out would exempt the pins from the very check they exist for.

    Lives HERE rather than in `cine_judge` (where it started) so that `measure_subjects` can build the
    background reference itself. A contrast that only some callers computed would be worse than none:
    the judge would convict on it and a bare `motion_spec --clip` run would silently disagree.
    """
    import numpy as np
    m = np.ones((H, W), bool)
    for s in spec.get("subjects") or []:
        b = s.get("box")
        if not b or s.get("still"):
            continue
        y0, y1 = int(b[1] * H), max(int(b[3] * H), int(b[1] * H) + 1)
        x0, x1 = int(b[0] * W), max(int(b[2] * W), int(b[0] * W) + 1)
        m[y0:y1, x0:x1] = False
    return m


def background_p95(tstd, spec, luma=None, lit_only=False):
    """p95 of the per-pixel temporal std over the declared-rigid region — the shimmer floor.

    None when the spec leaves too little of the frame rigid to form a reference (a `[0,0,1,1]` mover
    box, say). None means "unknown", and every caller must treat it as "no contrast check", never as
    a pass or a fail.

    IN A BAKED CLIP THIS SHOULD BE NEAR ZERO. The playback mask composites the frozen still into every
    pixel it holds back, so a rigid pixel the mask covered is bit-identical frame to frame. A rigid p95
    of 8 to 13 — which is what beacons measured — is therefore not a fact about the render, it is the
    mask having admitted the shimmer as motion. That is what `cine_judge.rigid_flicker` convicts on,
    and it is fixable by re-baking at a tighter threshold rather than by any amount of GPU.
    """
    import numpy as np
    m = static_mask(spec, tstd.shape[0], tstd.shape[1])
    if lit_only:
        # LIKE FOR LIKE, and getting this wrong shipped a misleading number for one turn. A sparse lit
        # subject is measured on its BRIGHTEST pixels (`lit_p95`), because a box that is 99% dark sky
        # is arithmetically blind to a lamp in it. Dividing that by a background taken over ALL rigid
        # pixels — most of them dark — compares two different populations and inflates the ratio:
        # ladder/night's river reported contrast 2.94 that way, against an honest 0.49 on the raw box.
        # So when the subject took the sparse path, the reference must be taken over rigid pixels of
        # comparable brightness, or declared unknown.
        if luma is None:
            return None
        m = m & (luma >= BRIGHT_LUMA)
        if m.sum() < MIN_LIT_PX:
            return None            # nothing bright and rigid to compare against: UNKNOWN, not a pass
        return float(np.percentile(tstd[m], 95))
    if m.sum() < MIN_RIGID_PX:
        return None
    return float(np.percentile(tstd[m], 95))


# The stabiliser. Unchanged from the validated night/day runs; the last sentence is THE demonstrated
# prompt rule — a two-ended loop forbids net travel, because both ends are pinned to the same still.
STABILISER_HEAD = ("locked-off static camera bolted to a tripod, the frame never moves: ")
# ── REWRITTEN 2026-09-07, and this is the generation-side half of the flicker fix ─────────────────
# WHAT WAS REMOVED, AND WHY IT WAS THE ROOT CAUSE. The tail used to open with "Continuous gentle
# ambient motion throughout the whole scene." — a standing, unconditional request for exactly the
# frame-wide boil Lucas identified: "a lot of the images have this kind of like flicker in them that's
# part of the loop ... it's registering in our metrics as the hero motion even though it isn't
# actually that motion." Under a one-hero spec that clause is not merely unhelpful, it is the
# opposite of the instruction, and the relative-liveness gate above would now convict every clip it
# succeeds in producing. Metric and prompt were both selecting for the same wrong thing; this is the
# other half.
#
# It was already on record as harmful and the note was not followed far enough. AGENTS.md's
# "A room whose ONLY legitimate mover is dust" entry says this clause "demands whole-frame motion and
# then confiscates almost every outlet", which is how egypt's Library came to animate its paper. That
# was read as a problem for STARVED rooms. It is a problem for every room.
#
# "Only water, cloth, flame, smoke and haze move" went with it, for a subtler reason: it licenses
# every instance of those five substances in the frame, which in this world means every river, every
# cloud and every snowfield — while the spec names one of them as the hero. The new sentence
# subsumes it and says something stronger and unambiguous.
#
# THE STABILISER NO LONGER ASKS FOR ANY MOTION IT WAS NOT GIVEN A SUBJECT FOR. Everything the clip
# should do now comes from the subject phrases; everything else is explicitly required to be
# identical frame to frame.
STABILISER_TAIL = (". THE NAMED SUBJECT ABOVE IS THE ONLY THING IN THE ENTIRE FRAME THAT MOVES. Every "
                   "other pixel of the image is perfectly static and identical in every frame: no "
                   "ambient motion, no shimmer, no flicker, no grain, no sparkle, no crawling or "
                   "boiling texture, no rippling of any surface that is not named above, and no "
                   "brightness change anywhere. {rigid} are rigid and fixed — they do not warp, "
                   "drift, breathe, shimmer or change shape. NOTHING TRAVELS ACROSS THE FRAME: the "
                   "one movement is a small cyclic motion that returns to where it began. Seamless "
                   "natural loop.")
DEFAULT_RIGID = "The buildings, walls, stonework, ground and horizon"

# The negatives gained the shimmer vocabulary in the same change as the tail above. A negative cannot
# outvote a positive whole-frame instruction — that is the Library lesson — so this is only worth
# anything now that the positive request for ambient motion is gone. Both halves or neither.
BASE_NEG = ("camera movement, pan, tilt, zoom, parallax, dolly, tracking shot, whole image moving, "
            "background sliding, warping, morphing, people, crowd, cars, vehicles, new objects "
            "appearing, explosion, distorted, blurry, low quality, jittery, hard seam, "
            "shimmer, shimmering, flicker, flickering, film grain, noise, sparkle, twinkling texture, "
            "crawling texture, boiling pixels, whole scene shimmering, ambient motion everywhere, "
            "pulsing brightness, exposure change")
# Written documents must be PINNED, not animated: the deck day render grew a curling corner with
# visibly crawling text, and adding this plus an explicit "lies flat and still" phrase fixed it outright.
NEG_PAPER = (", paper curling, parchment lifting, page turning, writing changing, text moving, "
             "letters shifting, document deforming")


def validate(spec):
    """Structural problems that would make the gate meaningless. Returns a list of messages."""
    errs = []
    subs = spec.get("subjects") or []
    if not subs:
        errs.append("no subjects — nothing to name in the prompt and nothing to measure")
    seen = set()
    for i, s in enumerate(subs):
        nm = s.get("name")
        if not nm:
            errs.append("subject %d has no name" % i)
        elif nm in seen:
            errs.append("duplicate subject name %r" % nm)
        seen.add(nm)
        # A `still` subject is a thing declared NOT to move. It needs no motion phrase, and demanding one
        # is how the flag stayed unusable: the only way to satisfy this check was to write a movement
        # sentence for the very object you were trying to freeze, and `render_prompt` then joined it into
        # the positive mover list. Its phrase, if given, is a PIN and is rendered as one.
        if not s.get("phrase") and not s.get("still"):
            errs.append("%s: no `phrase` — it would be measured but never named in the prompt" % nm)
        # `hero` and `still` are opposite claims about the same subject — one says "this is the
        # motion the room exists to show", the other "freeze this". A subject carrying both would
        # be pinned black in the playback mask and then convicted for not moving, which is a loop
        # that cannot be satisfied by any render. See `hero_deaths`.
        if s.get("hero") and s.get("still"):
            errs.append("%s: both `hero` and `still` — a pinned subject cannot be the hero motion" % nm)
        b = s.get("box")
        if not (isinstance(b, (list, tuple)) and len(b) == 4):
            errs.append("%s: no box — cannot be measured, so the gate would silently skip it" % nm)
            continue
        if not all(0.0 <= float(v) <= 1.0 for v in b):
            errs.append("%s: box outside 0..1 — boxes are image fractions" % nm)
        elif b[0] >= b[2] or b[1] >= b[3]:
            errs.append("%s: box is empty or inverted" % nm)
    return errs


def render_prompt(spec):
    """Compose the positive prompt FROM the subjects, so prose and subject list cannot drift.

    Subject order is preserved but carries no meaning: stage AO tested naming an object first, last and
    not at all and got 4.14 / 4.14 / 4.13 — order is NOT a lever and must not be encoded as one."""
    # DE-DUPLICATED, first occurrence wins. Subjects are per-LOCATION because each needs its own box to
    # be measured — a room with three lanterns carries lights_1/2/3 — but they share one phrase, and
    # joining them naively wrote that phrase into the prompt three times. That is not a neutral repeat:
    # it triples the weight of whatever it says, and j_c7's prompt therefore said "a live, restless flame
    # that gutters and flares, their pools of amber light pulsing" three times in a row, in a clip Lucas
    # rejected twice for being over-driven ("everything is moving too fast", 2026-09-01). Naming a thing
    # once and measuring it in three boxes is the behaviour that was always intended.
    seen, phrases, still_pins = set(), [], []
    for s in (spec.get("subjects") or []):
        ph = (s.get("phrase") or "").strip()
        if not ph:
            continue
        # A `still` subject's phrase is a PIN, not a mover. Joining it into the positive list would ask
        # the model to animate the exact object the flag exists to freeze.
        if s.get("still"):
            if ph not in still_pins:
                still_pins.append(ph)
            continue
        if ph not in seen:
            seen.add(ph)
            phrases.append(ph)
    rigid = spec.get("rigid") or DEFAULT_RIGID
    pinned = list(spec.get("pinned") or []) + still_pins   # things that must explicitly NOT move
    body = ", ".join(phrases)
    if pinned:
        # rstrip the join: a pinned line already ends in a full stop and the tail opens with one, which
        # was writing ".." into every prompt that used them.
        body = (body + ". " + " ".join(pinned)).rstrip(". ")
    return STABILISER_HEAD + body + STABILISER_TAIL.format(rigid=rigid)


def render_negative(spec):
    neg = BASE_NEG + "".join(spec.get("negatives") or [])
    if spec.get("has_document"):
        neg += NEG_PAPER
    return neg


def _sample(mp4, n=16):
    d = tempfile.mkdtemp(prefix="ms_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, f"{d}/%04d.png"], check=True)
        fs = sorted(os.listdir(d))
        idx = np.linspace(0, len(fs) - 1, min(n, len(fs))).astype(int)
        return np.stack([np.asarray(Image.open(os.path.join(d, fs[i])).convert("RGB"), dtype=np.float32)
                         for i in idx])
    finally:
        subprocess.run(["rm", "-rf", d], check=False)


def measure_subjects(mp4, spec, frames=None):
    """Per-subject temporal statistics + a verdict. `frames` lets a caller reuse an already-sampled
    stack (the full metric suite samples the same clip) instead of re-decoding it."""
    st = _sample(mp4) if frames is None else frames
    tstd = st.std(axis=0).mean(axis=2)
    luma = st.mean(axis=0).mean(axis=2)
    H, W = tstd.shape
    # THE SHIMMER FLOOR, computed ONCE per clip and attached to every subject. See the flicker note
    # above: without it a frame-wide shimmer reads as motion in every box simultaneously.
    bg = background_p95(tstd, spec)
    bg_lit = background_p95(tstd, spec, luma=luma, lit_only=True)
    out = []
    for s in spec.get("subjects") or []:
        b = s.get("box")
        if not (isinstance(b, (list, tuple)) and len(b) == 4):
            continue
        x0, y0, x1, y1 = b
        a, bb = int(y0 * H), max(int(y1 * H), int(y0 * H) + 1)
        c, dd = int(x0 * W), max(int(x1 * W), int(x0 * W) + 1)
        reg, rl = tstd[a:bb, c:dd], luma[a:bb, c:dd]
        p95 = float(np.percentile(reg, 95))

        # When the subject is a sparse lit thing on a dark field, measure the thing.
        mask = rl >= BRIGHT_LUMA
        lit_frac = float(mask.mean())
        lit_p95, unlit = None, False
        if lit_frac < SPARSE_FRAC:
            lit = reg[mask]
            if lit.size >= MIN_LIT_PX:
                lit_p95 = float(np.percentile(lit, 95))
            else:
                # Nothing lit in the box at all. This is a DIFFERENT defect from "not moving" —
                # it means the box is aimed off the subject or the subject is unlit — and saying
                # so is worth more than another motion number. hood/night's `village_lamps` box
                # was pure ridgeline with zero lamps in it and reported only "p95 4.42".
                unlit = True

        # MAX, so the sparse path can only rescue. `p95` stays the raw box figure: it is what the
        # `still` pins are checked against and what every historical calibration note refers to.
        eff = max(p95, lit_p95) if lit_p95 is not None else p95

        # ---- absolute verdict, then the contrast, which may only DEMOTE it ------------------------
        verdict = "dead" if eff < DEAD_P95 else ("weak" if eff < WEAK_P95 else "alive")
        contrast, flicker_pass = None, False
        # Match the reference to the statistic: a subject rescued by the sparse-lit path is compared
        # against LIT rigid pixels, everything else against the whole rigid region.
        ref = bg_lit if lit_p95 is not None and eff == lit_p95 else bg
        if ref is not None and ref > 1e-6:
            contrast = eff / ref
            # ⚠️ THE DEMOTION IS DISABLED — see CONTRAST_DECIDES. Kept computed because the number is
            # informative; kept inert because it has never reproduced a verdict.
            if CONTRAST_DECIDES and contrast <= DEAD_CONTRAST:
                # Not moving more than the declared-rigid frame is. Whatever the absolute number says,
                # there is no LOCAL motion here — this is the 47-of-62 case. `flicker_pass` records
                # that the absolute bar was cleared on frame-wide shimmer, so a reader can tell this
                # apart from a subject that simply measured low.
                flicker_pass = (verdict != "dead")
                verdict = "dead"
            elif CONTRAST_DECIDES and contrast < ALIVE_CONTRAST and verdict == "alive":
                verdict = "weak"       # provisional bar; `weak` is report-only everywhere
        out.append({
            "name": s["name"], "box": list(b),
            "p95": round(p95, 2), "mean": round(float(reg.mean()), 2),
            "luma": round(float(rl.mean()), 1),
            "p95_lit": round(lit_p95, 2) if lit_p95 is not None else None,
            "lit_pct": round(lit_frac * 100, 2),
            "unlit": unlit,
            "verdict": verdict,
            "bg_p95": round(ref, 2) if ref is not None else None,
            "bg_all_p95": round(bg, 2) if bg is not None else None,
            "contrast": round(contrast, 2) if contrast is not None else None,
            "flicker_pass": flicker_pass,
            "expect_still": bool(s.get("still")),
            "force": bool(s.get("force_repair")),
            "hero": bool(s.get("hero")),
            "hot": bool(p95 >= HOT_P95),
        })
    return out


def hero_deaths(measured):
    """The dead subjects a loop is entitled to spend a RE-RENDER on. Everything else is advisory.

    THE POLICY THIS ENCODES (Lucas, 2026-09-06): "look for one or two hero motions to animate and
    get those going and then call it good, leaving me to do the mask and accept/commit ... rather
    than doing a bunch of cycles to get some motion in some specific spots."

    Why it needed encoding rather than a note in a prompt: `dead_subjects` is the ONLY expensive
    gate in `cine_judge` — the others either convict on something free to fix (a rebake) or merely
    warn — and it scales with how many subjects a spec names. Name eight movers and you have built
    eight independent ways to demand ten minutes of DGX. On networks/beacons that arithmetic ran 42
    re-renders against 4 rebakes for 25 clips: about seven GPU-hours, and almost all of it spent
    suppressing or chasing incidental motion rather than establishing the room's actual hero.

    So liveness is gated on the HERO, and the rest of the frame is the mask's business:

      * heroes declared -> a dead hero convicts. That is the room failing to do the one thing it
        was designed to do, and no mask can rescue it because there is no motion to let through.
      * no heroes declared (every spec authored before this flag existed) -> convict only when
        the WHOLE spec is dead, i.e. not one named mover animated. A clip with some motion in it
        is a clip a human can finish; a clip with none is a failed render.

    The second rule is what makes the change reach the ~12 scenarios already specced without
    re-authoring them, and it is deliberately the gentlest reading: it can only ever convict a
    strict subset of what the old any-dead-subject rule convicted.

    A `still` subject is never a hero — the flags are mutually exclusive and `validate` says so.
    """
    movers = [m for m in measured if not m["expect_still"]]
    if not movers:
        return []
    heroes = [m for m in movers if m.get("hero")]
    if heroes:
        return [m for m in heroes if m["verdict"] == "dead"]
    dead = [m for m in movers if m["verdict"] == "dead"]
    return dead if len(dead) == len(movers) else []


def repair_list(measured):
    """Subjects the pipeline should tile-repair: named, boxed, and measured dead. A subject marked
    `still` is excluded — it is a check that something did NOT move, not a target.

    `force_repair` on a subject adds it regardless of verdict. WEAK is deliberately not auto-repaired
    (a modest real motion should reach a human, not get silently re-rolled), but a human who has LOOKED
    and judged it too quiet needs a way to say so — Lucas on the canyon skies and lanterns, 2026-08-31.
    Setting it in the authored spec keeps that judgement with the room instead of in a shell history."""
    return [m for m in measured
            if (m["verdict"] == "dead" or m.get("force")) and not m["expect_still"]]


def hot_list(measured):
    """Subjects moving hard enough to be worth a human look. Not a failure and not auto-actioned — see
    HOT_P95. A high number means the region changed a lot, which is equally consistent with lively water
    and with the scene coming apart, and only a person can tell those two apart."""
    return [m for m in measured if m.get("hot")]


def still_violations(measured):
    """Subjects declared `still` that moved anyway. NOTE: temporal variation cannot tell MOTION from
    ILLUMINATION — a static object under a flickering light varies strongly, which is why both such
    checks fired on the night set while a landmark drift test showed zero movement. Treat a hit here as
    a question for the landmark test, never as a verdict."""
    return [m for m in measured if m["expect_still"] and m["p95"] >= WEAK_P95]


def _main():
    ap = argparse.ArgumentParser(description="render a motion prompt, or gate a clip per subject")
    ap.add_argument("spec_json")
    ap.add_argument("--clip", default=None, help="measure this clip against the spec's subjects")
    a = ap.parse_args()
    spec = json.load(open(a.spec_json, encoding="utf-8"))
    errs = validate(spec)
    if errs:
        print("SPEC ERRORS:")
        for e in errs:
            print("  -", e)
        return 1
    if not a.clip:
        print(json.dumps({"positive": render_prompt(spec), "negative": render_negative(spec)},
                         indent=1, ensure_ascii=False))
        return 0
    m = measure_subjects(a.clip, spec)
    print("%-24s %7s %7s %7s  %s" % ("subject", "p95", "mean", "luma", "verdict"))
    for r in m:
        print("%-24s %7.2f %7.2f %7.1f  %s%s" % (r["name"], r["p95"], r["mean"], r["luma"],
                                                 r["verdict"], "  (expected still)" if r["expect_still"] else ""))
    rep = repair_list(m)
    print("\n%d subject(s) need tile repair: %s" % (len(rep), ", ".join(r["name"] for r in rep) or "none"))
    for v in still_violations(m):
        print("  ? %s was declared still but varies (p95 %.2f) — check with a landmark drift test, "
              "since flickering light on a static object reads the same as motion" % (v["name"], v["p95"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
