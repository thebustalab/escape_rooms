#!/usr/bin/env python3
"""
seam_ops.py — panorama seam repairs that need NO image model.

The AI repairs live in `generate_scene.py seamfix`; these are the ones that are pure pixel work, so they
are instant, free, deterministic, and — the point Lucas made on 2026-08-07 — they never re-render your art
into an AI-image-of-an-AI-image. Measured across the committed trees/egypt panoramas, the wrap
discontinuity is 5–23 grey levels against a natural column-to-column difference of 5–9: the seams are
overwhelmingly **tonal steps, not structural mismatches**, which is exactly what `gradient` dissolves.

Ops (each takes an input path + output path and returns a dict describing what it did):

  gradient(...)  A 1-D Poisson correction. Take the step across the seam, split it in half, and diffuse
                 each half inward over `span` columns with a linear ramp. Structure never moves; only the
                 discontinuity is absorbed. On the real panos this drives the seam to ~0 with a residual
                 gradient far below a grey level per column. FIRST thing to try.
  crop(...)      Drop the mismatched sliver at the wrap and rescale back to full width. Loses a couple of
                 percent of the scene and introduces no invented pixels at all. Good when a narrow band is
                 genuinely wrong rather than merely mis-toned.
  roll(...)      Don't repair the seam — MOVE it. Finds the quietest meridian (lowest local detail) and
                 rolls the panorama so the wrap falls there, where a join costs least. Purely a rotation,
                 so it is lossless; usually pair it with `gradient` afterwards.

Every op is wrap-aware: `pos` is the seam location as a fraction of width (1.0 = the L/R wrap edge), the
same convention the seam band and `generate_scene seamfix --pos` use.
"""
import numpy as np
from PIL import Image


def _load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def _save(arr, path):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(path)


def _snap_to_seam(a, pos, search):
    """The TRUE seam column nearest `pos`. A seam position comes from a human dragging a band, so it is
    only approximate — and a repair applied one column off leaves the actual step untouched. Search a small
    window around the nominal spot for the column with the biggest jump from its left neighbour, and use
    that. `search` is in columns; 0 disables the snap (take `pos` literally)."""
    w = a.shape[1]
    i = int(round(pos * w)) % w
    if search <= 0:
        return i
    offs = np.arange(-int(search), int(search) + 1)
    cols = (i + offs) % w
    jumps = np.abs(a[:, cols, :] - a[:, (cols - 1) % w, :]).mean(axis=(0, 2))
    return int(cols[int(np.argmax(jumps))])


def _roll_to_wrap(a, pos, search=0):
    """Roll so the seam nearest fraction `pos` lands on the x=0 / x=w boundary. Returns (rolled, dx, col);
    `np.roll(rolled, -dx, axis=1)` restores the original framing."""
    w = a.shape[1]
    col = _snap_to_seam(a, pos, search)
    dx = (-col) % w
    return (np.roll(a, dx, axis=1) if dx else a.copy()), dx, col


def _wrap_delta(a):
    """Mean absolute difference across the wrap — the size of the seam, in grey levels."""
    return float(np.abs(a[:, -1, :] - a[:, 0, :]).mean())


def _natural_delta(a):
    """The scene's own median column-to-column difference — the bar a seam must get under to vanish."""
    return float(np.median(np.abs(np.diff(a, axis=1)).mean(axis=(0, 2))))


def measure(path, pos=1.0):
    """Report the seam size against the scene's natural detail, without changing anything."""
    a = _load(path)
    r, _, _ = _roll_to_wrap(a, pos)
    d, n = _wrap_delta(r), _natural_delta(a)
    return {"seam": round(d, 2), "natural": round(n, 2),
            "ratio": round(d / n, 2) if n else None,
            "visible": bool(n and d > n)}


def gradient(inp, out, pos=1.0, span=64):
    """Diffuse the seam's step into both sides (a 1-D Poisson solve per row). `span` columns each side."""
    a = _load(inp)
    h, w, _ = a.shape
    span = max(2, min(int(span), w // 2))
    # snap to the real step within a quarter-span of where the band was dragged — a repair one column
    # off the actual seam leaves the step fully intact, which reads as "it didn't do anything"
    r, dx, col = _roll_to_wrap(a, pos, search=max(2, span // 4))
    before = _wrap_delta(r)
    step = (r[:, 0, :] - r[:, -1, :]) / 2.0            # half the discontinuity, per row per channel
    ramp = np.linspace(1.0, 0.0, span, dtype=np.float32)
    # lift the left side UP toward the join and pull the right side DOWN to it, each fading inward
    r[:, w - span:, :] += step[:, None, :] * ramp[::-1][None, :, None]
    r[:, :span, :] -= step[:, None, :] * ramp[None, :, None]
    after = _wrap_delta(r)
    _save(np.roll(r, -dx, axis=1) if dx else r, out)
    return {"op": "gradient", "pos": pos, "span": span, "seamColumn": col,
            "seamBefore": round(before, 2), "seamAfter": round(after, 2),
            "natural": round(_natural_delta(a), 2)}


def crop(inp, out, frac=0.02):
    """Drop `frac` of the width at the wrap (split across both ends) and rescale back to full width.
    No invented pixels; costs a sliver of scene and a hair of horizontal scale."""
    a = _load(inp)
    h, w, _ = a.shape
    frac = max(0.002, min(0.15, float(frac)))
    n = max(1, int(round(w * frac / 2)))               # columns removed from EACH end
    kept = a[:, n:w - n, :]
    im = Image.fromarray(np.clip(kept, 0, 255).astype(np.uint8), "RGB").resize((w, h), Image.LANCZOS)
    im.save(out)
    return {"op": "crop", "frac": frac, "droppedEachEnd": n,
            "seamBefore": round(_wrap_delta(a), 2),
            "seamAfter": round(_wrap_delta(np.asarray(im, dtype=np.float32)), 2)}


def roll(inp, out, window=33):
    """Move the wrap to the QUIETEST meridian — the column whose neighbourhood has the least detail, so a
    join there costs least. Lossless (a pure rotation). Returns the chosen column + fraction."""
    a = _load(inp)
    h, w, _ = a.shape
    d = np.abs(np.diff(a, axis=1)).mean(axis=(0, 2))           # per-column difference, length w-1
    d = np.concatenate([d, d[:1]])                              # close the ring so the wrap is comparable
    k = max(3, int(window) | 1)
    sm = np.convolve(np.concatenate([d[-k:], d, d[:k]]), np.ones(k) / k, mode="same")[k:k + w]
    col = int(np.argmin(sm))
    a2 = np.roll(a, -col, axis=1)                               # that column becomes x=0
    _save(a2, out)
    return {"op": "roll", "column": col, "fraction": round(col / w, 4),
            "quietness": round(float(sm[col]), 2),
            "seamBefore": round(_wrap_delta(a), 2), "seamAfter": round(_wrap_delta(a2), 2)}


OPS = {"gradient": gradient, "crop": crop, "roll": roll}


def run(op, inp, out, **kw):
    """Dispatch by name. Unknown op raises ValueError (the caller surfaces it)."""
    if op not in OPS:
        raise ValueError("unknown seam op %r (have %s)" % (op, ", ".join(sorted(OPS))))
    return OPS[op](inp, out, **kw)


if __name__ == "__main__":
    import argparse
    import json
    p = argparse.ArgumentParser(description="non-AI panorama seam repairs")
    p.add_argument("op", choices=sorted(OPS) + ["measure"])
    p.add_argument("input")
    p.add_argument("--out")
    p.add_argument("--pos", type=float, default=1.0)
    p.add_argument("--span", type=int, default=64)
    p.add_argument("--frac", type=float, default=0.02)
    p.add_argument("--window", type=int, default=33)
    a = p.parse_args()
    if a.op == "measure":
        print(json.dumps(measure(a.input, a.pos), indent=1))
    else:
        kw = {"gradient": {"pos": a.pos, "span": a.span},
              "crop": {"frac": a.frac},
              "roll": {"window": a.window}}[a.op]
        print(json.dumps(run(a.op, a.input, a.out or a.input, **kw), indent=1))
