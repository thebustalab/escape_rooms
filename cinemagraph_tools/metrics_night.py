#!/usr/bin/env python3
"""The full metric suite over the five NIGHT/PRE-DAWN clips, with the five DAYTIME clips as a
calibrated baseline in the same table.

Why the daytime rows are here and not left in the old stage log: every threshold we have was
calibrated on bright harbour water. Reading a night number against those thresholds from memory is
exactly the mistake the README warns about for hotspot crops. Re-measuring both sets with ONE code
path makes the comparison honest.

WHAT IS NEW HERE, and why — the dark-scene correction.
`live%` counts a pixel as moving when its temporal standard deviation exceeds 6 grey levels out of
255. That is an ABSOLUTE threshold, and these scenes are dark: boat's water and hold's interior sit
at a fraction of the quay's brightness. A ripple of the same physical strength produces a far
smaller absolute std when the thing rippling is nearly black, so a night room can score "dead" while
being visibly alive. So every motion figure is reported four ways:

    live6    the legacy absolute threshold — comparable with every number in the notes
    live3    a lower absolute threshold — how much is moving just below the legacy floor
    mod%     mean temporal std as a PERCENTAGE of the region's mean luminance
    liveW    a Weber threshold with a floor: max(3, 5% of local brightness)

`mod%` was the obvious fix and it is NOT trustworthy on its own — measured on the daytime set it
ranks the library's light shaft, the one region that genuinely needed a repair tile, ABOVE the
quay's water. Its denominator goes to zero exactly where the signal is weakest. `liveW` is the
version to read: it scales the bar with brightness but never below 3 grey levels, so a dark-but-
moving region gets a fair hearing while a dark-and-dead one still reads dead.

Neither is calibrated against Lucas's judgement yet. Both are diagnostics for reading the dark
rooms, not gates. Treat them the way the handoff says to treat every metric: they can screen a clip
out, they cannot certify one as good.

Regions per room were placed by opening each panorama and naming what should move. They answer the
tile-repair question (handoff section 6 step 2): which named object failed to animate. A motion map
PNG is also written per clip, because a map that can be LOOKED at is more trustworthy than my
coordinate guesses.
"""
import os, sys, json, subprocess, tempfile
import numpy as np
from PIL import Image
import importlib.util

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = "/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms"
EGY = f"{ROOT}/rooms/wrangling/egypt"
NIGHT = "/home/bustalab/Documents/Tools/temp/egypt_night"
DAY = "/home/bustalab/Documents/Tools/temp/egypt_daytime"
OUTJSON = f"{NIGHT}/metrics_night.json"


def _load(name):
    sp = importlib.util.spec_from_file_location(name, f"{TOOLS}/{name}.py")
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


lt = _load("loop_table")
cd = _load("colour_drift")

# Regions: (x0, y0, x1, y1) in 3072x1024 source coordinates, with what each is FOR.
# A leading "!" marks a region that should stay STILL — a check, not a target.
REGIONS = {
 "boat": {
   "crown_fire":   (1500,  20, 1590, 150),   # the lighthouse flame — the scene's focal light
   "gold_road":    (1350, 470, 1730, 730),   # its broken reflection on the water
   "bow_lamp":     (1130, 540, 1230, 670),   # the near lamp at the prow
   "open_water_L": ( 100, 480, 1000, 820),   # dark open sea, the biggest single surface
   "city_lamps":   (2100, 330, 2700, 470),   # lamps along the harbour wall astern
   "moored_ship":  (2050, 290, 2250, 510),   # the wine ship left behind at the quay
   "!skiff_bow":   ( 800, 900, 2200,1020),   # the boat's own timbers — must not deform
 },
 "pharos": {
   "door_glow":    (1290, 110, 1730, 790),   # THE shot: fire-light round the sealed door
   "light_bars":   (1280, 760, 1780,1010),   # those bars thrown across the flagstones
   "stair_lamp":   (1850, 760, 1950, 850),   # small lamp at the head of the spiral stair
   "surf_rocks":   (2450, 740, 2820,1010),   # sea breaking white on the island's rocks
   "sea_left":     (  60, 340,  600, 620),   # open water to the horizon
   "city_far":     (1950, 300, 3000, 450),   # the distant lit city across the harbour
   "!columns":     ( 480,   0,  760, 1010),  # stone column — must not warp
 },
 "lantern": {
   "fire":         (1230,  60, 1750, 710),   # the great fire itself
   "mirror_shell": (1650, 110, 1930, 670),   # polished bronze gathering the light
   "fuel_smoke":   (2450, 290, 2820, 620),   # smoke off the stacked logs — the likely casualty
   "gallery_door": ( 690, 230,  950, 700),   # open door to the cold night gallery
   "seaward_arch": (2030, 210, 2450, 670),   # the beam pouring out to sea
   "!gear_ring":   ( 560, 740,  900,1000),   # the turning-dial — MUST NOT ROTATE
 },
 "deck": {
   "water_L":      ( 100, 530,  850, 670),   # the glassy pale harbour
   "pharos_fire":  ( 820, 220,  900, 300),   # the far crown-fire, small and gold
   "rigging":      (1120,   0, 2010, 600),   # lines and halyards off the mast
   "furled_sail":  (1090, 110, 2000, 240),   # cloth lashed along the yard
   "manifest":     (1080, 820, 1490,1010),   # parchment on the customs desk
   "hatch_lamp":   (1950, 870, 2080,1010),   # lamplight up out of the hold
   "sky":          ( 100,   0,  900, 300),   # dawn sky — expected near-still
   "!mast":        (1450,   0, 1560, 620),   # the mast — must stay rigid
 },
 "hold": {
   "lamp":         (1460, 250, 1610, 470),   # hanging bronze lamp: a true pendulum
   "light_shaft":  ( 750,  70,  950, 410),   # dawn light down the ladder — library's twin
   "ropes_L":      ( 630, 210,  730, 670),   # coiled rope hanging by the ladder
   "straw_R":      (1690, 490, 2310, 900),   # straw between the stacked jars
   "!planking_L":  (   0,   0,  300,1010),   # tarred hull at the seam — must not move
 },
 # daytime baselines, from stage AM's own scorecard regions where known
 "quay":         {"water": (300, 500, 2700, 950)},
 "emporion":     {"awning": (900, 150, 1800, 480)},
 "market_price": {"cloth": (1200, 300, 1800, 700)},
 "market_boast": {"awnings": (700, 150, 1600, 450)},
 "canopic":      {"fountain": (1300, 400, 1750, 850)},
 "library":      {"light_shaft": (1200, 100, 1700, 600)},
}


def sample(mp4, n=16):
    """Frames as a float stack. Stride derived from the ACTUAL frame count — a hardcoded 73
    silently sampled only the first third of a longer clip (motion_mask.py's own bug)."""
    d = tempfile.mkdtemp(prefix="mn_")
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, f"{d}/%04d.png"], check=True)
        fs = sorted(os.listdir(d))
        idx = np.linspace(0, len(fs) - 1, min(n, len(fs))).astype(int)
        ims = [np.asarray(Image.open(os.path.join(d, fs[i])).convert("RGB"), dtype=np.float32)
               for i in idx]
        return np.stack(ims)
    finally:
        subprocess.run(["rm", "-rf", d], check=False)


def shift_of(ref, img):
    F_ = np.fft.rfft2(ref) * np.conj(np.fft.rfft2(img)); F_ /= np.maximum(np.abs(F_), 1e-8)
    c = np.fft.irfft2(F_, s=ref.shape)
    dy, dx = np.unravel_index(np.argmax(c), c.shape)
    if dy > ref.shape[0] // 2: dy -= ref.shape[0]
    if dx > ref.shape[1] // 2: dx -= ref.shape[1]
    return dy, dx


def seam_ratio(gray):
    """Difference across the wrap over the mean interior column difference. ~1.2 is a genuinely
    seamless wrap, ~8 is a real cut; the verdict threshold is 2.5."""
    wrap_d = float(np.abs(gray[:, -1] - gray[:, 0]).mean())
    interior = float(np.abs(np.diff(gray, axis=1)).mean())
    return wrap_d / max(interior, 1e-6)


def analyse(mp4, src_png, regions):
    st = sample(mp4)
    tstd = st.std(axis=0).mean(axis=2)          # per-pixel temporal std, greyscale
    luma = st.mean(axis=0).mean(axis=2)         # per-pixel mean brightness
    H, W = tstd.shape

    def stats(a_t, a_l):
        m = float(a_l.mean())
        # liveW — a Weber threshold WITH A FLOOR. The eye responds to relative change, so a fixed
        # 6-grey-level bar is too strict in a dark room; but a pure ratio (mod%) has a denominator
        # that goes to zero and therefore inflates exactly where the signal is weakest. Measured on
        # the daytime set, mod% ranks the library's light shaft — the one region that genuinely
        # needed a repair tile — ABOVE the quay's water, which is plainly wrong. Scaling the
        # threshold with local brightness but never letting it fall below 3 keeps codec noise out
        # and still gives dark-but-moving pixels a fair hearing.
        thr = np.maximum(3.0, 0.05 * a_l)
        # p95 — the MEAN over a region dilutes a small bright object to nothing. Measured here:
        # boat's crown-fire scored tstd 2.40 and library-like "dead", and the fuel-store smoke in
        # lantern scored 3.43, yet both are plainly animating when you crop in and look. The boxes
        # are mostly static black sky / static logs, and the average is dominated by those. p95 asks
        # "is the liveliest part of this region moving", which is the actual question when the
        # object of interest occupies a fraction of its own bounding box.
        return dict(live6=float((a_t > 6).mean() * 100),
                    live3=float((a_t > 3).mean() * 100),
                    liveW=float((a_t > thr).mean() * 100),
                    tstd=float(a_t.mean()),
                    p95=float(np.percentile(a_t, 95)),
                    luma=m,
                    mod=float(a_t.mean() / max(m, 1e-6) * 100))

    out = {"whole": stats(tstd, luma)}

    band = lambda lo, hi: stats(tstd[int(H*lo):int(H*hi)], luma[int(H*lo):int(H*hi)])
    out["bands"] = {"top": band(0, .34), "mid": band(.34, .67), "bot": band(.67, 1.)}

    reg = {}
    sx, sy = W / 3072.0, H / 1024.0
    for name, (x0, y0, x1, y1) in (regions or {}).items():
        a, b = int(y0*sy), max(int(y1*sy), int(y0*sy)+1)
        c, d_ = int(x0*sx), max(int(x1*sx), int(x0*sx)+1)
        reg[name] = stats(tstd[a:b, c:d_], luma[a:b, c:d_])
    out["regions"] = reg

    # incoherence: does the architecture itself drift? travels with live% always.
    g = [f.mean(axis=2) for f in st[:6]]
    gh, gw = g[0].shape[0] // 3, g[0].shape[1] // 8
    vs = [shift_of(g[0][y*gh:(y+1)*gh, x*gw:(x+1)*gw], fr[y*gh:(y+1)*gh, x*gw:(x+1)*gw])
          for fr in g[1:] for y in range(3) for x in range(8)]
    v = np.array(vs, dtype=np.float64)
    out["incoh"] = float(np.linalg.norm(v - v.mean(axis=0), axis=1).mean())

    g0 = st[0].mean(axis=2)
    out["detail"] = float(np.abs(np.diff(g0, axis=0)).mean() + np.abs(np.diff(g0, axis=1)).mean())
    out["seam"] = seam_ratio(g0)

    try:
        _t, _adj, ratio, _n, absj = lt.table(lt.frames(mp4))
        out["jump"], out["jump_ratio"] = float(absj), float(ratio)
    except Exception as e:
        out["jump"], out["jump_ratio"] = float("nan"), float("nan")
        out["jump_error"] = str(e)[:120]

    try:
        out["colour"] = float(cd.colour_drift(mp4)[0])
    except Exception as e:
        out["colour"] = float("nan"); out["colour_error"] = str(e)[:120]

    if src_png and os.path.isfile(src_png):
        f0 = st[0].mean(axis=2)
        src = np.asarray(Image.open(src_png).convert("L").resize((f0.shape[1], f0.shape[0])),
                         dtype=np.float32)
        out["corr"] = float(np.corrcoef(src.ravel(), f0.ravel())[0, 1])
        out["src_seam"] = seam_ratio(src)

    # a motion map to LOOK at — more trustworthy than my coordinate guesses
    mm = np.clip((tstd - 1.0) / 10.0, 0, 1)
    Image.fromarray((mm * 255).astype(np.uint8)).save(mp4.replace(".mp4", "_motion.png"))
    return out


NIGHT_ROOMS = ["boat", "pharos", "lantern", "deck", "hold"]
# The night VARIANTS. Their art prompts all say "keep this exact composition, every object at the
# same position and the same scale" and change only the time of day — so the daytime region boxes
# apply unchanged to the night state, which is why they are reused rather than re-placed.
VAR_ROOMS = ["deck", "quay", "emporion", "market_price", "market_boast", "canopic", "library"]
DAY_ROOMS = ["quay", "emporion", "market_price", "market_boast", "canopic", "library"]

# The daytime baseline is stage AM's UNREPAIRED base renders — the same thing the night clips are.
# Comparing a night base render against a repaired daytime clip would flatter the daytime side.
# quay has no stage-AM render of its own; its control clip is the one every threshold was set on.
QUAY_CONTROL = f"{ROOT}/authoring_v2/ui/cine360/quay_control_3072.mp4"

jobs = []
for r in NIGHT_ROOMS:
    p = f"{NIGHT}/{r}.mp4"
    if os.path.isfile(p): jobs.append(("night", r, p, f"{EGY}/{r}/scene.png"))
for r in DAY_ROOMS:
    p = QUAY_CONTROL if r == "quay" else f"{DAY}/{r}.mp4"
    if os.path.isfile(p): jobs.append(("day", r, p, f"{EGY}/{r}/scene.png"))
for r in VAR_ROOMS:
    p = f"{NIGHT}/{r}_night.mp4"
    if os.path.isfile(p):
        jobs.append(("nightvar", r + "_night", p, f"{EGY}/{r}/scene_night.png"))
        REGIONS[r + "_night"] = REGIONS.get(r, {})

results = {}
for kind, room, path, src in jobs:
    try:
        results[room] = analyse(path, src, REGIONS.get(room))
        results[room]["kind"] = kind
        results[room]["path"] = path
        print(f"measured {kind:<6} {room}", flush=True)
    except Exception as e:
        print(f"FAILED   {kind:<6} {room}: {type(e).__name__}: {str(e)[:150]}", flush=True)

json.dump(results, open(OUTJSON, "w"), indent=1)

# ---- report ----
def row(room, d):
    w = d["whole"]
    return (f"{room:<14} {d.get('corr',float('nan')):5.3f} {d['jump']:6.2f} {d['jump_ratio']:5.1f}x "
            f"{w['live6']:6.1f} {w['liveW']:6.1f} {w['tstd']:6.2f} {w['luma']:6.1f} {w['mod']:6.1f} "
            f"{d['incoh']:6.2f} {d['colour']:6.2f} {d['seam']:5.2f} {d['detail']:6.2f}")

print("\n" + "=" * 108)
print("FULL SUITE — night rooms above the line, daytime baseline below")
print("=" * 108)
print(f"{'room':<14} {'corr':>5} {'JUMP':>6} {'ratio':>6} {'live6':>6} {'liveW':>6} {'tstd':>6} "
      f"{'luma':>6} {'mod%':>6} {'incoh':>6} {'colour':>6} {'seam':>5} {'detail':>6}")
print("-" * 108)
for r in NIGHT_ROOMS:
    if r in results: print(row(r, results[r]))
print("-" * 108 + "   night VARIANTS")
for r in [x + "_night" for x in VAR_ROOMS]:
    if r in results: print(row(r, results[r]))
print("-" * 108 + "   daytime baseline")
for r in DAY_ROOMS:
    if r in results: print(row(r, results[r]))

print("\n" + "=" * 108)
print("PER-REGION LIVENESS — the tile-repair question: which named object failed to animate?")
print("a leading ! marks a region that SHOULD be still")
print("=" * 108)
for r in NIGHT_ROOMS + [x + "_night" for x in VAR_ROOMS] + DAY_ROOMS:
    if r not in results or not results[r]["regions"]: continue
    print(f"\n{r}")
    print(f"  {'region':<16} {'tstd':>6} {'p95':>6} {'luma':>6} {'mod%':>6} {'live6':>6} {'liveW':>6}")
    for name, s in results[r]["regions"].items():
        print(f"  {name:<16} {s['tstd']:6.2f} {s['p95']:6.2f} {s['luma']:6.1f} {s['mod']:6.1f} "
              f"{s['live6']:6.1f} {s['liveW']:6.1f}")

print(f"\n-> {OUTJSON}")
print("-> motion maps written alongside each clip as <room>_motion.png")
