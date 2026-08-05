#!/usr/bin/env python3
"""localizer.py — find the pixel box for each spec element in a generated scene (art-pipeline Phase 2).

After a room's art is generated from its scene spec, the spec knows WHAT should animate and roughly WHERE
(each element's `at` phrase) but not the exact pixel box a cinemagraph needs. This asks a vision model to
locate each object and — per Lucas's refinement — feeds it THREE things plus an explanation of how they
relate, so it can use the prompt's spatial ordering to disambiguate:

  1. the generated equirectangular IMAGE,
  2. the exact PROMPT the image was generated from (it names the objects left-to-right around the 360),
  3. the LIST of objects to find (id + description + the spatial `at` phrase from the spec).

Returns {id: {"box":[x0,y0,x1,y1] fractions, "confidence":0..1}}. Boxes are clamped + ordered. Pure stdlib
+ PIL; reuses the OPENAI_API_KEY env var + api.openai.com like generate_scene.py (no SDK, nothing shipped
to a client). The image is downscaled before upload (localization needs layout, not full resolution — keeps
vision cost + latency down). CLI has a --truth mode that scores predictions against a room's real hotspot
boxes (IoU + centre distance) so we can check accuracy before trusting it in the pipeline.
"""
import argparse, base64, io, json, os, subprocess, sys, urllib.request, urllib.error

API = "https://api.openai.com/v1/chat/completions"

# Grounding DINO (default engine) runs as a subprocess under a torch venv so the harness's conda-base python
# never imports torch. See grounding_dino_detect.py.
_HERE = os.path.dirname(os.path.abspath(__file__))
GDINO_SCRIPT = os.path.join(_HERE, "grounding_dino_detect.py")
GDINO_VENV = os.path.expanduser("~/ComfyUI/.venv/bin/python")
GDINO_MODEL = "IDEA-Research/grounding-dino-tiny"

SYSTEM = (
    "You are a precise object localizer for equirectangular 360° panorama images. You return only strict "
    "JSON. The image has a faint COORDINATE GRID burned onto it: labelled lines every 0.1 on both axes "
    "(the 0.5 lines are red, others blue, labels in yellow). READ each box's coordinates OFF THIS GRID. "
    "Coordinates are FRACTIONS: x from 0.0 (far-left edge) to 1.0 (far-right edge), y from 0.0 (top) to 1.0 "
    "(bottom). A box is [x0,y0,x1,y1] with x0<x1 and y0<y1, drawn tightly around the object's actual pixels."
)

# The explicit explanation of how the three inputs relate — this is the part Lucas asked for.
RELATIONSHIP = (
    "You are given three things that describe ONE scene:\n"
    "  (A) the IMAGE — an equirectangular 360° panorama with a coordinate grid drawn on it.\n"
    "  (B) the PROMPT that was used to GENERATE that image. It walks the objects in LEFT-TO-RIGHT order, so "
    "it tells you their horizontal ORDER — but only roughly where they are.\n"
    "  (C) a LIST of objects to locate, each with an id, a description, and a spatial phrase.\n"
    "Use (B) and the spatial phrase ONLY to decide which object is which and roughly which side to look; "
    "then find the object in the IMAGE and MEASURE its box off the grid. CRITICAL: the objects are NOT "
    "evenly spaced — do not spread them out uniformly, and do not make every box the same size. Real objects "
    "cluster; some are wide, some narrow. Measure each one from the pixels where you actually see it. If "
    "several similar objects exist (e.g. two boilers), the prompt's left-to-right order says which is which. "
    "For EACH object first state briefly what you SEE at that location and the grid lines it sits between, "
    "THEN give the box. If an object is genuinely not visible, set box to null and confidence 0.0 (do not "
    "invent a position)."
)


def _draw_grid(im):
    """Burn a faint coordinate ruler onto the image: labelled lines at every 0.1 fraction on both axes.
    Vision LLMs read positions far better off an explicit ruler than from raw pixels. Kept subtle so it
    doesn't swamp the scene."""
    from PIL import ImageDraw
    im = im.copy()
    d = ImageDraw.Draw(im)
    W, H = im.size
    for i in range(1, 10):
        f = i / 10.0
        x, y = int(f * W), int(f * H)
        major = (i % 5 == 0)   # 0.5 line heavier
        col = (255, 80, 80) if major else (120, 200, 255)
        d.line([(x, 0), (x, H)], fill=col, width=2 if major else 1)
        d.line([(0, y), (W, y)], fill=col, width=2 if major else 1)
        d.text((x + 2, 2), f"{f:.1f}", fill=(255, 255, 0))
        d.text((2, y + 2), f"{f:.1f}", fill=(255, 255, 0))
    return im


def _downscale_data_url(path, max_w=1536, grid=True):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    W, H = im.size
    if W > max_w:
        im = im.resize((max_w, max(1, round(H * max_w / W))))
    if grid:
        im = _draw_grid(im)
    buf = io.BytesIO(); im.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "data:image/png;base64," + b64, (W, H)


def _targets_text(targets):
    lines = []
    for t in targets:
        at = (" · position: " + t["at"]) if t.get("at") else ""
        lines.append(f'  - id "{t["id"]}": {t.get("desc", t["id"])}{at}')
    return "\n".join(lines)


def build_messages(prompt, targets, data_url):
    user_text = (
        RELATIONSHIP
        + "\n\n(B) PROMPT:\n" + (prompt or "(none provided)")
        + "\n\n(C) OBJECTS TO LOCATE:\n" + _targets_text(targets)
        + "\n\nReturn strict JSON of the form: "
          '{"boxes":[{"id":"<id>","seen":"<what you see there + the grid lines it sits between>",'
          '"box":[x0,y0,x1,y1],"confidence":0.0-1.0}, ...]} '
          "— one entry per object in the list, ids exactly as given; box may be null if not visible."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]},
    ]


def _clamp_box(b):
    try:
        x0, y0, x1, y1 = (float(v) for v in b)
    except Exception:  # noqa: BLE001
        return None
    x0, x1 = sorted((max(0.0, min(1.0, x0)), max(0.0, min(1.0, x1))))
    y0, y1 = sorted((max(0.0, min(1.0, y0)), max(0.0, min(1.0, y1))))
    if x1 - x0 < 1e-3 or y1 - y0 < 1e-3:
        return None
    return [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]


def _post_chat(payload, api_key):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(API, data=data, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + api_key})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")[:400]
        raise RuntimeError(f"OpenAI HTTP {e.code}: {body}") from None


def _localize_gdino(image_path, targets, model=GDINO_MODEL):
    """Grounding DINO engine (default): a real open-vocabulary detector. One query per object (its `desc`,
    falling back to id), top-scoring box. Returns {id: {"box":[...], "confidence":score}}."""
    payload = [{"id": t["id"], "query": (t.get("desc") or t["id"])} for t in targets if t.get("id")]
    p = subprocess.run([GDINO_VENV, GDINO_SCRIPT, "--image", image_path,
                        "--targets", json.dumps(payload), "--model", model],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("grounding_dino_detect failed: " + (p.stderr or p.stdout).strip()[-400:])
    boxes = json.loads(p.stdout).get("boxes", {})
    out = {}
    for tid, d in boxes.items():
        b = _clamp_box(d.get("box"))
        if b:
            out[tid] = {"box": b, "confidence": float(d.get("score", 0) or 0)}
    return out


def localize(image_path, targets, prompt, model=None, engine="gdino", max_w=1536, api_key=None):
    """Locate each target object. engine='gdino' (Grounding DINO, default, local) or 'gpt4o' (vision LLM
    fallback — imprecise, kept for comparison). Returns {id: {"box":[...], "confidence":float}}."""
    if engine == "gdino":
        return _localize_gdino(image_path, targets, model=model or GDINO_MODEL)
    return _localize_gpt4o(image_path, targets, prompt, model=model or "gpt-4o", max_w=max_w, api_key=api_key)


def _localize_gpt4o(image_path, targets, prompt, model="gpt-4o", max_w=1536, api_key=None):
    """Locate each target object in the image. Returns {id: {"box":[...], "confidence":float}}."""
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in this environment")
    data_url, _orig = _downscale_data_url(image_path, max_w)
    payload = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
               "messages": build_messages(prompt, targets, data_url)}
    resp = _post_chat(payload, api_key)
    content = resp["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    out = {}
    for row in parsed.get("boxes", []):
        box = _clamp_box(row.get("box"))
        if box and row.get("id"):
            out[str(row["id"])] = {"box": box, "confidence": float(row.get("confidence", 0) or 0)}
    return out


# --- accuracy check ---------------------------------------------------------------------------------------

def _iou(a, b):
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _centre_dist(a, b):
    ax, ay = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    bx, by = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def _targets_from_spec(spec):
    return [{"id": e["id"], "desc": e.get("desc", e["id"]), "at": e.get("at")}
            for e in spec.get("elements", [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True, help="committed scene.png")
    ap.add_argument("--spec", required=True, help="scene spec JSON (targets + prompt source)")
    ap.add_argument("--truth", help="scenario.json to score against (real hotspot boxes)")
    ap.add_argument("--room", help="room key in --truth")
    ap.add_argument("--engine", default="gdino", choices=["gdino", "gpt4o"])
    ap.add_argument("--model", default=None, help="override the engine's default model")
    ap.add_argument("--max-w", type=int, default=1536)
    a = ap.parse_args()

    spec = json.load(open(a.spec, encoding="utf-8"))
    targets = _targets_from_spec(spec)
    # prefer the spec's own rendered prompt for the relationship; fall back to a stored one
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import scene_spec
        prompt = scene_spec.render_prompt(spec)
    except Exception:  # noqa: BLE001
        prompt = spec.get("prompt", "")

    print(f"localizing {len(targets)} objects in {os.path.basename(a.scene)} via {a.engine}…", file=sys.stderr)
    pred = localize(a.scene, targets, prompt, engine=a.engine, model=a.model, max_w=a.max_w)

    truth = {}
    if a.truth and a.room:
        doc = json.load(open(a.truth, encoding="utf-8"))
        node = next((r for r in doc.get("rooms", []) if r.get("key") == a.room), None)
        for h in (node or {}).get("hotspots", []):
            if isinstance(h.get("box"), list) and len(h["box"]) == 4:
                truth[h["id"]] = h["box"]

    print(f"\n{'id':26} {'pred box':38} conf   " + ("IoU   dCentre  truth box" if truth else ""))
    ious = []
    for t in targets:
        tid = t["id"]; p = pred.get(tid)
        pb = p["box"] if p else None
        row = f"{tid:26} {str(pb):38} {p['confidence'] if p else 0:.2f}   "
        if truth and tid in truth and pb:
            iou = _iou(pb, truth[tid]); dc = _centre_dist(pb, truth[tid]); ious.append(iou)
            row += f"{iou:.2f}   {dc:.3f}    {truth[tid]}"
        elif truth and tid in truth:
            row += f" --     --      {truth[tid]}"
        print(row)
    if ious:
        print(f"\nmean IoU {sum(ious)/len(ious):.2f} over {len(ious)} scored · "
              f"mean centre-dist {sum(_centre_dist(pred[t['id']]['box'], truth[t['id']]) for t in targets if t['id'] in pred and t['id'] in truth)/len(ious):.3f}")
        print("(IoU>0.5 = tight; for ambient cinemagraphs even a roughly-centred box that contains the object is usable.)")


if __name__ == "__main__":
    main()
