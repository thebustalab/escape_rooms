#!/usr/bin/env python3
"""
generate_scene.py — authoring-time scene-art generator for the escape rooms.

Runs on Lucas's machine ONLY (never in a student's browser). Reads the OpenAI
key from the OPENAI_API_KEY environment variable — the key is never hard-coded,
never committed, and never shipped to the client. The generated PNGs are static
public art that get served with the rest of the site.

Usage:
  python3 generate_scene.py check
      List the image-capable models available on this account.

  python3 generate_scene.py gen --prompt-file scene.txt --out ../demo_hub/scene/station.png \
      [--size 1536x1024] [--quality medium] [--model gpt-image-2]
      Generate one image and save it.

Because this needs the key, invoke it through a login shell so ~/.bashrc is
sourced, e.g.:
  bash -lic 'python3 .../generate_scene.py check'
"""
import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error

API = "https://api.openai.com/v1"


def _key():
    k = os.environ.get("OPENAI_API_KEY")
    if not k:
        sys.exit("OPENAI_API_KEY not set in this environment.")
    return k


def _post(path, payload):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + _key(),
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        # Surface the API's actual error body — a bare "400 Bad Request" hides the reason
        # (invalid size / model / moderation / etc.). Read the body and re-raise with it.
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            body = "<no response body>"
        raise RuntimeError(f"OpenAI {path} -> HTTP {e.code} {e.reason}: {body}") from None


def cmd_check(_):
    req = urllib.request.Request(API + "/models",
                                 headers={"Authorization": "Bearer " + _key()})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    imgs = sorted(m["id"] for m in data["data"] if "image" in m["id"])
    print("Image-capable models:")
    for i in imgs:
        print("  ", i)
    if not imgs:
        print("  (none — check account access)")


def cmd_gen(a):
    prompt = open(a.prompt_file, encoding="utf-8").read().strip() if a.prompt_file else a.prompt
    if not prompt:
        sys.exit("No prompt (use --prompt-file or --prompt).")
    refs = [p for p in (getattr(a, "ref", None) or []) if p]
    if refs:                       # Phase 2 world-plate: condition the scene on reference image(s)
        return _gen_with_refs(a, prompt, refs)
    payload = {"model": a.model, "prompt": prompt, "size": a.size,
               "quality": a.quality, "n": 1}
    print(f"Generating with {a.model} ({a.size}, quality={a.quality})…", flush=True)
    resp = _post("/images/generations", payload)
    b64 = resp["data"][0]["b64_json"]
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # Write the returned bytes VERBATIM (no PIL round-trip) so gpt-image-2's embedded C2PA "AI-generated"
    # provenance metadata is preserved on the base scene. Keep base scenes on this byte-write path; a PIL
    # re-encode would silently strip the manifest. (The pixel-editing paths — dooropen/seamfix/variant —
    # necessarily invalidate any signature, so provenance lives on the base scene, which is correct.)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64))
    usage = resp.get("usage")
    print("Saved:", out)
    if usage:
        print("Usage:", json.dumps(usage))


def _gen_with_refs(a, prompt, refs):
    # Phase 2 world-plate reference: generate a NEW scene CONDITIONED on one or more reference
    # images by posting to /images/edits (the only image endpoint that accepts input images).
    # No mask → the whole frame is generated fresh, guided by the reference(s) for backdrop/style
    # continuity while the prompt drives this room's composition. input_fidelity defaults to the
    # API default ("low") so the plate guides the WORLD, not the exact pixels — send "high" only
    # to hew closely to the reference. Up to 16 refs (OpenAI cap); repeated "image" form field.
    import requests
    if len(refs) > 16:
        sys.exit(f"too many reference images ({len(refs)}); OpenAI allows at most 16.")
    missing = [p for p in refs if not os.path.exists(p)]
    if missing:
        sys.exit("reference image(s) not found: " + ", ".join(missing))
    fhs = [open(p, "rb") for p in refs]
    try:
        files = [("image", (os.path.basename(p), fh, "image/png")) for p, fh in zip(refs, fhs)]
        data = {"model": a.model, "prompt": prompt, "size": a.size, "quality": a.quality}
        if getattr(a, "input_fidelity", None):
            data["input_fidelity"] = a.input_fidelity
        print(f"Generating with {a.model} ({a.size}, quality={a.quality}) "
              f"referencing {len(refs)} plate(s)"
              f"{', input_fidelity=' + a.input_fidelity if data.get('input_fidelity') else ''}…",
              flush=True)
        r = requests.post(API + "/images/edits",
                          headers={"Authorization": "Bearer " + _key()},
                          files=files, data=data, timeout=300)
    finally:
        for fh in fhs:
            fh.close()
    if r.status_code != 200:
        sys.exit(f"gen (ref) failed {r.status_code}: {r.text[:400]}")
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print("Saved:", out)


def cmd_genset(a):
    # Manifest: JSON array of {"prompt": "...", "out": "path.png"}.
    # Resumable + fault-tolerant: skips files that already exist, and a failure on
    # one item is logged and skipped rather than aborting the whole batch.
    items = json.load(open(a.manifest, encoding="utf-8"))
    failed = []
    for i, it in enumerate(items, 1):
        out = os.path.abspath(it["out"])
        if os.path.exists(out) and not a.force:
            print(f"[{i}/{len(items)}] exists, skipping {it['out']}", flush=True)
            continue
        print(f"[{i}/{len(items)}] generating {it['out']} …", flush=True)
        try:
            resp = _post("/images/generations",
                         {"model": a.model, "prompt": it["prompt"],
                          "size": a.size, "quality": a.quality, "n": 1})
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f:
                f.write(base64.b64decode(resp["data"][0]["b64_json"]))
            print("     saved", out, flush=True)
        except Exception as e:  # noqa: BLE001 — keep the batch going
            print(f"     FAILED {it['out']}: {type(e).__name__} {e}", flush=True)
            failed.append(it["out"])
    if failed:
        print("Failed items (re-run to retry):", ", ".join(failed), flush=True)


def cmd_slice(a):
    # Cut an image into N vertical facings (N = number of --names), centred on the
    # N equal segments. --overlap widens each facing by that many px so adjacent
    # facings share content (cohesion — you see a bit of the next view). --crop-height
    # first trims the image to a centred band (shorter -> less portrait -> fills a
    # wide screen better with `cover`).
    from PIL import Image
    names = [s.strip() for s in a.names.split(",")]
    im = Image.open(a.input)
    w, h = im.size
    if a.crop_height and a.crop_height < h:
        top = (h - a.crop_height) // 2
        im = im.crop((0, top, w, top + a.crop_height))
        w, h = im.size
    n = len(names)
    step = w / n
    half = (step + a.overlap) / 2.0
    for i, name in enumerate(names):
        c = (i + 0.5) * step
        x0 = max(0, int(round(c - half)))
        x1 = min(w, int(round(c + half)))
        out = os.path.abspath(name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im.crop((x0, 0, x1, h)).save(out)
        print("sliced", out, f"({x1 - x0}x{h})", flush=True)


def cmd_edit(a):
    # images.edit: send an input image + prompt, save the returned image.
    import requests
    with open(a.input, "rb") as f:
        r = requests.post(
            API + "/images/edits",
            headers={"Authorization": "Bearer " + _key()},
            files={"image": (os.path.basename(a.input), f, "image/png")},
            data={"model": a.model, "prompt": a.prompt, "size": a.size},
            timeout=300,
        )
    if r.status_code != 200:
        sys.exit(f"edit failed {r.status_code}: {r.text[:400]}")
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print("edited ->", out, flush=True)


def cmd_dooropen(a):
    # Masked edit: open the door inside a box, keeping every other pixel identical.
    # Mask = opaque everywhere, TRANSPARENT inside the box (OpenAI edits the transparent
    # region). We then composite the returned image back over the original through a
    # feathered box so nothing outside the door can drift between closed/open variants.
    import io
    import requests
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.open(a.input).convert("RGB")
    w, h = im.size
    bx = [float(x) for x in a.box.split(",")]
    x0, y0, x1, y1 = int(bx[0]*w), int(bx[1]*h), int(bx[2]*w), int(bx[3]*h)
    mask = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    ImageDraw.Draw(mask).rectangle([x0, y0, x1, y1], fill=(0, 0, 0, 0))
    mb = io.BytesIO(); mask.save(mb, "PNG"); mb.seek(0)
    ib = io.BytesIO(); im.save(ib, "PNG"); ib.seek(0)
    r = requests.post(
        API + "/images/edits",
        headers={"Authorization": "Bearer " + _key()},
        files={"image": ("s.png", ib, "image/png"), "mask": ("m.png", mb, "image/png")},
        data={"model": a.model, "prompt": a.prompt, "size": f"{w}x{h}", "quality": a.quality},
        timeout=300,
    )
    if r.status_code != 200:
        sys.exit(f"dooropen failed {r.status_code}: {r.text[:400]}")
    res = Image.open(io.BytesIO(base64.b64decode(r.json()["data"][0]["b64_json"]))).convert("RGB")
    if res.size != (w, h):
        res = res.resize((w, h))
    alpha = Image.new("L", (w, h), 0)
    ImageDraw.Draw(alpha).rectangle([x0, y0, x1, y1], fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(max(4, (x1 - x0) // 20)))
    comp = Image.composite(res, im, alpha)
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    comp.save(out)
    print("dooropen ->", out, flush=True)


def _roll_h(im, dx):
    # Horizontally roll a panorama by dx px (wrapping). Used by seamfix to bring the L/R wrap seam to
    # the centre and back. Invertible: _roll_h(_roll_h(im, dx), w-dx) == im.
    from PIL import Image
    w, h = im.size
    dx %= w
    if dx == 0:
        return im.copy()
    out = Image.new(im.mode, (w, h))
    out.paste(im.crop((w - dx, 0, w, h)), (0, 0))
    out.paste(im.crop((0, 0, w - dx, h)), (dx, 0))
    return out


def cmd_seamfix(a):
    # Seam-safe 360 wrap: an equirectangular panorama's left and right edges must meet, but generated
    # panos rarely wrap cleanly. Roll the image by half its width so the seam sits at the CENTRE, masked-
    # edit a vertical strip there so the scene reads continuous across the join, feather-composite it back
    # (only the strip changes), then roll back — leaving the L/R edges seamless. Reuses the door-open
    # mask+edit+feather mechanic on a centre strip instead of a door box.
    import io
    import requests
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.open(a.input).convert("RGB")
    w, h = im.size
    # Roll so the seam to fix lands at the CENTRE (where the model has context on both sides). --pos is the
    # seam's location as a fraction of width: 1.0 = the L/R wrap edge (the default, dx = w/2); ~0.5 = the
    # middle. The middle case is the second stage of a two-stage repair — --full at the wrap fixes it but
    # pushes a new seam to the far meridian (~0.5), which a composite pass at --pos then stitches.
    dx = int(round(w * (0.5 - a.pos))) % w
    rolled = _roll_h(im, dx)
    # Strip bounds straddle the seam (now at the centre, w//2). --left/--right give the extent on EACH
    # side of the seam as a fraction of width, independently — so the regenerated band need not be
    # symmetric and can be narrowed to dodge features you want to keep. Absent (or ≤0), fall back to a
    # symmetric split of --width. The two-handled band in the wrap tester drives these.
    lf = a.left if a.left and a.left > 0 else a.width / 2
    rf = a.right if a.right and a.right > 0 else a.width / 2
    lpx, rpx = max(4, int(w * lf)), max(4, int(w * rf))
    x0, x1 = w // 2 - lpx, w // 2 + rpx
    strip = x1 - x0                                # total px width of the editable band
    mask = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    ImageDraw.Draw(mask).rectangle([x0, 0, x1, h], fill=(0, 0, 0, 0))   # transparent = editable strip
    mb = io.BytesIO(); mask.save(mb, "PNG"); mb.seek(0)
    ib = io.BytesIO(); rolled.save(ib, "PNG"); ib.seek(0)
    if a.occluder:
        prompt = (f"Standing exactly in the centre of this view, {a.occluder}. It runs the full height of "
                  "the frame and visually separates the left and right halves, so they do not need to "
                  "match. Keep the existing scene, style, lighting, and palette on both sides completely "
                  "unchanged; no people, no lettering, no text.")
    else:
        prompt = a.prompt or ("Seamlessly blend the vertical band through the centre so the scene is continuous "
                              "left-to-right with no visible seam, join, or repetition; keep identical style, "
                              "lighting, and content on both sides; no people, no lettering, no text.")
    # CROP-INPAINT. Sending the WHOLE pano makes the model re-render everything, so a composite keeps a
    # strip cut from a different render — the mismatch Lucas hit. Sending only a crop AROUND the seam
    # confines the model's drift to that crop; every column outside it stays pixel-identical original art.
    crop_frac = a.crop if a.crop and a.crop > 0 else (0.34 if a.occluder else 0.0)
    if crop_frac > 0:
        cw = max(strip + 64, int(w * min(0.9, crop_frac)))
        cw -= cw % 16                                   # the API wants each edge a multiple of 16
        cx0 = max(0, w // 2 - cw // 2)
        cx1 = min(w, cx0 + cw)
        sub = rolled.crop((cx0, 0, cx1, h))
        sub_mask = mask.crop((cx0, 0, cx1, h))
        sb = io.BytesIO(); sub.save(sb, "PNG"); sb.seek(0)
        smb = io.BytesIO(); sub_mask.save(smb, "PNG"); smb.seek(0)
        rc = requests.post(
            API + "/images/edits",
            headers={"Authorization": "Bearer " + _key()},
            files={"image": ("s.png", sb, "image/png"), "mask": ("m.png", smb, "image/png")},
            data={"model": a.model, "prompt": prompt, "size": f"{cx1 - cx0}x{h}", "quality": a.quality},
            timeout=300,
        )
        if rc.status_code != 200:
            sys.exit(f"seamfix (crop) failed {rc.status_code}: {rc.text[:400]}")
        patch = Image.open(io.BytesIO(base64.b64decode(rc.json()["data"][0]["b64_json"]))).convert("RGB")
        if patch.size != (cx1 - cx0, h):
            patch = patch.resize((cx1 - cx0, h))
        res = rolled.copy()
        res.paste(patch, (cx0, 0))                      # only the crop is model output; the rest is untouched
        _finish_seamfix(a, res, rolled, w, h, x0, x1, strip, dx)
        return
    r = requests.post(
        API + "/images/edits",
        headers={"Authorization": "Bearer " + _key()},
        files={"image": ("s.png", ib, "image/png"), "mask": ("m.png", mb, "image/png")},
        data={"model": a.model, "prompt": prompt, "size": f"{w}x{h}", "quality": a.quality},
        timeout=300,
    )
    if r.status_code != 200:
        sys.exit(f"seamfix failed {r.status_code}: {r.text[:400]}")
    res = Image.open(io.BytesIO(base64.b64decode(r.json()["data"][0]["b64_json"]))).convert("RGB")
    if res.size != (w, h):
        res = res.resize((w, h))
    _finish_seamfix(a, res, rolled, w, h, x0, x1, strip, dx)


def _finish_seamfix(a, res, rolled, w, h, x0, x1, strip, dx):
    """Composite (or not) the model's output back over the rolled original, then roll back and save.
    Shared by the whole-image path and the crop-inpaint path."""
    from PIL import Image, ImageDraw, ImageFilter
    if a.full:
        # Full-output mode: keep the model's ENTIRE returned image, no composite. The strip and its
        # surroundings then come from ONE generation, so they're self-consistent — no cross-fade of two
        # near-identical layers, hence no ghosting (the failure mode of the composite path on continuous
        # sky/canopy). Trade-off: the whole scene is the model's re-render (slight drift from the committed
        # art), so use it PRE-COMMIT. gpt-image-2 has no input_fidelity knob (it 400s), so this is the lever.
        out_im = _roll_h(res, w - dx)
    else:
        # Composite mode: paste only the regenerated strip back over the original, feathered at its edges.
        # --feather is a fraction of width: <0 (or unset) -> AUTO (strip/8); 0 -> OFF (hard edge); >0 -> px.
        alpha = Image.new("L", (w, h), 0)
        ImageDraw.Draw(alpha).rectangle([x0, 0, x1, h], fill=255)
        if a.feather is None or a.feather < 0:
            fr = max(4, strip // 8)
        else:
            fr = int(w * a.feather)
        if fr > 0:
            alpha = alpha.filter(ImageFilter.GaussianBlur(fr))   # fr == 0 leaves a crisp rectangle (hard edge)
        comp = Image.composite(res, rolled, alpha)
        out_im = _roll_h(comp, w - dx)             # undo the roll → seam back at the L/R edges, now blended
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    out_im.save(out)
    print("seamfix ->", out, flush=True)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(required=True)
    c = sub.add_parser("check"); c.set_defaults(fn=cmd_check)
    g = sub.add_parser("gen"); g.set_defaults(fn=cmd_gen)
    g.add_argument("--prompt-file")
    g.add_argument("--prompt")
    g.add_argument("--out", required=True)
    g.add_argument("--size", default="1536x1024")
    g.add_argument("--quality", default="medium")
    g.add_argument("--model", default="gpt-image-2")
    g.add_argument("--ref", action="append", default=[],
                   help="world-plate reference image (repeatable, up to 16); routes gen through "
                        "/images/edits for cross-room backdrop continuity")
    g.add_argument("--input-fidelity", dest="input_fidelity", choices=["low", "high"], default=None,
                   help="how closely to preserve the reference(s) (default: API default 'low')")
    s = sub.add_parser("genset"); s.set_defaults(fn=cmd_genset)
    s.add_argument("--manifest", required=True)
    s.add_argument("--size", default="1536x1024")
    s.add_argument("--quality", default="medium")
    s.add_argument("--model", default="gpt-image-2")
    s.add_argument("--force", action="store_true", help="regenerate even if the file exists")
    sl = sub.add_parser("slice"); sl.set_defaults(fn=cmd_slice)
    sl.add_argument("--input", required=True)
    sl.add_argument("--names", required=True, help="comma-separated output paths, left to right")
    sl.add_argument("--overlap", type=int, default=0, help="px each facing overlaps its neighbours")
    sl.add_argument("--crop-height", dest="crop_height", type=int, default=0, help="centred height-crop before slicing")
    e = sub.add_parser("edit"); e.set_defaults(fn=cmd_edit)
    e.add_argument("--input", required=True)
    e.add_argument("--prompt", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--size", default="1536x1024")
    e.add_argument("--model", default="gpt-image-2")
    do = sub.add_parser("dooropen"); do.set_defaults(fn=cmd_dooropen)
    do.add_argument("--input", required=True)
    do.add_argument("--box", required=True, help="x0,y0,x1,y1 as 0-1 fractions")
    do.add_argument("--prompt", required=True)
    do.add_argument("--out", required=True)
    do.add_argument("--quality", default="medium")
    do.add_argument("--model", default="gpt-image-2")
    sf = sub.add_parser("seamfix"); sf.set_defaults(fn=cmd_seamfix)
    sf.add_argument("--input", required=True)
    sf.add_argument("--out", required=True)
    sf.add_argument("--width", type=float, default=0.12, help="centre strip width as a fraction of image width (symmetric fallback)")
    sf.add_argument("--left", type=float, default=0.0, help="strip extent LEFT of the seam as a fraction of width (overrides --width/2 when >0)")
    sf.add_argument("--right", type=float, default=0.0, help="strip extent RIGHT of the seam as a fraction of width (overrides --width/2 when >0)")
    sf.add_argument("--feather", type=float, default=-1.0, help="composite feather radius as a fraction of width; <0 = auto (strip/8), 0 = OFF (hard edge), >0 = explicit")
    sf.add_argument("--full", action="store_true", help="use the model's whole returned image (no composite) — self-consistent seam, no ghosting; re-renders the scene, so use pre-commit")
    sf.add_argument("--pos", type=float, default=1.0, help="seam location as a fraction of width (1.0 = L/R wrap edge; ~0.5 = middle) — where to centre the fix")
    sf.add_argument("--crop", type=float, default=0.0, help="CROP-INPAINT: send only this fraction of width around the seam to the model instead of the whole pano (0 = off/legacy). Keeps the rest of the art pixel-identical — no AI-image-of-an-AI-image outside the band.")
    sf.add_argument("--occluder", default="", help="OCCLUDER mode: what to stand ON the seam (e.g. 'a plain stone pillar, floor to ceiling'). The two sides then never have to agree. Implies a crop-inpaint.")
    sf.add_argument("--prompt", default="")
    sf.add_argument("--quality", default="medium")
    sf.add_argument("--model", default="gpt-image-2")
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
