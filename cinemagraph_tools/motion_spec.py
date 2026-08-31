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

# The stabiliser. Unchanged from the validated night/day runs; the last sentence is THE demonstrated
# prompt rule — a two-ended loop forbids net travel, because both ends are pinned to the same still.
STABILISER_HEAD = ("locked-off static camera bolted to a tripod, the frame never moves: ")
STABILISER_TAIL = (". Continuous gentle ambient motion throughout the whole scene. {rigid} are rigid and "
                   "fixed — they do not warp, drift, breathe or change shape. Only water, cloth, flame, "
                   "smoke and haze move. NOTHING TRAVELS ACROSS THE FRAME: every movement is a small "
                   "cyclic motion that returns to where it began. Seamless natural loop.")
DEFAULT_RIGID = "The buildings, walls, stonework, ground and horizon"

BASE_NEG = ("camera movement, pan, tilt, zoom, parallax, dolly, tracking shot, whole image moving, "
            "background sliding, warping, morphing, people, crowd, cars, vehicles, new objects "
            "appearing, explosion, distorted, blurry, low quality, jittery, hard seam")
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
        if not s.get("phrase"):
            errs.append("%s: no `phrase` — it would be measured but never named in the prompt" % nm)
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
    phrases = [s["phrase"] for s in (spec.get("subjects") or []) if s.get("phrase")]
    rigid = spec.get("rigid") or DEFAULT_RIGID
    pinned = spec.get("pinned") or []          # things that must explicitly NOT move (documents, dials)
    body = ", ".join(phrases)
    if pinned:
        body += ". " + " ".join(pinned)
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
        out.append({
            "name": s["name"], "box": list(b),
            "p95": round(p95, 2), "mean": round(float(reg.mean()), 2),
            "luma": round(float(rl.mean()), 1),
            "verdict": "dead" if p95 < DEAD_P95 else ("weak" if p95 < WEAK_P95 else "alive"),
            "expect_still": bool(s.get("still")),
        })
    return out


def repair_list(measured):
    """Subjects the pipeline should tile-repair: named, boxed, and measured dead. A subject marked
    `still` is excluded — it is a check that something did NOT move, not a target."""
    return [m for m in measured if m["verdict"] == "dead" and not m["expect_still"]]


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
