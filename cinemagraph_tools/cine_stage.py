#!/usr/bin/env python3
"""cine_stage.py — the cinemagraph stage for ONE (room, state): render, gate, measure, repair, re-measure.

This is handoff §6's repair loop, automated. Per state:

  1. RENDER the full frame at the settled recipe (`cine_render.graph`).
  2. GATE on the four checks that transfer: frame-0 correlation (binary), landmark drift, loop jump.
     NOT colour drift or incoherence — their thresholds are daytime calibrations (see cine_render).
  3. MEASURE each NAMED SUBJECT from the motion spec (`motion_spec.measure_subjects`), p95 per box.
  4. REPAIR the dead ones: re-render each as its own tile so it becomes the dominant subject, then
     composite it back. "Elements refuse to animate because of COMPETITION FOR THE FRAME, not the
     wording" — the emporion awning stayed dead through three full-frame prompt variants and went from
     mean temporal std 4.35 to 13.95 when rendered as its own tile with the SAME words and seed.
  5. RE-MEASURE the composite, not the tile. Tiling is not a universal fix: the canopic shrine tile did
     not animate its lamps any better than the full frame did, yet the composite still looked right to
     Lucas. Judge the thing that ships.

Tiles are cheap — 77-108 s against ~470 s for a panorama, because the latent is far smaller — so repair
is affordable per subject. What is NOT affordable is re-rendering the whole frame hoping for luck.

  cine_stage.py --spec spec.json --source scene.png --out out.mp4 [--no-repair] [--dry-run]
"""
import argparse
import json
import os
import time

from PIL import Image

import cine_render as CR
import motion_spec as MS


def render_state(cg, src_png, spec, out_mp4, prefix="ltx25PIPE/pipe", seed=CR.SEED):
    """One full-frame render of a state at the settled recipe. Returns the fetched clip path."""
    img = Image.open(src_png).convert("RGB")
    if img.size != (CR.FULL_W, CR.FULL_H):
        img = img.resize((CR.FULL_W, CR.FULL_H), Image.LANCZOS)
    name = CR.upload(cg, img, "pipe_%s_%s.png" % (spec.get("room", "room"), spec.get("state", "base")))
    g = CR.graph(name, MS.render_prompt(spec), MS.render_negative(spec),
                 CR.FULL_W, CR.FULL_H, CR.LENGTH, prefix, seed=seed)
    pid = cg.submit(g)
    r = CR.wait(cg, pid)
    if r is not True:
        raise RuntimeError("OOM" if r is False else "TIMEOUT — check /history for %s" % pid)
    cg.fetch_remote_clip(pid, out_mp4)
    return out_mp4


def repair_subject(cg, src_png, spec, subject, work_dir, seed=CR.SEED):
    """Render ONE dead subject as its own tile. The tile is only a RENDERING CONTEXT — it exists so the
    object stops competing with the rest of the frame — so it is cropped generously around the subject,
    while the paste is confined to the subject's own bounds by the caller."""
    img = Image.open(src_png).convert("RGB")
    if img.size != (CR.FULL_W, CR.FULL_H):
        img = img.resize((CR.FULL_W, CR.FULL_H), Image.LANCZOS)
    tb = CR.tile_bounds(subject["box"], CR.FULL_W, CR.FULL_H)
    crop = img.crop(tb)
    name = CR.upload(cg, crop, "tile_%s_%s.png" % (spec.get("room", "room"), subject["name"]))
    # The tile's prompt names ONLY this subject: that is the whole mechanism. Its phrase is looked up
    # from the spec so the words are identical to the full-frame attempt — the variable being changed
    # is the framing, not the language.
    phrase = next((s["phrase"] for s in spec["subjects"] if s["name"] == subject["name"]), subject["name"])
    tile_spec = {"subjects": [{"name": subject["name"], "box": [0, 0, 1, 1], "phrase": phrase}],
                 "rigid": spec.get("rigid"), "negatives": spec.get("negatives"),
                 "has_document": spec.get("has_document")}
    tw, th = crop.size
    tw -= tw % 32
    th -= th % 32
    out = os.path.join(work_dir, "tile_%s.mp4" % subject["name"])
    g = CR.graph(name, MS.render_prompt(tile_spec), MS.render_negative(tile_spec),
                 tw, th, CR.LENGTH, "ltx25PIPE/tile", seed=seed)
    pid = cg.submit(g)
    r = CR.wait(cg, pid, budget_s=1800)
    if r is not True:
        raise RuntimeError("tile %s: %s" % (subject["name"], "OOM" if r is False else "TIMEOUT"))
    cg.fetch_remote_clip(pid, out)
    return out, tb


def run(spec, src_png, out_mp4, repair=True, dry_run=False, reuse=False, log=print):
    errs = MS.validate(spec)
    if errs:
        raise SystemExit("spec errors:\n  " + "\n  ".join(errs))
    work = os.path.dirname(os.path.abspath(out_mp4)) or "."
    os.makedirs(work, exist_ok=True)

    if dry_run:
        return {"positive": MS.render_prompt(spec), "negative": MS.render_negative(spec),
                "subjects": [s["name"] for s in spec["subjects"]],
                "tiles": {s["name"]: CR.tile_bounds(s["box"], CR.FULL_W, CR.FULL_H)
                          for s in spec["subjects"] if not s.get("still")}}

    cg = CR._cg()
    t0 = time.time()
    # `reuse` skips the ~470 s full-frame render when the clip is already on disk — a resume after an
    # interrupted run, and the way the repair path is exercised without paying for the base again.
    if reuse and os.path.isfile(out_mp4):
        log("reusing existing clip %s" % out_mp4)
    else:
        log("render %s/%s …" % (spec.get("room"), spec.get("state")))
        render_state(cg, src_png, spec, out_mp4)
    g = CR.gate(out_mp4, src_png)
    log("  gate: corr %.3f  drift %d px  jump %.2f  %s"
        % (g["frame0_corr"], g["landmark_drift_px"], g["loop_jump"], "OK" if g["ok"] else "NOISE"))
    if not g["ok"]:
        return {"gate": g, "status": "noise", "secs": round(time.time() - t0)}

    measured = MS.measure_subjects(out_mp4, spec)
    for m in measured:
        log("  %-22s p95 %6.2f  %s" % (m["name"], m["p95"], m["verdict"]))
    dead = MS.repair_list(measured)
    result = {"gate": g, "subjects": measured, "repaired": [], "status": "ok"}

    for v in MS.still_violations(measured):
        # Temporal variation cannot tell motion from illumination; the landmark test is the arbiter.
        log("  ? %s declared still but varies (p95 %.2f); landmark drift is %d px"
            % (v["name"], v["p95"], g["landmark_drift_px"]))

    if dead and repair:
        cur = out_mp4
        for d in dead:
            log("  repair tile: %s" % d["name"])
            try:
                tile, tb = repair_subject(cg, src_png, spec, d, work)
            except Exception as e:                       # one bad tile must not lose the base clip
                log("    FAILED (%s) — keeping the unrepaired clip" % str(e)[:120])
                continue
            x0, y0, x1, y1 = d["box"]
            region = (x0 * CR.FULL_W, y0 * CR.FULL_H, x1 * CR.FULL_W, y1 * CR.FULL_H)
            nxt = os.path.join(work, "%s_rep_%s.mp4" % (os.path.splitext(os.path.basename(out_mp4))[0],
                                                        d["name"]))
            CR.composite_tile(cur, tile, tb, nxt, region_px=region)
            cur = nxt
            result["repaired"].append(d["name"])
        if cur != out_mp4:
            # Re-measure the COMPOSITE, never the tile — that is what ships.
            after = MS.measure_subjects(cur, spec)
            for m in after:
                if m["name"] in result["repaired"]:
                    log("  after repair: %-16s p95 %6.2f  %s" % (m["name"], m["p95"], m["verdict"]))
            result["final"] = cur
            result["subjects_after"] = after
    result["secs"] = round(time.time() - t0)
    return result


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-repair", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reuse", action="store_true", help="skip the full-frame render if --out exists")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    r = run(spec, a.source, a.out, repair=not a.no_repair, dry_run=a.dry_run, reuse=a.reuse)
    print(json.dumps(r, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
