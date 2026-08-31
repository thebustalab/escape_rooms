#!/usr/bin/env python3
"""Stage NIGHT-2 — cinemagraphs for the scenario's NIGHT-VARIANT panoramas.

Found 2026-08-31, after Lucas spotted that the "night deck" clip was the daytime image.

THE FINDING, which is bigger than the one wrong file. Egypt is not a daytime scenario with three
night rooms bolted on: SEVEN of its rooms carry a full-scene night variant that swaps in when the
library is solved — deck, quay, emporion, market_price, market_boast, canopic and library. Each
declares it on an `ambient` carrier hotspot (id `night_wash`) as
`variants[0].panorama = <room>/scene_night.png`, gated `when: {solved: "library"}`. All seven PNGs
exist on disk. So the scenario visibly goes dark for its whole second half, and every daytime clip
confirmed in the earlier work has an unrendered night twin.

`scenario.json`'s room-level `panorama` field points at the DAY art, which is correct — that is the
room's base state — and that is exactly why the first night pass rendered deck in daylight: it read
the base panorama and never looked at the variant carrier. **A room's cinemagraph set is per STATE,
not per room.** Any pipeline that walks `room.panorama` will silently miss every variant.

Prompts are written per state by LOOKING at that state's panorama — a night variant is a different
photograph with different light sources, so its day prompt does not transfer.

Run:  sweep_night_variants.py deck            (one or more room keys)
Only rooms with a prompt defined below can be run; the rest need someone to open the art first.
"""
import os, sys, json, time, urllib.request, subprocess, tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/bustalab/ComfyUI")
os.environ["CINEMAGRAPH_COMFY_HOST"] = "http://127.0.0.1:8289"
import importlib.util
spec = importlib.util.spec_from_file_location("cg", "/home/bustalab/ComfyUI/cinemagraph_gen.py")
cg = importlib.util.module_from_spec(spec); spec.loader.exec_module(cg)

ROOT = "/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms"
EGY = f"{ROOT}/rooms/wrangling/egypt"
OUT = "/home/bustalab/Documents/Tools/temp/egypt_night"
os.makedirs(OUT, exist_ok=True)

SEED, FPS, CFG, END, STEPS = 4242, 24.0, 2.0, 0.70, 8
TW, TH, LENGTH = 3072, 1024, 73
DIST = "ltx-2.5-22b-distilled-transformer-nvfp4.safetensors"

BASE_NEG = ("camera movement, pan, tilt, zoom, parallax, dolly, tracking shot, whole image moving, "
            "background sliding, warping, morphing, people, crowd, cars, vehicles, new objects "
            "appearing, explosion, distorted, blurry, low quality, jittery, hard seam")
# Learned from the deck DAY render, which Lucas and I both saw: the manifest grew a large curling
# corner and its writing visibly crawled. Written documents must be pinned, not animated.
NEG_PAPER = BASE_NEG + (", paper curling, parchment lifting, page turning, writing changing, "
                        "text moving, letters shifting, document deforming")


def wrap(p):
    return ("locked-off static camera bolted to a tripod, the frame never moves: " + p +
            ". Continuous gentle ambient motion throughout the whole scene. The buildings, walls, "
            "stonework, ground and horizon are rigid and fixed — they do not warp, drift, breathe "
            "or change shape. Only water, cloth, flame, smoke and haze move. NOTHING TRAVELS ACROSS "
            "THE FRAME: every movement is a small cyclic motion that returns to where it began. "
            "Seamless natural loop.")


# One entry per night-variant room. Add a room here only after opening its scene_night.png.
# (room key) -> (source png, positive prompt, negative)
VARIANTS = {
 "deck": (
   f"{EGY}/deck/scene_night.png",
   # Looked at 2026-08-31: moon low on the left laying a silver path, the Pharos lit gold with its
   # own reflection, the city's lamps along the far shore, mast + furled sail + rigging centre, the
   # open hatch glowing warm at right, wet deck boards catching the light. The desk manifest is
   # present but is deliberately NOT named — it is the thing that broke the daytime render.
   "the dark harbour water rippling and breathing across the bay, the long gold reflection of the "
   "lighthouse fire shivering and reforming on the water, the pale moon-path trembling on the "
   "surface, the crown-fire at the top of the lighthouse flickering and guttering, the lamps along "
   "the far shore trembling faintly, the flame of the lamp down in the open deck hatch wavering and "
   "throwing moving warm light on the timbers, the rigging lines and halyards hanging from the mast "
   "swaying slightly, the loose ends of the furled sail stirring in the night air, the straw packed "
   "around the amphorae trembling. The parchment on the writing-desk lies completely flat and still",
   NEG_PAPER),

 "quay": (
   f"{EGY}/quay/scene_night.png",
   # Full moon upper left with a silver path on the water, the Pharos centre laying a gold road,
   # moored ships left with furled sails and lamps, a skiff with a lamp centre-right, a lit portico
   # far right, wet quay stone reflecting everything.
   "the dark harbour water rippling and breathing across the whole bay, the gold road of lighthouse "
   "fire and the pale moon-path shivering and reforming on the surface, the crown-fire at the top of "
   "the lighthouse flickering and guttering, the moored fishing boats and the wine ship rocking "
   "gently at their lines with masts and rigging swaying, the small pennants strung between their "
   "masts fluttering in place, the lamps aboard the ships and in the skiff wavering, the lamps under "
   "the far portico and along the distant shore trembling",
   BASE_NEG),

 "emporion": (
   f"{EGY}/emporion/scene_night.png",
   # The long striped awning over the colonnade — the element that needed a repair tile in daylight,
   # so watch it here — plus hanging oil lamps down the colonnade, slack ropes at the right end, the
   # stone water trough, and the harbour with the far Pharos at the left.
   "the great striped awning over the emporion billowing and rippling slowly on the night breeze, "
   "its slack hanging ropes swaying, the row of hanging oil lamps along the colonnade flickering and "
   "throwing moving warm light over the stacked jars, the water in the stone trough trembling and "
   "catching the lamplight, the harbour water rippling away to the left, the distant lighthouse fire "
   "flickering with its reflection shivering on the water, the lamps of the lit street beyond the "
   "archway trembling",
   BASE_NEG),

 "market_price": (
   f"{EGY}/market_price/scene_night.png",
   # Broad sagging awning, hanging lanterns, bolts of dyed cloth on a line at the right, dried herb
   # bunches, brass balance pans, the lit city behind. An open ledger sits on the stall — pinned.
   "the broad awning above the stall sagging and breathing on the night breeze, the draped cloth "
   "along the stall front stirring, the hanging bolts of dyed cloth swaying gently on their line, "
   "the bunches of dried herbs trembling beside them, the hanging lantern flames wavering and "
   "throwing moving light across the stall, the brass balance pans rocking very slightly on their "
   "chains, the lamps along the walls flickering, the lamplit city and harbour water shimmering "
   "beyond the stall. The open ledger and the loose papers on the stall lie completely flat and still",
   NEG_PAPER),

 "market_boast": (
   f"{EGY}/market_boast/scene_night.png",
   # A bronze cauldron over glowing coals at the right with smoke rising, the heavy canopy overhead,
   # draped stall cloths, small oil-bowl flames on the stall, the colonnade street right, sea left.
   "smoke rising and curling slowly from the bronze cauldron over its coals, the coals glowing and "
   "pulsing red, the heavy canopy overhead sagging and breathing, the cloths draped over the stall "
   "front stirring, the small oil-lamp flames along the stall wavering and throwing moving light "
   "over the stacked jars, the lamps down the colonnade trembling, the dark sea breathing beyond the "
   "parapet at the left. The open page on the stall lies completely flat and still",
   NEG_PAPER),

 "canopic": (
   f"{EGY}/canopic/scene_night.png",
   # A lion-head spout pouring into a round basin — falling water loops perfectly — plus a lit shrine
   # with candles at the right (the flames that needed a repair tile in daylight) and a temple portico.
   "the lion-head spout pouring a steady unbroken fall of water into the fountain basin, the basin "
   "surface rippling and turning, water trembling as it spills over the rim and runs down the stone, "
   "the candle and lamp flames at the little shrine flickering and throwing moving light over the "
   "statue in its niche, the lamps along the colonnade and up the temple steps wavering, the lamps of "
   "the city below the archway trembling faintly",
   BASE_NEG),

 "library": (
   f"{EGY}/library/scene_night.png",
   # The hardest of the set and the twin of its own daytime version, which needed a repair tile for
   # the light shaft. A moonlight beam through a high window at the right, many small lamp flames, a
   # draped cloth off the reading table. The open codex and scrolls are pinned.
   "the oil-lamp flames on their tall stands flickering and guttering, the warm lamplight breathing "
   "over the stone floor and the ranked scroll shelves, the shaft of pale moonlight slanting down "
   "from the high window with dust motes turning slowly within it, the light breathing gently in and "
   "out of intensity, the pale cloth draped over the edge of the reading table stirring very "
   "slightly. The open book on the lectern, the scrolls and the sheets on the table lie completely "
   "flat and still",
   NEG_PAPER),
}


def upload_named(img, name):
    import io
    buf = io.BytesIO(); img.save(buf, format="PNG")
    body, ctype = cg._multipart({"overwrite": "true", "type": "input"},
                                {"image": (name, buf.getvalue(), "image/png")})
    r = urllib.request.urlopen(urllib.request.Request(
        cg.HOST + "/upload/image", data=body, headers={"Content-Type": ctype}), timeout=300)
    j = json.load(r)
    n = j.get("name") or name
    return os.path.join(j["subfolder"], n) if j.get("subfolder") else n


def build(neg, pos, image_name):
    return {"prompt": {
      "1":  {"class_type": "UNETLoader", "inputs": {"unet_name": DIST, "weight_dtype": "default"}},
      "2":  {"class_type": "CLIPLoader",
             "inputs": {"clip_name": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                        "type": "ltxv"}},
      "17": {"class_type": "VAELoader",
             "inputs": {"vae_name": "ltx-2.5-video-vae-conv-bf16.safetensors"}},
      "4":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": wrap(pos)}},
      "5":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": neg}},
      "6":  {"class_type": "LoadImage", "inputs": {"image": image_name}},
      "30": {"class_type": "EmptyLTXVLatentVideo",
             "inputs": {"width": TW, "height": TH, "length": LENGTH, "batch_size": 1}},
      "31": {"class_type": "LTXVAddGuide",
             "inputs": {"positive": ["4", 0], "negative": ["5", 0], "vae": ["17", 0],
                        "latent": ["30", 0], "image": ["6", 0], "frame_idx": 0, "strength": 1.0}},
      "32": {"class_type": "LTXVAddGuide",
             "inputs": {"positive": ["31", 0], "negative": ["31", 1], "vae": ["17", 0],
                        "latent": ["31", 2], "image": ["6", 0], "frame_idx": -1, "strength": END}},
      "8":  {"class_type": "LTXVConditioning",
             "inputs": {"positive": ["32", 0], "negative": ["32", 1], "frame_rate": FPS}},
      "9":  {"class_type": "LTXVScheduler",
             "inputs": {"steps": STEPS, "max_shift": 2.05, "base_shift": 0.95,
                        "stretch": True, "terminal": 0.1, "latent": ["32", 2]}},
      "10": {"class_type": "RandomNoise", "inputs": {"noise_seed": SEED}},
      "11": {"class_type": "CFGGuider",
             "inputs": {"model": ["1", 0], "positive": ["8", 0], "negative": ["8", 1], "cfg": CFG}},
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
      "16": {"class_type": "SaveVideo",
             "inputs": {"video": ["15", 0], "filename_prefix": "ltx25NIGHTVAR/nv",
                        "format": "auto", "codec": "auto"}},
    }}


def wait_long(pid, budget_s=7200):
    t0 = time.time()
    while time.time() - t0 < budget_s:
        time.sleep(15)
        try:
            h = json.load(urllib.request.urlopen(f"{cg.HOST}/history/{pid}", timeout=30))
            if pid in h:
                err = cg._history_error(h[pid])
                if err is None: return True
                if cg._is_oom(err): return False
                raise RuntimeError("ComfyUI failed the render — " + err[:400])
        except RuntimeError: raise
        except Exception: pass
    return None


def frame0_corr(mp4, src_png):
    d = tempfile.mkdtemp(prefix="nv0_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vframes", "1", f"{d}/f0.png"],
                       check=True)
        f0 = np.asarray(Image.open(f"{d}/f0.png").convert("L"), dtype=np.float32)
        src = np.asarray(Image.open(src_png).convert("L").resize(f0.shape[::-1]), dtype=np.float32)
        return float(np.corrcoef(src.ravel(), f0.ravel())[0, 1])
    finally:
        subprocess.run(["rm", "-rf", d], check=False)


rooms = sys.argv[1:] or ["deck"]
unknown = [r for r in rooms if r not in VARIANTS]
if unknown:
    sys.exit(f"no prompt defined for {unknown} — open that room's scene_night.png and add one")

print(f"backend {cg.HOST}   night-variant renders: {', '.join(rooms)}\n", flush=True)
res = []
for room in rooms:
    src, pos, neg = VARIANTS[room]
    t0 = time.time()
    try:
        img = Image.open(src).convert("RGB")
        if img.size != (TW, TH):
            img = img.resize((TW, TH), Image.LANCZOS)
        name = upload_named(img, f"sceneNV_{room}_night.png")
        pid = cg.submit(build(neg, pos, name))
        print(f"{room:<10} submitted {pid}", flush=True)
        r = wait_long(pid)
        if r is not True:
            print(f"{room:<10} {'OOM' if r is False else 'TIMEOUT (check /history)'}", flush=True)
            res.append(dict(room=room, status="OOM" if r is False else "TIMEOUT")); continue
        dst = f"{OUT}/{room}_night.mp4"
        cg.fetch_remote_clip(pid, dst)
        corr = frame0_corr(dst, src)
        print(f"{room:<10} {time.time()-t0:5.0f}s  frame0 corr {corr:.3f}"
              f"{'' if corr > 0.7 else '   <-- NOISE, DO NOT TRUST'}", flush=True)
        res.append(dict(room=room, status="ok" if corr > 0.7 else "NOISE", path=dst, corr=corr))
    except Exception as e:
        print(f"{room:<10} FAIL {type(e).__name__}: {str(e)[:200]}", flush=True)
        res.append(dict(room=room, status="FAIL", error=f"{type(e).__name__}: {str(e)[:200]}"))
    json.dump(res, open(f"{OUT}/variant_status.json", "w"), indent=1)
print(f"\nDONE -> {OUT}", flush=True)
