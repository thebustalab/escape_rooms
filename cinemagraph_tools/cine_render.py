#!/usr/bin/env python3
"""cine_render.py — the settled cinemagraph recipe as reusable primitives, plus the gates that transfer.

Factored out of the one-off stage scripts (`sweep_night.py`, `sweep_night_variants.py`) so the pipeline
has ONE definition of the recipe rather than a fourth copy. Those scripts stay as the experiment record.

THE RECIPE (notes/cinemagraph_handoff.md §1, validated across 18 clips — 6 daytime, 12 night — all
passed by Lucas): ltx-2.5-22b-distilled, 8 steps, cfg 2, 3072x1024, 73 frames, 24 fps, end-guide 0.70,
no mask. Two LTXVAddGuide nodes on the room's own panorama: frame 0 at strength 1.0, frame -1 at 0.70.
The end guide is simultaneously the loop closer, the drift suppressor and the motion limiter.

ONLY FOUR GATES TRANSFER, and this module implements exactly those:
  * `frame0_corr`     — the BINARY gate. /history reporting `success` only means the graph ran; two
                        clips of pure noise were once filed as successes. Nothing is trusted below 0.7.
  * `loop_jump`       — the ABSOLUTE jump at the junction. Report it absolute, never normalised: dividing
                        by the mean adjacent-frame step made a 28% BETTER loop read as worse, because
                        pinning also halves ordinary motion.
  * `landmark_drift`  — did the architecture actually move. Phase-correlates high-contrast STATIC
                        landmarks INCLUDING at the frame edges, because a slow zoom barely moves the
                        centre. This replaces `incoherence`, which does not transfer: dark low-texture
                        water gives it nothing to lock onto and boat scored 6.34 against 0.00-0.17 for
                        every daytime room while being provably rock solid at 0 px.
  * per-subject liveness — `motion_spec.measure_subjects`, not implemented here.

DELIBERATELY NOT GATED: colour drift and incoherence. Their thresholds are DAYTIME calibrations. Lucas
passed pharos at colour 27.4 and emporion at 17.3 where the daytime rooms all sit at 0.9-1.5 — in a dark
room lit by flames the global mean legitimately swings, and gating on it would auto-reject nearly every
good night clip.
"""
import json
import os
import subprocess
import tempfile
import time
import urllib.request

import numpy as np
from PIL import Image

COMFY = os.environ.get("CINEMAGRAPH_COMFY_HOST", "http://127.0.0.1:8289")
DIST = "ltx-2.5-22b-distilled-transformer-nvfp4.safetensors"
SEED, FPS, CFG, END_GUIDE, STEPS = 4242, 24.0, 2.0, 0.70, 8
FULL_W, FULL_H, LENGTH = 3072, 1024, 73
CORR_GATE = 0.70

# Latent volume, not clip length, is what fails: 229 M pixel-frames clean, 305 M colour drift, 380 M
# black, 531 M noise. A tile is far smaller than a panorama, which is why tiles cost 77-108 s against
# ~470 s and can be rendered freely.
MAX_PIXEL_FRAMES = 250_000_000


def _cg():
    """The generator module, imported by path (it lives in ~/ComfyUI, outside this tree)."""
    import importlib.util
    import sys
    sys.path.insert(0, os.path.expanduser("~/ComfyUI"))
    os.environ["CINEMAGRAPH_COMFY_HOST"] = COMFY
    spec = importlib.util.spec_from_file_location("cg", os.path.expanduser("~/ComfyUI/cinemagraph_gen.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def upload(cg, img, name):
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    body, ctype = cg._multipart({"overwrite": "true", "type": "input"},
                                {"image": (name, buf.getvalue(), "image/png")})
    r = urllib.request.urlopen(urllib.request.Request(
        cg.HOST + "/upload/image", data=body, headers={"Content-Type": ctype}), timeout=300)
    j = json.load(r)
    n = j.get("name") or name
    return os.path.join(j["subfolder"], n) if j.get("subfolder") else n


CINEMAGRAPH_LORA = "LTX-2.3-22b-LoRA-Cinemagraph/ltx-2.3-22b-lora-cinemagraph-0.9.safetensors"


def graph(image_name, positive, negative, w, h, length, prefix, end_guide=END_GUIDE, seed=SEED,
          cond_fps=None, lora=None):
    """The settled two-ended-guide graph. Frame 0 pinned hard, frame -1 at `end_guide`.

    `cond_fps` DECOUPLES THE PACE FROM THE CONTAINER. `LTXVConditioning.frame_rate` is a conditioning
    value telling the model what playback rate the frames it generates are meant for; `CreateVideo.fps`
    is only the container's declared rate. This graph passed the same FPS to both, which tied them
    together and left pace unadjustable.

    Set `cond_fps` ABOVE FPS to slow the motion down: at cond_fps 48 the model lays out 48 frames'
    worth of movement per second of intent, and playing those frames back at FPS=24 stretches it over
    twice the time. The motion is GENERATED slower, not retimed — which matters, because retiming is
    already a recorded dead end ("they look 'slowed', not natural"; frame duplication is not new
    motion). Lowering it has the opposite effect and is also already recorded: frame_rate 16 was
    tried and Lucas preferred 24, i.e. more motion per frame read as worse. Upward was never tested.

    Defaults to FPS, so every existing caller renders exactly as before.
    """
    cond_fps = FPS if cond_fps is None else cond_fps
    # `lora` = strength_model for the Lightricks cinemagraph LoRA, inserted between the UNET and the
    # guider. It is a 2.3 adapter on a 2.5 base; Lightricks say most 2.3 LoRAs run on 2.5 unchanged but
    # to validate. Its trigger word is CINEMAGRAPH_MOTION and the CALLER must supply it in `positive` —
    # a LoRA fired without its trigger typically does nothing, which is the most likely explanation for
    # the undocumented 2.5-era "no difference" verdict.
    model_src = ["1", 0] if lora is None else ["40", 0]
    return {"prompt": {
        "1":  {"class_type": "UNETLoader", "inputs": {"unet_name": DIST, "weight_dtype": "default"}},
        "2":  {"class_type": "CLIPLoader",
               "inputs": {"clip_name": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                          "type": "ltxv"}},
        "17": {"class_type": "VAELoader", "inputs": {"vae_name": "ltx-2.5-video-vae-conv-bf16.safetensors"}},
        "4":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": positive}},
        "5":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": negative}},
        "6":  {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "30": {"class_type": "EmptyLTXVLatentVideo",
               "inputs": {"width": w, "height": h, "length": length, "batch_size": 1}},
        "31": {"class_type": "LTXVAddGuide",
               "inputs": {"positive": ["4", 0], "negative": ["5", 0], "vae": ["17", 0],
                          "latent": ["30", 0], "image": ["6", 0], "frame_idx": 0, "strength": 1.0}},
        "32": {"class_type": "LTXVAddGuide",
               "inputs": {"positive": ["31", 0], "negative": ["31", 1], "vae": ["17", 0],
                          "latent": ["31", 2], "image": ["6", 0], "frame_idx": -1, "strength": end_guide}},
        "8":  {"class_type": "LTXVConditioning",
               "inputs": {"positive": ["32", 0], "negative": ["32", 1], "frame_rate": cond_fps}},
        "9":  {"class_type": "LTXVScheduler",
               "inputs": {"steps": STEPS, "max_shift": 2.05, "base_shift": 0.95,
                          "stretch": True, "terminal": 0.1, "latent": ["32", 2]}},
        "10": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "11": {"class_type": "CFGGuider",
               "inputs": {"model": model_src, "positive": ["8", 0], "negative": ["8", 1], "cfg": CFG}},
        "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "13": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["10", 0], "guider": ["11", 0], "sampler": ["12", 0],
                          "sigmas": ["9", 0], "latent_image": ["32", 2]}},
        "35": {"class_type": "LTXVCropGuides",
               "inputs": {"positive": ["8", 0], "negative": ["8", 1], "latent": ["13", 0]}},
        "14": {"class_type": "VAEDecodeTiled",
               "inputs": {"samples": ["35", 2], "vae": ["17", 0], "tile_size": 512,
                          "overlap": 64, "temporal_size": 256, "temporal_overlap": 8}},
        "15": {"class_type": "CreateVideo", "inputs": {"images": ["14", 0], "fps": FPS}},
        **({} if lora is None else {"40": {"class_type": "LoraLoaderModelOnly",
               "inputs": {"model": ["1", 0], "lora_name": CINEMAGRAPH_LORA,
                          "strength_model": float(lora)}}}),
        "16": {"class_type": "SaveVideo",
               "inputs": {"video": ["15", 0], "filename_prefix": prefix,
                          "format": "auto", "codec": "auto"}},
    }}


def wait(cg, pid, budget_s=7200):
    """cg.poll() gives up at 900 s and a full panorama exceeds it, which is how a whole stage once
    filed slow renders as TIMEOUTs. True = clean, False = OOM, None = genuinely still not done."""
    t0 = time.time()
    while time.time() - t0 < budget_s:
        time.sleep(15)
        try:
            h = json.load(urllib.request.urlopen(f"{cg.HOST}/history/{pid}", timeout=30))
            if pid in h:
                err = cg._history_error(h[pid])
                if err is None:
                    return True
                if cg._is_oom(err):
                    return False
                raise RuntimeError("ComfyUI failed the render — " + err[:400])
        except RuntimeError:
            raise
        except Exception:
            pass
    return None


# ------------------------------------------------------------------ gates

def sample(mp4, n=16):
    d = tempfile.mkdtemp(prefix="cr_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, f"{d}/%04d.png"], check=True)
        fs = sorted(os.listdir(d))
        idx = np.linspace(0, len(fs) - 1, min(n, len(fs))).astype(int)
        return np.stack([np.asarray(Image.open(os.path.join(d, fs[i])).convert("RGB"), dtype=np.float32)
                         for i in idx])
    finally:
        subprocess.run(["rm", "-rf", d], check=False)


def frame0_corr(mp4, src_png):
    """THE binary gate: correlate frame 0 against the source still, or trust nothing."""
    st = sample(mp4, n=1)
    f0 = st[0].mean(axis=2)
    src = np.asarray(Image.open(src_png).convert("L").resize((f0.shape[1], f0.shape[0])), dtype=np.float32)
    return float(np.corrcoef(src.ravel(), f0.ravel())[0, 1])


def _shift(ref, img):
    F = np.fft.rfft2(ref) * np.conj(np.fft.rfft2(img))
    F /= np.maximum(np.abs(F), 1e-8)
    c = np.fft.irfft2(F, s=ref.shape)
    dy, dx = np.unravel_index(np.argmax(c), c.shape)
    if dy > ref.shape[0] // 2:
        dy -= ref.shape[0]
    if dx > ref.shape[1] // 2:
        dx -= ref.shape[1]
    return dy, dx


def landmark_drift(mp4, boxes=None, frames=None):
    """Max pixel shift of static landmarks across the clip. **Includes the frame EDGES**, because a
    slow zoom barely moves the centre — checking only central landmarks would miss it. Every one of the
    18 validated clips returns 0. Unlike incoherence this does not care how dark or textureless the
    scene is: it locks onto whatever contrast the landmark box contains."""
    st = sample(mp4, n=9) if frames is None else frames
    g = [f.mean(axis=2) for f in st]
    H, W = g[0].shape
    if boxes is None:                       # default: both frame edges, full height
        boxes = [(int(W * 0.02), 0, int(W * 0.20), H), (int(W * 0.80), 0, int(W * 0.98), H)]
    mx = 0
    for x0, y0, x1, y1 in boxes:
        crops = [f[y0:y1, x0:x1] for f in g]
        for c in crops[1:]:
            dy, dx = _shift(crops[0], c)
            mx = max(mx, abs(dy), abs(dx))
    return int(mx)


def loop_jump(mp4):
    """Absolute difference across the loop junction, in grey levels. Validated clips run 1.4-4.0."""
    d = tempfile.mkdtemp(prefix="lj_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "scale=iw/4:ih/4",
                        f"{d}/%04d.png"], check=True)
        fs = sorted(os.listdir(d))
        a = [np.asarray(Image.open(os.path.join(d, f)).convert("L"), dtype=np.float32) for f in fs]
        return float(np.abs(a[-1] - a[0]).mean())
    finally:
        subprocess.run(["rm", "-rf", d], check=False)


def gate(mp4, src_png):
    """The four transferable checks. `ok` is the binary noise gate only — the rest are reported for a
    human, because metrics screen a clip OUT and cannot certify one as good."""
    corr = frame0_corr(mp4, src_png)
    return {"frame0_corr": round(corr, 3), "ok": corr > CORR_GATE,
            "landmark_drift_px": landmark_drift(mp4),
            "loop_jump": round(loop_jump(mp4), 2)}


# ------------------------------------------------------------------ tile repair

def tile_bounds(box, W, H, margin=0.25, multiple=32):
    """Pixel crop for a repair tile: the subject's box plus margin, snapped to `multiple`.

    THE TILE MUST CONTAIN THE WHOLE OBJECT. A partially-cropped object composites as half-moving,
    half-static — `paste_tile.py` warns when the moving region touches the tile border, which is that
    signature. The margin also gives the model context, which is the point of tiling at all: rendered
    alone the object becomes the dominant subject instead of competing with the rest of the frame."""
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) * W, (y1 - y0) * H
    cx, cy = (x0 + x1) / 2 * W, (y0 + y1) / 2 * H
    tw = min(W, max(multiple * 4, int(round(w * (1 + 2 * margin)))))
    th = min(H, max(multiple * 4, int(round(h * (1 + 2 * margin)))))
    tw -= tw % multiple
    th -= th % multiple
    px0 = int(min(max(0, cx - tw / 2), W - tw))
    py0 = int(min(max(0, cy - th / 2), H - th))
    return px0, py0, px0 + tw, py0 + th


def composite_tile(base_mp4, tile_mp4, tile_box_px, out_mp4, region_px=None, fps=FPS):
    """Paste a repair tile back into the full-frame clip via paste_tile.py.

    `region_px` is the SUBJECT's own bounds. Passing it matters: the tile rectangle is NOT the paste
    region. A first attempt in the earlier work pasted everything that moved, which included the arch
    and entablature the tile had re-rendered slightly differently, and the architecture appeared to
    shift between frames."""
    here = os.path.dirname(os.path.abspath(__file__))
    cmd = ["python3", os.path.join(here, "paste_tile.py"), base_mp4, tile_mp4,
           "--box", ",".join(str(int(v)) for v in tile_box_px), "--out", out_mp4, "--fps", str(fps)]
    if region_px:
        cmd += ["--region", ",".join(str(int(v)) for v in region_px)]
    subprocess.run(cmd, check=True)
    return out_mp4
