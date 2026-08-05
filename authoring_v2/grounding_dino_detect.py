#!/usr/bin/env python3
"""grounding_dino_detect.py — open-vocabulary object localization for the art pipeline.

Runs under a torch+transformers venv (e.g. ~/ComfyUI/.venv); called as a SUBPROCESS by localizer.py so the
harness's conda-base python never has to import torch. Grounding DINO has a real box-regression head trained
on localization — the right tool for "find the box for this named object", where a vision LLM only guesses.

Input  (--targets, JSON): [{"id":"boiler","query":"a riveted boiler"}, ...]
Output (stdout, JSON): {"boxes":{"boiler":{"box":[x0,y0,x1,y1],"score":0.63}, ...}}  (box = fractions of W,H)
One Grounding-DINO query per object (top-scoring box), so id->box mapping is unambiguous. N is small (~a
dozen objects/room), and inference is fast on the GV100; the model loads once per invocation.
"""
import argparse, json, sys
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--targets", required=True, help="JSON list of {id, query}")
    ap.add_argument("--model", default="IDEA-Research/grounding-dino-tiny")
    ap.add_argument("--box-threshold", type=float, default=0.15)
    ap.add_argument("--text-threshold", type=float, default=0.15)
    a = ap.parse_args()

    targets = json.loads(a.targets)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = AutoProcessor.from_pretrained(a.model)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(a.model).to(device).eval()

    img = Image.open(a.image).convert("RGB")
    W, H = img.size
    out = {}
    for t in targets:
        q = (t.get("query") or t["id"]).strip().lower()
        if not q.endswith("."):
            q += "."
        inputs = proc(images=img, text=q, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        # transformers has renamed the threshold kwarg across versions — try both.
        try:
            res = proc.post_process_grounded_object_detection(
                outputs, inputs.input_ids, threshold=a.box_threshold,
                text_threshold=a.text_threshold, target_sizes=[(H, W)])[0]
        except TypeError:
            res = proc.post_process_grounded_object_detection(
                outputs, inputs.input_ids, box_threshold=a.box_threshold,
                text_threshold=a.text_threshold, target_sizes=[(H, W)])[0]
        boxes, scores = res["boxes"], res["scores"]
        if len(scores) == 0:
            continue
        i = int(torch.argmax(scores))
        x0, y0, x1, y1 = (float(v) for v in boxes[i].tolist())
        out[t["id"]] = {"box": [round(max(0.0, x0 / W), 4), round(max(0.0, y0 / H), 4),
                                round(min(1.0, x1 / W), 4), round(min(1.0, y1 / H), 4)],
                        "score": round(float(scores[i]), 4)}
    print(json.dumps({"boxes": out}))


if __name__ == "__main__":
    main()
