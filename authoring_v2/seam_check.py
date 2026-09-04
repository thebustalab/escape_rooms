#!/usr/bin/env python3
"""seam_check.py — MEASURE the 360 wrap seam on committed art, and render it for the eye.

WHY (Lucas, 2026-09-02). beacons shipped twelve stills whose seams were never looked at: the far-left and
far-right edges are the same line, but nothing in the pipeline checked that they joined. Five of twelve had
a structural break at the join (an object starting mid-seam) and essentially all had a sky tone step. The
`seam` field and the `seamOccluder` recipe both existed and were authored — what was missing was the step
that ASKS whether the result worked. A defect nothing measures is a defect nobody finds.

THE METRIC. Column W-1 is adjacent to column 0 once wrapped, so the join is just another column step. We
compare it against the image's OWN typical column-to-column change:

    ratio = mean|col[W-1] - col[0]|  /  median over i of mean|col[i+1] - col[i]|

A seamless wrap scores ~1: the join is as ordinary as any other column boundary. A tonal step or a
structural break scores well above that. Normalising by the image's own texture is what makes one
threshold work across a smooth sky and a busy stone yard alike.

⚠️ THE RATIO ALONE OVER-FLAGS, so a flag needs the ABSOLUTE join delta too. In a near-flat sky the
median column step approaches zero, and dividing by it makes the ratio explode on a difference nobody
can see: beacons' Crown scored 5.5x on a join delta of 2.6 levels out of 255 (invisible), while Fenwatch
scored 7.7x on 11.1 levels (a real step). Same ratio band, opposite verdicts. So a band is flagged only
when the join is BOTH statistically unusual for this image (ratio >= --threshold) AND large enough to
see (>= --min-delta levels). Both numbers are printed; judge with both.

Reported per band, because the two defects live in different places and want different fixes:
  * SKY    (top third)    — a tone step. Cheap to fix, low visual cost.
  * GROUND (bottom third) — a structural break: an object starting at the join. This is the one that
                            needs an occluder planted (per AGENTS.md rule 5a).

WHAT IT DOES NOT DO — judge. Per the standing rule from the cinemagraph work and art_qc.py, metrics
SCREEN OUT, they cannot certify. So it also writes a rolled seam strip per image (right half | left half,
join dead centre) and you look. A PASS here means "nothing obvious"; it does not mean "good".

  seam_check.py --chapter networks --scenario beacons [--strips-out DIR] [--threshold 3.0]
"""
import argparse
import json
import os
import sys

from PIL import Image

ROOMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rooms")
BAND = {"sky": (0.0, 0.34), "mid": (0.34, 0.66), "ground": (0.66, 1.0)}


def _cols(im):
    """Mean RGB per column, as a list of (r,g,b) — cheap and enough for a tonal/structural step."""
    w, h = im.size
    px = im.load()
    step = max(1, h // 256)                       # subsample rows; a seam is a full-height property
    out = []
    for x in range(w):
        r = g = b = n = 0
        for y in range(0, h, step):
            p = px[x, y]; r += p[0]; g += p[1]; b += p[2]; n += 1
        out.append((r / n, g / n, b / n))
    return out


def _mad(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / 3.0


def seam_ratio(path, band=None):
    """(ratio, join_delta, typical_delta) for one image, optionally within a vertical band."""
    with Image.open(path) as im0:
        im = im0.convert("RGB")
        w, h = im.size
        if band:
            y0, y1 = int(h * band[0]), int(h * band[1])
            im = im.crop((0, y0, w, y1))
        cols = _cols(im)
    join = _mad(cols[-1], cols[0])
    steps = sorted(_mad(cols[i], cols[i + 1]) for i in range(len(cols) - 1))
    typical = steps[len(steps) // 2] or 0.01      # median; guard a perfectly flat image
    return join / typical, join, typical


def strip(path, out_path, half=512, width=900):
    """Roll the panorama so the join is dead centre and write it — the thing you actually look at."""
    with Image.open(path) as im0:
        im = im0.convert("RGB")
        w, h = im.size
        half = min(half, w // 2)
        s = Image.new("RGB", (half * 2, h))
        s.paste(im.crop((w - half, 0, w, h)), (0, 0))
        s.paste(im.crop((0, 0, half, h)), (half, 0))
        s = s.resize((width, max(1, int(h * width / (half * 2)))), Image.LANCZOS)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        s.save(out_path, quality=92)


def images_for(base, doc):
    """Every wrap-bearing image in the scenario: each room's committed base, plus every FULL-SCENE state
    variant (box [0,0,1,1]). A variant is a fresh generation and has its OWN seam — repairing the base
    does not repair it (harness_server: seam repair was scene.png-only until variants got their own path),
    so a check that only looked at scene.png would pass a scenario whose night art is broken."""
    out = []
    for r in doc.get("rooms") or []:
        rk = r.get("key")
        p = os.path.join(base, rk, "scene.png")
        if os.path.isfile(p):
            out.append((rk, "base", p))
        for h in r.get("hotspots") or []:
            for v in h.get("variants") or []:
                b, pano = v.get("box"), v.get("panorama")
                if pano and b == [0, 0, 1, 1]:
                    vp = os.path.join(base, *pano.split("/"))
                    if os.path.isfile(vp):
                        out.append((rk, v.get("state") or "?", vp))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter")
    ap.add_argument("--scenario")
    ap.add_argument("--threshold", type=float, default=3.0,
                    help="ratio above which a band is flagged (1.0 = join is an ordinary column step)")
    ap.add_argument("--min-delta", dest="min_delta", type=float, default=4.0,
                    help="absolute join delta (0-255 levels) below which a band is NOT flagged however "
                         "extreme its ratio — a smooth sky makes the ratio explode on an invisible step")
    ap.add_argument("--strips-out", default=None, help="write rolled seam strips here for the eye")
    ap.add_argument("--require-accepted", action="store_true",
                    help="GATE MODE (run_all_tests): fail unless every committed room carries "
                         "authoring.seam.accepted. Asserts on the human verdict, not on a score — the "
                         "metric screens and cannot certify, so a good number is not a pass.")
    ap.add_argument("--all", action="store_true", help="sweep every scenario that has committed stills")
    a = ap.parse_args()

    if a.all:
        import glob as _g
        bad = 0
        for p in sorted(_g.glob(os.path.join(ROOMS, "*", "*", "scenario.json"))):
            b = os.path.dirname(p)
            if not _g.glob(os.path.join(b, "*", "scene.png")):
                continue
            d = json.load(open(p, encoding="utf-8"))
            un = [r.get("key") for r in d.get("rooms") or []
                  if os.path.isfile(os.path.join(b, r.get("key") or "", "scene.png"))
                  and not ((r.get("authoring") or {}).get("seam") or {}).get("accepted")]
            tag = os.path.relpath(b, ROOMS)
            print(f"{tag:44}{'all accepted' if not un else str(len(un)) + ' room(s) unaccepted: ' + ', '.join(un[:6])}")
            bad += bool(un)
        return 1 if bad else 0

    base = os.path.join(ROOMS, a.chapter, a.scenario)
    doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))

    if a.require_accepted:
        un = [r.get("key") for r in doc.get("rooms") or []
              if os.path.isfile(os.path.join(base, r.get("key") or "", "scene.png"))
              and not ((r.get("authoring") or {}).get("seam") or {}).get("accepted")]
        if un:
            print(f"FAIL — {len(un)} committed room(s) have no accepted seam verdict: {', '.join(un)}")
            print("Run authoring_v2/seam_stage.py (screen -> blur -> occlude), then accept by eye.")
            return 1
        print(f"all committed rooms carry an accepted seam verdict")
        return 0
    imgs = images_for(base, doc)
    if not imgs:
        print("no committed art found"); return 1

    print(f"{'room':16}{'state':12}" + "".join(f"{n + ' x/lvl':>16}" for n in ("sky", "mid", "ground")))
    print("-" * 80)
    bad = []
    for rk, state, p in imgs:
        m = {n: seam_ratio(p, b) for n, b in BAND.items()}          # name -> (ratio, join, typical)
        hits = {n: v for n, v in m.items() if v[0] >= a.threshold and v[1] >= a.min_delta}
        worst = max(hits, key=lambda n: hits[n][0]) if hits else None
        print(f"{rk:16}{state:12}"
              + "".join(f"{m[n][0]:9.1f}/{m[n][1]:5.1f}" for n in ("sky", "mid", "ground"))
              + (f"  <-- FLAG {worst}" if worst else ""))
        if worst:
            bad.append((rk, state, worst, m[worst][0], m[worst][1]))
        if a.strips_out:
            strip(p, os.path.join(a.strips_out, f"{rk}_{state}.jpg"))
    print("-" * 66)
    if a.strips_out:
        print(f"strips written to {a.strips_out} — LOOK at them; the metric only screens out.")
    if bad:
        print(f"\n{len(bad)} of {len(imgs)} images flagged "
              f"(ratio >= {a.threshold} AND delta >= {a.min_delta} levels):")
        for rk, state, band, ratio, delta in sorted(bad, key=lambda t: -t[4]):
            print(f"  {rk}/{state}: {band} join is {ratio:.1f}x an ordinary column step "
                  f"({delta:.1f} levels of 255)")
        print("\nGROUND flags want an occluder planted (AGENTS.md rule 5a); SKY-only flags are a tone step.")
        return 1
    print(f"\nall {len(imgs)} images below threshold — still LOOK at the strips.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
