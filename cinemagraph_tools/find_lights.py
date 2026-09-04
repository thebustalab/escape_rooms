#!/usr/bin/env python3
"""find_lights.py — find the practical lights in a panorama, by measuring them.

WHY NOT ASK A MODEL. The obvious route is `localizer.py --engine gpt4o` with "where are the lanterns".
That was tried on all nine canyon rooms (2026-08-31) and it returned a box for every room with
**confidence 1.00 every time**, including for two rooms whose boxes turn out to contain nothing but bare
sandstone. Four tile repairs were then spent animating rock. A localizer asked for an object that is not
in the picture does not say "absent" — it points somewhere.

A practical light is not a semantic question, it is a photometric one, and that makes it measurable:

  * **bright** — near the top of the image's own value distribution (a percentile, not a fixed level, so
    a dim night interior and a sunlit canyon are both handled);
  * **warm** — R meaningfully above B. This is what separates a flame from a bright patch of sky, a
    specular glint on water, or a pale rock face catching the sun;
  * **small and compact** — a lamp is a blob. A large warm region is a sunlit wall, not a light.

Each surviving blob is dilated into a box with margin, because what must animate is the flame AND the
pool of light it throws — a box tight on the bulb measures nothing when the flame flickers.

WHAT IT DOES NOT DO. It does not decide. It writes a contact sheet of every candidate at native
resolution (with a 2x zoom, since a lamp is ~40 px in a 3072x1024 panorama) and the agent or Lucas LOOKS
before any of it reaches a motion spec. That is the same rule the whole pipeline runs on: measure to
find the candidates, look to confirm what they are.

  find_lights.py --chapter hierarchical_clustering --scenario canyon [--room j_c1] [--top 6]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rooms")

BRIGHT_PCT = 99.5      # a light is in the top fraction of a percent of pixels — they are rare by nature
WARM_MIN = 75.0        # R - B, in grey levels. CALIBRATED, not guessed (canyon, 2026-08-31): every blob
                       # confirmed by eye as a flame measured 80-158; every confirmed non-flame — the
                       # daylight shaft, sunlit rock, the reading-table's glowing glass pane, open sky —
                       # measured 42-63. The gap is clean and this sits in the middle of it. Warmth, not
                       # brightness, is what separates a lamp from everything else that is bright.
MIN_PX = 12            # smaller than this is sensor-grade speckle, not a lamp
MAX_AREA_FRAC = 0.004  # bigger than this is a lit surface (sky, sunlit wall), not a practical light
BOX_MARGIN = 2.2       # grow the blob to include the light POOL, which is what actually flickers


def find(png, bright_pct=BRIGHT_PCT, warm_min=WARM_MIN, top=8):
    """Candidate lights, brightest-first. Returns dicts with a normalised box and its measurements."""
    im = Image.open(png).convert("RGB")
    W, H = im.size
    a = np.asarray(im, dtype=np.float32)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    val = a.max(axis=2)
    warm = R - B
    thr = np.percentile(val, bright_pct)
    mask = (val >= thr) & (warm >= warm_min)
    lab, n = ndimage.label(mask)
    if not n:
        return []
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        blob = (lab[sl] == i)
        area = int(blob.sum())
        if area < MIN_PX or area > MAX_AREA_FRAC * W * H:
            continue
        ys, xs = sl[0], sl[1]
        cy, cx = (ys.start + ys.stop) / 2, (xs.start + xs.stop) / 2
        bh, bw = max(ys.stop - ys.start, 6), max(xs.stop - xs.start, 6)
        # grow to take in the light pool, then clamp
        gh, gw = bh * BOX_MARGIN, bw * BOX_MARGIN
        x0, x1 = max(0, cx - gw / 2), min(W, cx + gw / 2)
        y0, y1 = max(0, cy - gh / 2), min(H, cy + gh / 2)
        out.append({
            "box": [round(x0 / W, 4), round(y0 / H, 4), round(x1 / W, 4), round(y1 / H, 4)],
            "px": [int(x0), int(y0), int(x1), int(y1)],
            "area_px": area,
            "peak": round(float(val[sl][blob].max()), 1),
            "warm": round(float(warm[sl][blob].mean()), 1),
        })
    out.sort(key=lambda c: (c["peak"], c["area_px"]), reverse=True)
    return out[:top]


def merge_boxes(cands, gap=0.02):
    """Union candidates that sit close together: a row of lamps along a ledge should animate as ONE
    subject, and a cluster of tiny separate boxes is both harder to render and harder to judge."""
    boxes = [c["box"][:] for c in cands]
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if (a[0] - gap <= b[2] and b[0] - gap <= a[2]
                        and a[1] - gap <= b[3] and b[1] - gap <= a[3]):
                    boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    boxes.pop(j)
                    changed = True
                    break
            if changed:
                break
    return [[round(v, 4) for v in b] for b in boxes]


def contact_sheet(png, cands, out_path, zoom=2, label_h=22):
    """Every candidate cropped at native resolution and zoomed, stacked with its measurements. This is
    the artefact a human (or the agent) actually judges — the numbers only shortlist."""
    im = Image.open(png).convert("RGB")
    crops, labels = [], []
    for k, c in enumerate(cands, 1):
        x0, y0, x1, y1 = c["px"]
        pad_x, pad_y = int((x1 - x0) * 0.8) + 20, int((y1 - y0) * 0.8) + 20
        box = (max(0, x0 - pad_x), max(0, y0 - pad_y),
               min(im.width, x1 + pad_x), min(im.height, y1 + pad_y))
        cr = im.crop(box)
        cr = cr.resize((cr.width * zoom, cr.height * zoom), Image.LANCZOS)
        crops.append(cr)
        labels.append("%d  box %s  peak %.0f  warm %.0f  area %d px"
                      % (k, c["box"], c["peak"], c["warm"], c["area_px"]))
    if not crops:
        return None
    w = max(c.width for c in crops)
    h = sum(c.height + label_h for c in crops)
    sheet = Image.new("RGB", (w, h), (12, 12, 16))
    d = ImageDraw.Draw(sheet)
    y = 0
    for cr, lab in zip(crops, labels):
        d.text((4, y + 5), lab, fill=(255, 216, 140))
        y += label_h
        sheet.paste(cr, (0, y))
        y += cr.height
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    return out_path


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--room", default=None, help="one room; default every built room")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--bright-pct", type=float, default=BRIGHT_PCT)
    ap.add_argument("--warm-min", type=float, default=WARM_MIN)
    ap.add_argument("--out", default="/home/bustalab/Documents/Tools/temp/art_qc/lights")
    a = ap.parse_args()

    base = os.path.join(ROOMS, a.chapter, a.scenario)
    doc = json.load(open(os.path.join(base, "scenario.json"), encoding="utf-8"))
    rooms = ([a.room] if a.room
             else [r["key"] for r in doc.get("rooms", []) if r.get("panorama")])
    summary = {}
    for room in rooms:
        png = os.path.join(base, room, "scene.png")
        if not os.path.isfile(png):
            continue
        cands = find(png, a.bright_pct, a.warm_min, a.top)
        merged = merge_boxes(cands)
        sheet = contact_sheet(png, cands, os.path.join(a.out, "%s_%s.png" % (a.scenario, room)))
        summary[room] = {"candidates": cands, "merged": merged, "sheet": sheet}
        print("%-12s %d candidate light(s), %d after merge  %s"
              % (room, len(cands), len(merged), sheet or "(no sheet)"))
        for c in cands:
            print("    box %-34s peak %5.0f  warm %5.0f  area %4d px" %
                  (c["box"], c["peak"], c["warm"], c["area_px"]))
    print("\nLOOK at every sheet before any of these reaches a motion spec. The measurement shortlists "
          "warm compact bright blobs; only your eye knows whether a given one is a lamp, a glinting "
          "wet rock, or a scrap of bright sky.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
