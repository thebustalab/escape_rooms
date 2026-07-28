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
    payload = {"model": a.model, "prompt": prompt, "size": a.size,
               "quality": a.quality, "n": 1}
    print(f"Generating with {a.model} ({a.size}, quality={a.quality})…", flush=True)
    resp = _post("/images/generations", payload)
    b64 = resp["data"][0]["b64_json"]
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64))
    usage = resp.get("usage")
    print("Saved:", out)
    if usage:
        print("Usage:", json.dumps(usage))


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
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
