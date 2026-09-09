#!/usr/bin/env python3
"""art_qc.py — structure the LOOK step of art generation so small defects are actually visible.

WHY (Lucas, 2026-08-31). Three `j_c1` candidates were generated; two had broken ladders — one lying at
an odd angle across the shaft, one reduced to two rope-lashed posts with no rungs. Reviewing the three
panoramas as a stacked contact sheet, I passed all three. Cropped to native resolution, the defects are
obvious. The ladder is ~200x400 px in a 3072x1024 panorama; in a 1400-px-wide contact sheet it is ~90 px
tall, which is genuinely below what can be resolved.

So the failure was not "an agent cannot see art defects" — it was reviewing at the wrong scale. This is
the same lesson the cinemagraph work already learned twice: a region averaged into a whole-frame view
disappears (mean vs p95), and "small objects need a coarse pass then crop-and-zoom"
(`notes/scenario_pipeline_vision.md`).

WHAT THIS DOES. Cuts each candidate into vertical strips at NATIVE resolution and lays the candidates
SIDE BY SIDE within each strip. Two properties matter:
  * nothing is downscaled, so a 200-px ladder stays 200 px;
  * the same region appears across all candidates in one image, which is what actually picks a winner —
    a defect is much easier to see next to a correct version of the same object than in isolation.

WHAT IT DELIBERATELY DOES NOT DO. It does not judge. There is no classifier here: it prepares the views
and prints the room's expected-object checklist (from `plannedHotspots`, which names exactly what the art
must contain), and the agent or Lucas looks. Automating the judgement would mean trusting a metric to
certify art, and the standing rule from the cinemagraph work is that metrics screen out, they cannot
certify.

  art_qc.py --chapter hierarchical_clustering --scenario canyon --room j_c1 [--strips 6]

ALSO TILES ARBITRARY IMAGES (added 2026-09-09 for the gpt-image-2.5 bake-off): `--files a.png b.png
--labels A B [--stack]` skips the scenario lookup entirely and lays the given images out the same
way. `--labels` BURNS each label onto its panel — do that for any sheet that leaves this machine,
because the left-to-right key printed to stdout does not travel with the image, and "the second
one" means nothing to someone reading it on a phone.

  art_qc.py --files x.png y.png --labels "A base" "B new" --strips 6 --out /tmp/cmp
"""
import argparse
import glob
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

ROOMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rooms")


def candidates(base, room):
    """The room's level-1 candidates in _scratch, indexed order."""
    out = []
    for p in sorted(glob.glob(os.path.join(base, "_scratch", "l1_%s_*.png" % room))):
        m = re.match(r"^l1_%s_(\d+)\.png$" % re.escape(room), os.path.basename(p))
        if m:
            out.append((int(m.group(1)), p))
    return [p for _i, p in sorted(out)]


def expected_objects(doc, room):
    """What the art MUST contain, from the design. `plannedHotspots` names every interactive object the
    room needs — so QC never has to guess what to look for, only whether it is there and well-formed.
    A hotspot with nothing to attach to is a dead room, so this list is the real acceptance criterion."""
    node = next((r for r in doc.get("rooms") or [] if r.get("key") == room), None)
    if not node:
        return []
    return [{"type": h.get("type"), "label": h.get("label"), "note": h.get("note")}
            for h in (node.get("plannedHotspots") or [])]


def grid_overlay(scene_png, out_png, step=0.05):
    """A labelled percentage grid over the room's art. The measured hotspot experiment got IoU 0.83 on
    a prominent object WITH such a grid drawn on, and coordinates could not be estimated without it."""
    im = Image.open(scene_png).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except Exception:
        f = ImageFont.load_default()
    n = int(round(1 / step))
    for i in range(n + 1):
        x, y = int(i * step * W), int(i * step * H)
        major = (i % 2 == 0)
        d.line([(x, 0), (x, H)], fill=(255, 90, 90) if major else (120, 200, 255), width=2 if major else 1)
        d.line([(0, y), (W, y)], fill=(255, 90, 90) if major else (120, 200, 255), width=2 if major else 1)
        if major:
            lab = "%.2f" % (i * step)
            d.text((x + 4, 4), lab, fill=(255, 255, 0), font=f)
            d.text((4, y + 4), lab, fill=(0, 255, 180), font=f)
    im.save(out_png)
    return out_png


def strips(paths, out_dir, n=6, labels=None, burn_labels=False, prefix="strip", stack=False):
    """One image per vertical strip, candidates laid side by side, at native resolution.

    `burn_labels` draws each panel's label ONTO the panel. Off by default so the original
    scenario flow is unchanged, but on for any sheet that leaves this machine: a strip that
    is read on a phone, or pasted into a chat, loses the left-to-right key printed to stdout,
    and then "the second one" means nothing.

    `stack` lays the panels vertically instead of horizontally — for a wide panorama strip
    that is taller than it is wide, side-by-side quickly becomes unreadably narrow on a phone.
    """
    os.makedirs(out_dir, exist_ok=True)
    ims = [Image.open(p).convert("RGB") for p in paths]
    W, H = ims[0].size
    labels = labels or [os.path.basename(p) for p in paths]
    sw = W // n
    pad = 34 if burn_labels else 0
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:                                     # noqa: BLE001
        f = ImageFont.load_default()
    made = []
    for i in range(n):
        x0 = i * sw
        x1 = W if i == n - 1 else x0 + sw
        crops = [im.crop((x0, 0, x1, H)) for im in ims]
        cw = crops[0].width
        panels = []
        for c, lab in zip(crops, labels):
            if not burn_labels:
                panels.append(c); continue
            q = Image.new("RGB", (cw, H + pad), (10, 10, 12))
            q.paste(c, (0, pad))
            ImageDraw.Draw(q).text((8, 6), lab, fill=(255, 235, 120), font=f)
            panels.append(q)
        ph = panels[0].height
        if stack:
            sheet = Image.new("RGB", (cw, ph * len(panels)), (10, 10, 12))
            for j, c in enumerate(panels):
                sheet.paste(c, (0, j * ph))
        else:
            sheet = Image.new("RGB", (cw * len(panels), ph), (10, 10, 12))
            for j, c in enumerate(panels):
                sheet.paste(c, (j * cw, 0))
        out = os.path.join(out_dir, "%s%d_of%d.png" % (prefix, i + 1, n))
        sheet.save(out)
        made.append(out)
    return made, labels


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="+", help="tile ARBITRARY images instead of a room's candidates "
                                               "(model bake-offs, before/after pairs). With --labels.")
    ap.add_argument("--labels", nargs="+", help="one label per --files entry, burnt onto each panel")
    ap.add_argument("--stack", action="store_true", help="lay panels vertically, not side by side")
    ap.add_argument("--chapter")
    ap.add_argument("--scenario")
    ap.add_argument("--room")
    ap.add_argument("--strips", type=int, default=6)
    ap.add_argument("--out", default=None)
    ap.add_argument("--grid", action="store_true",
                    help="write a labelled percentage-grid overlay of the room's committed art — "
                         "coordinates cannot be read reliably off a bare image (measured: the 0.83-IoU "
                         "hotspot result needed one)")
    a = ap.parse_args()
    if a.files:
        out = a.out or "/home/bustalab/Documents/Tools/temp/art_qc/files"
        made, labels = strips(a.files, out, a.strips, labels=a.labels,
                              burn_labels=True, stack=a.stack)
        print("panels (%s):" % ("top -> bottom" if a.stack else "left -> right"))
        for i, l in enumerate(labels, 1):
            print("  %d. %s" % (i, l))
        print("\nstrips at native resolution:")
        for p in made:
            print("  " + p)
        return 0
    missing = [f for f in ("chapter", "scenario", "room") if not getattr(a, f)]
    if missing:
        raise SystemExit("need --chapter/--scenario/--room (or --files): missing " + ", ".join(missing))
    base = os.path.join(ROOMS, a.chapter, a.scenario)
    doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    if a.grid:
        out = "/home/bustalab/Documents/Tools/temp/art_qc/grid_%s_%s.png" % (a.scenario, a.room)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        print(grid_overlay(os.path.join(base, a.room, "scene.png"), out))
        return 0
    paths = candidates(base, a.room)
    if not paths:
        raise SystemExit("no candidates for %s" % a.room)
    out = a.out or os.path.join("/home/bustalab/Documents/Tools/temp/art_qc", a.scenario, a.room)
    made, labels = strips(paths, out, a.strips)

    print("candidates (left -> right in every strip):")
    for i, l in enumerate(labels, 1):
        print("  %d. %s" % (i, l))
    print("\nMUST CONTAIN (from plannedHotspots — every one needs an object to attach to):")
    for o in expected_objects(doc, a.room):
        print("  [%s] %s%s" % (o["type"], o["label"], ("  — " + o["note"]) if o.get("note") else ""))
    print("\nstrips at native resolution:")
    for p in made:
        print("  " + p)
    print("\nLook at every strip. For each expected object: is it PRESENT, and is it WELL-FORMED "
          "(a ladder with rails and rungs, not two posts)? A candidate fails if any required object is "
          "missing or malformed — a hotspot with nothing to attach to is a dead room.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
