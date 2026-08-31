#!/usr/bin/env python3
"""Stage NIGHT — the settled recipe on the five NIGHT / PRE-DAWN Egypt rooms.

Lucas, 2026-08-30: "do the night ones to see if any new surprises jump out before we build the
pipeline... after generation run all the metrics then I'll have a look."

Everything in the daytime work was tuned on bright scenes containing harbour water. These five are
genuinely different material and are the first real test of whether the recipe AND the thresholds
transfer. Recipe is unchanged from stage AM (section 1 of notes/cinemagraph_handoff.md):
ltx-2.5-22b-distilled, 8 steps, cfg 2, 3072x1024, 73 frames, 24 fps, end-guide 0.70, BASE_NEG,
no mask, seed 4242. Only the prompt differs per room.

The five, and what I saw when I opened each panorama:

  boat     open black water on every side, the Pharos ahead in full fire laying a broken gold road
           over the sea, a bow lamp close at the prow, the city's lamps astern, surf at the
           sea-steps. Lots of natural oscillation, but nearly all of it is DARK.
  pharos   the hard case of this batch, and the twin of the daytime library: a stone gallery,
           rigid on almost every pixel. The motion that matters is the hot gold light bleeding
           round the sealed bronze door and thrown in bars across the flagstones. If that stays
           dead the room is dead.
  lantern  the opposite extreme: a cart-sized fire dead centre in a polished bronze mirror-shell.
           Expect very high motion, and expect the fire to WIN THE FRAME — the fuel-store smoke on
           the far right is the likely casualty (competition for the frame, handoff section 6).
  deck     first light, not night: pale rose sky, glassy harbour, mast and rigging, furled sail.
           Closest of the five to the daytime rooms.
  hold     the darkest: a lamplit interior below the waterline. The hanging bronze lamp is a true
           pendulum, which is the ideal two-ended-loop subject, and the light shaft down the
           ladder is the same structure as the library shaft that needed a repair tile.

TWO THINGS DELIBERATELY GUARDED IN THE PROMPTS, both of which would be scene-breaking rather than
merely ugly:
  * pharos — the bronze door MUST STAY SHUT. There is a separate authored state variant
    (var_lantern_door_open.png) for the open state; a cinemagraph that swings it open would show
    the player the wrong world state.
  * lantern — the geared turning-dial MUST NOT ROTATE. It is a control the player throws, so a
    clip that turns it on its own tells the player the puzzle is already solved.
Both are negated in the prompt and in the negative.

Names: filename_prefix "ltx25NIGHT/night" and uploads "sceneNIGHT_<room>.png" — deliberately NOT
shared with any earlier stage. Sharing either silently mixes results between stages (README trap).

Archive to z_sweeps/ at close-out, like the other stage scripts.
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
# Two scene-breaking motions, negated per room (see the docstring).
NEG_DOOR = BASE_NEG + ", door opening, door swinging open, gate opening, door ajar"
NEG_GEAR = BASE_NEG + ", gears turning, cogs rotating, wheels turning, machinery running, rotating"


def wrap(p):
    """The stabiliser, unchanged from stage AM. The last sentence is THE demonstrated prompt rule:
    a two-ended loop forbids net travel, because both ends are pinned to the same still."""
    return ("locked-off static camera bolted to a tripod, the frame never moves: " + p +
            ". Continuous gentle ambient motion throughout the whole scene. The buildings, walls, "
            "stonework, ground and horizon are rigid and fixed — they do not warp, drift, breathe "
            "or change shape. Only water, cloth, flame, smoke and haze move. NOTHING TRAVELS ACROSS "
            "THE FRAME: every movement is a small cyclic motion that returns to where it began. "
            "Seamless natural loop.")


# Written by looking at each panorama, not from the art prompt. Oscillatory phenomena only:
# nothing here has a net path, because a two-ended loop cannot give one back.
ROOMS = {
 "boat": (
   "the black harbour water rippling and breathing across the whole bay, the long broken road of "
   "gold firelight laid over the water shivering and reforming, the great crown-fire at the top of "
   "the lighthouse flickering and guttering, the flame in the skiff's bow lamp wavering in its "
   "glass, the lamps along the distant harbour wall trembling, the moored wine ship rocking gently "
   "at her lines, small waves lapping and breaking pale against the sea-steps"),
 "pharos": (
   "the hot gold light bleeding out around every edge of the sealed bronze door pulsing and "
   "breathing as the great fire beyond it works, the hard bars of that light thrown across the "
   "flagstones brightening and dimming with it, the small lamp flame at the head of the spiral "
   "stair wavering, the black sea far below breaking white against the bare rocks at the island's "
   "foot, the open water rippling out to the horizon, the distant city lamps trembling faintly "
   "across the harbour. The heavy bronze door itself stays shut and completely still"),
 "lantern": (
   "the great fire roaring and surging in its iron basket, flames leaping and falling back on "
   "themselves, the gathered light raking and pulsing across the polished bronze mirror-shell "
   "behind it, warm amber firelight breathing over the stone piers and the wet flagstones, smoke "
   "curling and dragging slowly off the stacked logs at the fuel store, the hot glow trembling in "
   "the seaward arch. The bronze gear ring and its handle stay completely still and do not turn"),
 "deck": (
   "the flat pale harbour water rippling very gently and breathing across the bay, the rigging "
   "lines and halyards hanging from the mast swaying slightly, the loose ends of the furled sail "
   "lashed along the yard stirring in the dawn air, the straw packed around the amphorae "
   "trembling, the edges of the unrolled manifest lifting and settling on the desk, the brass "
   "balance pans rocking very slightly on their chains, the flame of the lamp down in the open "
   "hatch wavering, the far crown-fire of the lighthouse flickering across the water"),
 "hold": (
   "the bronze oil lamp hanging on its chain swinging very slightly to and fro above the gangway, "
   "its small flame guttering and flaring, the warm lamplight breathing across the stacked clay "
   "jars and the straw, the pale shaft of dawn light falling down the ladder-stair with dust and "
   "straw-chaff turning slowly within it, the coils of rope hanging beside the ladder swaying "
   "gently, loose straw stirring between the jars"),
}
NEG_FOR = {"pharos": NEG_DOOR, "lantern": NEG_GEAR}


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
      "1":  {"class_type": "UNETLoader",
             "inputs": {"unet_name": DIST, "weight_dtype": "default"}},
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
             "inputs": {"video": ["15", 0], "filename_prefix": "ltx25NIGHT/night",
                        "format": "auto", "codec": "auto"}},
    }}


def wait_long(pid, budget_s=7200):
    """cg.poll() gives up at 900 s and a full panorama can exceed it, which is how stage T filed
    slow renders as TIMEOUTs. Same status semantics, bigger budget."""
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
    """THE binary gate. /history reporting `success` only means the graph ran — two clips of pure
    noise were filed as successes. Correlate frame 0 against the source still or trust nothing."""
    d = tempfile.mkdtemp(prefix="n0_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vframes", "1",
                        f"{d}/f0.png"], check=True)
        f0 = np.asarray(Image.open(f"{d}/f0.png").convert("L"), dtype=np.float32)
        src = np.asarray(Image.open(src_png).convert("L").resize(f0.shape[::-1]), dtype=np.float32)
        return float(np.corrcoef(src.ravel(), f0.ravel())[0, 1])
    finally:
        subprocess.run(["rm", "-rf", d], check=False)


print(f"backend {cg.HOST}", flush=True)
print(f"recipe: distilled / {STEPS} steps / cfg {CFG} / {TW}x{TH} / {LENGTH}f / end-guide {END} / "
      f"seed {SEED}\n", flush=True)

res = []
for room, pos in ROOMS.items():
    t0 = time.time()
    src = f"{EGY}/{room}/scene.png"
    try:
        img = Image.open(src).convert("RGB")
        if img.size != (TW, TH):
            img = img.resize((TW, TH), Image.LANCZOS)
        name = upload_named(img, f"sceneNIGHT_{room}.png")
        g = build(NEG_FOR.get(room, BASE_NEG), pos, name)
        pid = cg.submit(g)
        print(f"{room:<10} submitted {pid}", flush=True)
        r = wait_long(pid)
        if r is not True:
            print(f"{room:<10} {'OOM' if r is False else 'TIMEOUT (check /history)'}", flush=True)
            res.append(dict(room=room, status="OOM" if r is False else "TIMEOUT")); continue
        dst = f"{OUT}/{room}.mp4"
        cg.fetch_remote_clip(pid, dst)
        corr = frame0_corr(dst, src)
        ok = corr > 0.7
        print(f"{room:<10} {time.time()-t0:5.0f}s  frame0 corr {corr:.3f}"
              f"{'' if ok else '   <-- NOISE, DO NOT TRUST'}", flush=True)
        res.append(dict(room=room, status="ok" if ok else "NOISE", path=dst,
                        corr=corr, secs=round(time.time()-t0)))
    except Exception as e:
        print(f"{room:<10} FAIL {type(e).__name__}: {str(e)[:200]}", flush=True)
        res.append(dict(room=room, status="FAIL", error=f"{type(e).__name__}: {str(e)[:200]}"))
    json.dump(res, open(f"{OUT}/render_status.json", "w"), indent=1)

print(f"\nRENDERS DONE -> {OUT}", flush=True)
print("Next: metrics_night.py (full suite + per-region liveness).", flush=True)
