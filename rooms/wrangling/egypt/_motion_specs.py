#!/usr/bin/env python3
"""_motion_specs.py — egypt's motion specs, authored once and written onto the room nodes.

WHY THIS EXISTS AS A FILE. A motion spec is a judgement about what should move in a scene; it is not
derivable from the art, and a variant that shipped with no recorded prompt is the handoff's standing
complaint. So the spec lives on the room node (`authoring.motionSpec`) and this script is the record of
how it was authored — re-run it to restore or revise.

AUTHORED 2026-09-02, for the move from BOXED clips to FULL-SCENE ones. Egypt's original eight clips each
animated a single object in its own box; the scenario is being rebuilt on the full-scene LTX pipeline, so
every room now needs a whole-frame spec instead. Each was drafted from BOTH inputs the protocol requires:
the committed panorama, opened and looked at, and the room's stored `authoring.scenePrompt`.

THE DAY ARC IS THE DESIGN. Egypt walks a single day — deck at first light, the hold below the waterline,
quay in early morning, emporion in the morning, the wine market at hard midday, the boast stall in early
afternoon, the Canopic Way in late afternoon, the Library at dusk, the skiff at nightfall, then the
lantern gallery and the lamp chamber at the summit. The motion follows it: water goes from glassy at
dawn to real chop offshore at night, and light goes from a sky that carries the scene to a flame that
does. Two rooms are already night (boat, lantern) and take no night variant.

WHAT IS AND ISN'T NAMED. Only oscillatory phenomena — water surfaces, flame, smoke, hanging cloth,
drifting dust. The recipe pins frame 0 and frame -1 to the same still, so a two-ended loop cannot express
net travel; naming anything that must GO somewhere only starts a fight the end-guide wins.

DOCUMENTS ARE THE INVERSE TRAP, and egypt is full of them. The chalked price-board, the reject-slate, the
Library's open codices and the bronze relief in the gallery must all be explicitly PINNED: the deck render
grew a curling corner with crawling text until its map was, and this scenario has nine such surfaces.
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "cinemagraph_tools"))
import motion_spec as MS  # noqa: E402

HARNESS = "http://127.0.0.1:8752"
CHAPTER, SCENARIO = "wrangling", "egypt"

SHIP_RIGID = ("The hull, deck planking, mast, yard, rails, crates, amphorae, ladder and all cargo")
QUAY_RIGID = ("The quay stonework, steps, columns, arches, warehouse front, moored hulls, amphorae, "
              "barrels, baskets and the city across the water")
STREET_RIGID = ("The paving, columns, colonnade, walls, stalls, counters, stacked amphorae, baskets and "
                "the buildings")
TOWER_RIGID = ("The tower stonework, columns, parapet, paving, bronze door, relief panel, machinery, "
               "firewood and the city across the water")

# The one lamp sentence, used wherever a room has a live flame in a lamp. Named because a subject that is
# not in the prompt is not animated and not measured — the scheme's blind spot is whatever you forgot to
# list, and lamps were exactly what canyon forgot on its first pass.
LAMP = ("the hanging oil lamps burning with a small live flame that wavers and settles, their pools of "
        "warm light breathing on the stone around them")

# ── the Library's pins are GENERATED, not listed ─────────────────────────────────────────────────
# AUTHORED 2026-09-04. Lucas, on the rebuilt Library's clips: "still has all sorts of pages turning and
# falling everywhere. All the paper needs to be still, focus on lights twinkling instead."
#
# The six day / seven night hand-drawn pins were WORKING — every one of them measured 0.31-1.37 in the
# baked clips. There simply were not enough of them. The rebuilt hall is a ring of scroll-niches from
# floor to vault, and the motion map showed the whole of that ring alight: left wall p95 15.3, right
# wall 17.8, against the veils the room exists to show at 20.9. That is the case the threshold slider
# cannot express — the paper moves as hard as the hero — and the region cut is worse still, because a
# scroll rack is exactly the large coherent region it keeps. Only pins reach it, and a pin only reaches
# what it is drawn over. Listing the remaining paper by hand would have meant hand-drawing most of a
# 3072x1024 frame and being wrong about the corner nobody checked.
#
# So the rule is INVERTED here: name what may move, and pin the complement. `_pins()` grids the frame,
# marks every cell touched by a free box, and emits the rest as merged rectangles. Adding a mover
# automatically re-cuts the pins around it, which is the property the hand-drawn set did not have.
#
# THE LAMPS ARE THE HOLES, and they are why this is not simply "freeze everything but the veils". The
# twinkle Lucas asked for lives in ~44 practical lights, measured photometrically off `scene_night.png`
# (warm + bright + compact, the `find_lights.py` test) and merged into 14 holes. They are taken from the
# NIGHT plate for BOTH states because the night variant preserves the day composition object for object,
# and by day the sunlit floor outshines every lamp in the room — a photometric pass on `scene.png`
# returns nothing but paving glints. Measure where the lights are on the plate that shows them.
#
# THE HOLE IS THE LAMP GLASS, NOT THE LIGHT POOL, and getting that wrong wasted a bake. The first
# halo (0.009 x, 0.028 up) was drawn to take the flame AND the warmth it throws, on the assumption
# that what moves around a lamp is its light. Frame-by-frame it is not: the lamp sits still and its
# flame varies cleanly inside the glass, while the SCROLL STACK BEHIND IT churns from one frame to
# the next — rolled ends becoming dark blobs and back. That churn is Lucas's "pages falling
# everywhere" at close range, and a halo-sized hole hands it a rectangle to do it in, with a hard
# black edge around it (measured envelope p99 143 inside the hole, 0 outside). So the halo is now
# barely larger than the measured flame blob: the hole lands on the lamp's own outline, where the
# picture already has an edge, and the light pool on the desk stays pinned with the paper it lies on.
# The asymmetry is kept — a flame throws upward and the paper lies below it.
LIB_LAMPS = [
    [0.0977, 0.5039, 0.1035, 0.5215], [0.0954, 0.5156, 0.0970, 0.5244], [0.0924, 0.5156, 0.0951, 0.5205],
    [0.0898, 0.5088, 0.0905, 0.5127], [0.2028, 0.5137, 0.2080, 0.5225], [0.2692, 0.5176, 0.2702, 0.5244],
    [0.3252, 0.3965, 0.3262, 0.4131], [0.4642, 0.5615, 0.4674, 0.5693], [0.4665, 0.5674, 0.4701, 0.5732],
    [0.4668, 0.5576, 0.4688, 0.5635], [0.4707, 0.5596, 0.4756, 0.5654], [0.4915, 0.5732, 0.4977, 0.5811],
    [0.4967, 0.5508, 0.5013, 0.5605], [0.4990, 0.5732, 0.5088, 0.5859], [0.5000, 0.5605, 0.5029, 0.5654],
    [0.4974, 0.5781, 0.4980, 0.5850], [0.5016, 0.5576, 0.5039, 0.5605], [0.5352, 0.5527, 0.5394, 0.5605],
    [0.6325, 0.5674, 0.6465, 0.5713], [0.6367, 0.5674, 0.6436, 0.5693], [0.6436, 0.5645, 0.6465, 0.5674],
    [0.6579, 0.4990, 0.6595, 0.5029], [0.7109, 0.5029, 0.7119, 0.5059], [0.7259, 0.5645, 0.7285, 0.5654],
    [0.7474, 0.5723, 0.7536, 0.5791], [0.7542, 0.5732, 0.7562, 0.5752], [0.7809, 0.5801, 0.7819, 0.5830],
    [0.7819, 0.6045, 0.7852, 0.6055], [0.8066, 0.5830, 0.8102, 0.5879], [0.8073, 0.6094, 0.8145, 0.6143],
    [0.8099, 0.5986, 0.8158, 0.6045], [0.8102, 0.5850, 0.8161, 0.5889], [0.8115, 0.6133, 0.8154, 0.6172],
    [0.8138, 0.5410, 0.8167, 0.5527], [0.8154, 0.5527, 0.8171, 0.5557], [0.8167, 0.5811, 0.8223, 0.5918],
    [0.8177, 0.5420, 0.8213, 0.5596], [0.8200, 0.5654, 0.8213, 0.5703], [0.8223, 0.5352, 0.8229, 0.5430],
    [0.8223, 0.5488, 0.8239, 0.5566], [0.8659, 0.6299, 0.8678, 0.6328], [0.8665, 0.6152, 0.8717, 0.6279],
    [0.8717, 0.5898, 0.8770, 0.6035],
]
LIB_HALO = (0.002, 0.006, 0.004)         # (x, up, down) — see above; ~6x10 px on a 3072x1024 frame
# THE VEILS WERE PINNED AND ARE NOW BACK — Lucas overturned it the same day: "can it just be the
# fabric and the light/lanterns? Try prompting hard for gentle motion in fabric and lights/lanterns
# and negative prompting on paper, scrolls, books." That is the RIGHT fix and pinning was the wrong
# one: the churn is in the RENDER, and a pin only hides it by freezing whatever sits on top of it.
# The history below is kept because it is what says a pin cannot save this room on its own.
#
# The cloth itself is not the problem: frame by frame the panels hang coherently, their folds shift,
# and the envelope climbs smoothly down them (p95 13 at the top to 75 near the hems) exactly as
# hanging linen should. The problem is that the veils are SHEER. The scroll shelving is visible
# THROUGH them, and that shelving is what this render churns — scroll ends swelling into pale blobs
# and back between consecutive frames. Three geometries were tried and measured, and the failure is
# the same each time because it is not geometric:
#   * one rectangle 0.735-0.888 — takes in the gaps BETWEEN panels, which churn worst;
#   * six columns, one per panel (detected off the still as the runs of pale cloth in y 0.30-0.52,
#     column-mean brightness above its 42nd percentile) — the churn stays, because it is BEHIND the
#     cloth, not beside it;
#   * cutting the columns short above the churn band — moves a hard pin edge onto lit cloth that is
#     still moving at p95 65, which is the most visible place a pin edge can possibly land.
# There is no box that contains the linen and excludes the shelving, because they occupy the same
# pixels. Lucas: "All the paper needs to be still, focus on lights twinkling instead" — the veils are
# how the paper was still getting in, so they go, and the lights carry the room.
#
# TO PUT THEM BACK: restore the six columns below and re-bake. No GPU, about four minutes.
LIB_VEIL_COLS = [[0.7298, 0.7354], [0.7581, 0.7731], [0.7809, 0.7920],
                 [0.7995, 0.8109], [0.8164, 0.8519], [0.8636, 0.8792]]
LIB_VEILS = [[c[0] - 0.0025, 0.140, c[1] + 0.0025, 0.535] for c in LIB_VEIL_COLS]
def _beam_bands(y_top, y_bot, step=0.014):
    """The light shaft as a fine staircase between its two sloping edges.

    The edges are MEASURED, not eyeballed: a brightness profile across the wall at twelve heights,
    taking the widest run above the row's own median plus 45% of its range. Two earlier by-eye traces
    were both badly wrong in the same direction — they had the beam leaning hard left and fanning to
    0.116 wide at the floor, when it actually stays near-vertical and NARROWS, 0.065 wide at y 0.22
    down to 0.039 at y 0.54. The wedge those traces freed took in the scroll shelving down its whole
    left flank, which is the paper this pass exists to hold still.

    Bands are ~14 px tall on a 1024-px frame, so each horizontal step is ~1 px: far finer than the
    beam's own soft edge, and the boundary disappears into the light instead of drawing a staircase."""
    L0, L1 = 0.629, 0.622          # left edge at y_top / y_bot (measured, +0.005 margin)
    R0, R1 = 0.705, 0.686          # right edge at y_top / y_bot (measured, +0.005 margin)
    out, y = [], y_top
    while y < y_bot - 1e-9:
        y2 = min(y + step, y_bot)
        t0, t1 = (y - y_top) / (y_bot - y_top), (y2 - y_top) / (y_bot - y_top)
        # each band takes the WIDEST extent it spans, so no sliver of beam falls between two bands
        out.append([round(L0 + (L1 - L0) * t1, 4), round(y, 4),
                    round(R0 + (R1 - R0) * t0, 4), round(y2, 4)])
        y = y2
    return out


# THE SHAFT IS A DIAGONAL WEDGE, so it is freed as a staircase, not as one rectangle. The first pass
# used the subject's own measurement box, [0.575, 0.075, 0.722, 0.560], and that rectangle is mostly
# WALL — its corners sat on the scroll-niches either side of the light and freed them to animate, the
# same diagonal-boundary fault as deck's night sea. The second pass fixed the geometry with six bands
# and introduced a new artefact: six steps are visible AS steps. Hence `_beam_bands`.
# THE BEAM IS FREED ONLY DOWN TO THE GALLERY RAIL (y 0.330), and that is a judgement call worth
# stating plainly, because it gives up part of a mover the rebuilt room was designed around.
# Below the rail the shaft crosses the great stone pier, and there is NO rectangle that separates the
# airborne haze from the lit masonry behind it — they occupy the same pixels. Freeing that stretch
# freed the pier, the arch mouldings, a ladder and a run of scroll shelving down its left flank, and
# all of them crawled harder than the dust did (the day shaft's own hero motion measured 11.8 against
# the veils at 20.9). Two traces of the beam's edges disagreed for exactly this reason: measured
# photometrically it returns the LIT PIER, a near-vertical column; traced by eye it returns the
# airborne haze, which fans left. Both are really there; only one of them should move.
# So the free region stops at the gallery rail — a horizontal architectural line that already exists
# in the picture, which is the only kind of place a pin edge can hide. What remains is the window and
# the first throw of light out of it, which is the legible part anyway.
LIB_SHAFT = [[0.646, 0.068, 0.710, 0.200]] + _beam_bands(0.200, 0.330)
LIB_CLOCKWATER = [0.302, 0.326, 0.350, 0.436]
# The floor's sun-pool is NOT freed, and the first pass was wrong to free it. The room's own `rigid` line
# already ends "...and the floor" — stone paving that shimmers is the model animating masonry, not light,
# and it measured p95 44, the hottest thing in the day frame. Freeing it also meant a hard-edged
# RECTANGLE of moving paving in the middle of a still floor, which is the one artefact a still-pin can
# introduce: an edge is invisible where nothing moves and glaring where something does.


def _merge(boxes):
    """Union overlapping boxes until nothing overlaps — so two lamps a few pixels apart make one hole."""
    bs = [list(b) for b in boxes]
    changed = True
    while changed:
        changed, out = False, []
        while bs:
            a = bs.pop()
            for i, b in enumerate(out):
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    out[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    changed = True
                    break
            else:
                out.append(a)
        bs = out
    return bs


def _pins(free, nx=512, ny=256):
    """Every part of the frame NOT covered by a free box, as merged rectangles.

    512x256 puts a cell at 6x4 px on a 3072x1024 panorama. That is finer than the beam staircase's own
    14-px bands, which matters: at the first resolution the bands snapped to 8-px rows and the steps
    re-appeared as steps. It is still coarse enough to keep the rectangle count in the dozens. Cells are grown right then down, greedily, so a plain wall comes back as one box."""
    xs = [i / nx for i in range(nx + 1)]
    ys = [j / ny for j in range(ny + 1)]
    grid = [[False] * nx for _ in range(ny)]
    for x0, y0, x1, y1 in free:
        for j in range(max(0, int(y0 * ny)), min(ny, int(y1 * ny + 0.999))):
            for i in range(max(0, int(x0 * nx)), min(nx, int(x1 * nx + 0.999))):
                grid[j][i] = True
    used = [[False] * nx for _ in range(ny)]
    out = []
    for j in range(ny):
        i = 0
        while i < nx:
            if grid[j][i] or used[j][i]:
                i += 1
                continue
            i2 = i
            while i2 < nx and not grid[j][i2] and not used[j][i2]:
                i2 += 1
            j2 = j + 1
            while j2 < ny and all(not grid[j2][k] and not used[j2][k] for k in range(i, i2)):
                j2 += 1
            for jj in range(j, j2):
                for ii in range(i, i2):
                    used[jj][ii] = True
            out.append([round(xs[i], 4), round(ys[j], 4), round(xs[i2], 4), round(ys[j2], 4)])
            i = i2
    return out


LIB_VEIL_PHRASE = ("the tall sheer linen veils hung down the right-hand wall, stirring very gently and "
                   "settling again in the faintest draught, a slow soft breathing of cloth and nothing "
                   "more")
LIB_LAMP_PHRASE = ("the little oil lamps and lanterns burning all round the hall, each flame alive and "
                   "unsteady inside its glass, gently swelling and sinking so the warm light on the "
                   "wood beside it breathes with it")


# ── pharos: the same inversion the Library needed, for the same reason ───────────────────────────
# THIRD PASS, 2026-09-04. Lucas: "the water is still really fast and the light pulses too much. The
# water issue is mainly right at the shore by the little boat and the rocks."
#
# THE SHORE WATER WAS NEVER A SUBJECT. open_sea, inner_water and rock_surf between them cover the
# offshore water and the spur, and they DID slow down when their phrases were rewritten — the open sea
# is nearly flat now. The stretch Lucas is pointing at, the foam around the rocks below the mooring
# lamp and the little boat, sat outside all three boxes. Nothing named it, so nothing governed its
# pace: "the scheme's blind spot is whatever you forgot to list". Two rounds of slowing the water were
# slowing the wrong water. It is named now, and its phrase is the slowest in the room.
#
# THE PULSE IS CAPPED IN THE MASK, not just asked away. Tempering the phrases took the whole-frame
# luminance swing from 37.8 to 6.7 — a real fix, and still an order of magnitude above the 0.3-1.6
# every other clip in the scenario sits at, because the door glow lights the ENTIRE cliff and paving
# and a prompt cannot promise how far a light spreads. So pharos now frees only the light ITSELF —
# four thin seams around the door and a shallow band of the brightest paving at its threshold — plus
# the water, the city lights and the stair lamp, and pins the rest. Stone that changes brightness is
# the artefact; stone is the thing being pinned.
# `floor_rays` is DROPPED as a subject: it was the phrase that tied the whole paving to the door's
# pulse ("brightening and dimming WITH IT"), and the paving is in `rigid` anyway.
PHAROS_SEAMS = [
    [0.4360, 0.0980, 0.4540, 0.7760],   # left edge of the door
    [0.5370, 0.0980, 0.5580, 0.7760],   # right edge
    [0.4360, 0.0900, 0.5580, 0.1260],   # head
    [0.4400, 0.7300, 0.5460, 0.7800],   # foot
    [0.4189, 0.7715, 0.5882, 0.8500],   # the brightest paving at the threshold
]
# The inner box STOPS AT 0.800, not 0.870: its lower strip reached into the shore band that is
# pinned below, so a free mover overlapped a pin and the shore kept a residual p95 7.8 after
# being 'pinned'. Overlapping boxes are decided by whichever list is applied last, which is not
# something to leave to chance. Its LEFT edge moved 0.898 -> 0.910 for the same reason: an
# 8-px sliver of it lay over the spur's pinned foam and carried that box's whole p95.
PHAROS_WATER_OPEN = [[0.840, 0.400, 1.000, 0.478], [0.910, 0.500, 0.975, 0.800]]
# THE SHORE WATER IS PINNED, after prompting was given two clear goes at it and did not take.
# Naming it worked in the sense that matters — it went from unnamed to governed — but the foam among
# the rocks still re-formed wholesale between consecutive frames at p95 19-29, and it brought a second
# problem with it: the water was the only thing moving against newly-pinned rock, so the pin boundary
# itself became visible, a straight edge across a pale wash. That is the rule this scenario keeps
# re-learning — an edge is invisible where nothing moves and glaring where something does.
# Pinning it fixes both at once and costs a re-bake, not a render. What it costs is a still shoreline;
# at night, in a sheltered rocky inlet far below the parapet, that reads. The OPEN water keeps its
# slow swell, so the room still has moving sea.
# TO GIVE IT BACK: return this list to the `out +=` in `pharos_movers` and re-bake.
PHAROS_WATER_SHORE = [[0.860, 0.540, 0.906, 0.770],     # the spur's foam
                      [0.862, 0.845, 0.938, 0.912],     # AT THE BOAT — the stretch Lucas flagged twice
                      [0.869, 0.912, 0.922, 0.975]]
# The city band is SPLIT around the near column: as one rectangle it freed the column and the parapet
# in front of the far shore, and freed stone is stone that can brighten — the exact artefact this pass
# is capping.
PHAROS_CITY = [[0.620, 0.300, 0.752, 0.440], [0.782, 0.300, 0.990, 0.440]]
PHAROS_STAIR_LAMP = [0.595, 0.73, 0.635, 0.84]

PHAROS_SEAM_PHRASE = ("a steady seam of hot gold light around the edges of the sealed bronze door, "
                      "holding almost perfectly constant and lifting only the very slightest amount, "
                      "never flaring, pulsing, throbbing or washing out across the stone")
PHAROS_OPEN_PHRASE = ("the black sea far below lying heavy and almost flat, swelling and settling again "
                      "in one long, slow rhythm, its surface barely creasing and never hurrying")
PHAROS_SHORE_PHRASE = ("the pale foam among the rocks at the water's edge below the mooring lamp, "
                       "easing in and thinning out again very slowly indeed, the slowest thing in the "
                       "picture, never breaking, rushing, churning or throwing spray")


def pharos_movers():
    """The light, the water and the lamps — one subject per location, one phrase each."""
    out = [{"name": "door_seam_%d" % n, "box": b, "phrase": PHAROS_SEAM_PHRASE}
           for n, b in enumerate(PHAROS_SEAMS, 1)]
    out += [{"name": "open_water_%d" % n, "box": b, "phrase": PHAROS_OPEN_PHRASE}
            for n, b in enumerate(PHAROS_WATER_OPEN, 1)]
    # PHAROS_WATER_SHORE is NOT here — it is pinned. See the note above `PHAROS_WATER_SHORE`.
    out += [{"name": "city_lights_%d" % n, "box": b,
             "phrase": "the lamps of the city along the far shore, each small light breathing and steadying"}
            for n, b in enumerate(PHAROS_CITY, 1)]
    out += [{"name": "stair_lamp", "box": PHAROS_STAIR_LAMP,
             "phrase": "the small lamp burning at the head of the stair, its flame alive and just "
                       "perceptibly wavering inside its glass"}]
    return out


def pharos_pins():
    """Everything the movers do not claim — tower, paving, cliff, rocks, boat, and the shore water."""
    subs = [{"name": "ph_hold_%02d" % n, "box": b, "still": True}
            for n, b in enumerate(_pins([m["box"] for m in pharos_movers()]), 1)]
    subs[0]["phrase"] = ("The tower, its parapet and paving, the bronze door and its relief, the cliff, "
                         "the rocks and the moored boat are stone, metal and timber: they do not move, "
                         "and they do not brighten or darken as a whole.")
    return subs


def library_movers(state):
    """The Library's movers: the cloth and the lights, one subject per LOCATION, one phrase each.

    Lucas, after the pinned bake: "can it just be the fabric and the light/lanterns?" So the mover list
    is exactly that — six veil panels and every practical lamp in the room — plus the window shaft and
    the clepsydra's falling ribbon, which are light and water rather than paper and were never part of
    the complaint. Each veil and each lamp needs its own box to be measured, but they share one phrase
    and `render_prompt` de-duplicates, so the composed prompt names cloth once and lamps once.

    These are the SAME boxes `library_pins` frees, which is the property that matters: a mover the pins
    overlap is a mover that cannot move, and that is only guaranteed if one list generates both."""
    out = [{"name": "veil_%d" % n, "box": b, "phrase": LIB_VEIL_PHRASE}
           for n, b in enumerate(LIB_VEILS, 1)]
    out += [{"name": "lamp_%02d" % n, "box": b, "phrase": LIB_LAMP_PHRASE}
            for n, b in enumerate(_lamp_holes(), 1)]
    return out


def _lamp_holes():
    """The measured lamp blobs, dilated by LIB_HALO and unioned."""
    mx, mu, md = LIB_HALO
    return _merge([[max(0.0, b[0] - mx), max(0.0, b[1] - mu), min(1.0, b[2] + mx), min(1.0, b[3] + md)]
                   for b in LIB_LAMPS])


def library_pins(state):
    """The Library's `still: True` subjects for one state — the complement of everything allowed to move."""
    free = [LIB_CLOCKWATER] + LIB_SHAFT + [m["box"] for m in library_movers(state)]
    subs = [{"name": "hold_%02d" % n, "box": b, "still": True}
            for n, b in enumerate(_pins(free), 1)]
    # One pin carries the sentence, so the composed prompt states the rule once instead of thirty times.
    subs[0]["phrase"] = ("Every scroll, ledger, codex, wax tablet and loose sheet in the hall — on the "
                         "desks, in the wall-niches, stacked on the floor and piled on the carts — lies "
                         "absolutely dead still. No page turns, lifts, curls, falls or slips, no scroll "
                         "unrolls, rocks or topples, and no lettering moves.")
    return subs


SPECS = {
    # ── first light on the moored ship: a glassy harbour and the Pharos still lit ──────────────────
    "deck": {
        "rigid": SHIP_RIGID,
        "has_document": True,
        "pinned": ["The written tablet and the open ledger on the deck table lie flat and still; their "
                   "ruled lines and lettering do not move, lift, curl or change."],
        "negatives": [", rising water, waves breaking over the deck, a wave rolling in, a swell "
                      "travelling across the water, water running up the hull or over the rail, the "
                      "ship rocking, the ship sailing away, sails unfurling, fast moving clouds, "
                      "time-lapse sky"],
        "subjects": [
            {"name": "dawn_sky", "box": [0.0, 0.0, 1.0, 0.30],
             "phrase": "the pale dawn sky above the harbour, its colour breathing almost imperceptibly "
                       "from cool to warm and back"},
            {"name": "harbour_water", "box": [0.0, 0.42, 0.34, 0.62],
             "phrase": "the flat dawn harbour lying almost glassy, only the faintest slow swell moving "
                       "across it and the light sliding on its skin"},
            {"name": "pharos_flame", "box": [0.258, 0.1959, 0.2999, 0.3676], "force_repair": True,
             "phrase": "the signal fire burning at the head of the distant Pharos, a small hot point of "
                       "gold flame guttering and flaring against the dawn"},
            {"name": "furled_sail", "box": [0.34, 0.09, 0.63, 0.23],
             "phrase": "the great furled sail lashed along its yard, its loose canvas edges stirring "
                       "very slightly in the morning air"},
            {"name": "deck_lamp", "box": [0.63, 0.80, 0.69, 0.93],
             "phrase": "the lamp burning down in the open deck hatch, its flame small and live, the "
                       "warm light wavering on the timbers around it"},
        ],
    },
    # ── the hold: one lamp, one shaft of daylight, and the ship breathing at her mooring ───────────
    "hold": {
        "rigid": SHIP_RIGID,
        "negatives": [", the ship moving, cargo shifting, amphorae rolling, water entering the hold"],
        "subjects": [
            {"name": "hold_lamp", "box": [0.4615, 0.0854, 0.5422, 0.4874],
             "phrase": "the hanging oil lamp on its chain in the middle of the hold, its flame live and "
                       "restless, the lamp itself swinging only the smallest amount and returning, its "
                       "light breathing out across the stacked jars"},
            {"name": "hatch_shaft", "box": [0.20, 0.06, 0.34, 0.34],
             "phrase": "the pale shaft of daylight falling down the open hatch and the ladder, fine dust "
                       "turning slowly through it"},
            {"name": "hanging_ropes", "box": [0.18, 0.24, 0.26, 0.68],
             "phrase": "the coiled ropes hanging against the hull, swaying by the smallest amount as the "
                       "moored ship works"},
        ],
    },
    # ── the harbour steps: early morning, the working quay ────────────────────────────────────────
    "quay": {
        "rigid": QUAY_RIGID,
        "negatives": [", boats sailing away, the ship departing, rising tide, waves breaking over the "
                      "quay, fast moving clouds"],
        "subjects": [
            {"name": "harbour_water", "box": [0.0, 0.44, 1.0, 0.66],
             "phrase": "the pale green harbour water lapping along the quay stones and around the moored "
                       "hulls, its surface wrinkling and settling in place"},
            {"name": "moored_boats", "box": [0.1991, 0.377, 0.4023, 0.7097],
             "phrase": "the row of small moored boats rocking gently at their lines, their masts leaning "
                       "the smallest amount and coming back"},
            {"name": "bunting", "box": [0.20, 0.36, 0.40, 0.46],
             "phrase": "the strung bunting between the boats' masts lifting and falling on the morning air"},
            {"name": "pharos_flame", "box": [0.485, 0.20, 0.515, 0.36],
             "phrase": "the fire burning at the head of the Pharos out on its mole, a small point of gold "
                       "flame against the morning sky"},
            {"name": "morning_cloud", "box": [0.0, 0.0, 1.0, 0.26],
             "phrase": "the high morning cloud over the harbour, turning over very slowly in place"},
        ],
    },
    # ── the emporion: the awning is the thing, and it has stayed dead before ───────────────────────
    "emporion": {
        "rigid": QUAY_RIGID,
        "negatives": [", the awning tearing free, cargo moving, people, fast moving clouds, time-lapse sky"],
        "subjects": [
            {"name": "striped_awning", "box": [0.308, 0.0699, 0.6806, 0.4031], "force_repair": True,
             "phrase": "the long striped awning stretched on its ropes over the warehouse front, its "
                       "cloth lifting and sagging in the harbour breeze and its fringed edge stirring"},
            {"name": "awning_rope", "box": [0.63, 0.22, 0.71, 0.58],
             "phrase": "the slack rope hanging from the awning's corner, swinging slightly and settling"},
            {"name": "harbour_water", "box": [0.0, 0.40, 0.22, 0.64],
             "phrase": "the blue harbour water beyond the quay wall, its surface glittering and shifting "
                       "in place"},
            {"name": "trough_water", "box": [0.575, 0.70, 0.735, 0.86],
             "phrase": "the water standing in the long stone trough, its surface trembling and settling"},
            {"name": "morning_cloud", "box": [0.0, 0.0, 1.0, 0.30],
             "phrase": "the bright morning cloud over the harbour, rolling and folding slowly in place"},
        ],
    },
    # ── the wine market at hard midday: cloth is the only thing that moves in that heat ────────────
    "market_price": {
        "rigid": STREET_RIGID,
        "has_document": True,
        "pinned": ["The tall chalked price-board, the dark board on the counter and the open ledger lie "
                   "exactly as they are: their chalked columns, figures and lettering do not move, "
                   "smudge, lift, curl or change."],
        "negatives": [", people, fast moving clouds, time-lapse sky, the awning tearing, stalls collapsing"],
        "subjects": [
            {"name": "hanging_cloths", "box": [0.7173, 0.0901, 0.8277, 0.9167],
             "phrase": "the long dyed cloths hanging from the line, swaying and turning heavily on the "
                       "hot air, their lower edges lifting and falling"},
            {"name": "canopy_fringe", "box": [0.28, 0.10, 0.70, 0.36],
             "phrase": "the great stall canopy overhead, its sun-bleached cloth breathing slightly and "
                       "its knotted fringe swinging along the lower edge"},
            {"name": "hanging_herbs", "box": [0.695, 0.09, 0.765, 0.31],
             "phrase": "the bunches of dried herbs strung up beside the cloths, turning slowly where they hang"},
            {"name": "harbour_water", "box": [0.30, 0.50, 0.56, 0.62],
             "phrase": "the harbour water below the market, glittering hard under the midday sun and "
                       "shifting in place"},
            {"name": "side_awnings", "box": [0.03, 0.36, 0.21, 0.56],
             "phrase": "the pale awnings over the stalls down the row, their cloth sagging and lifting gently"},
        ],
    },
    # ── the boast stall in the early afternoon: the brazier smokes ─────────────────────────────────
    # ── the boast stall in early afternoon ────────────────────────────────────────────────────────
    # RE-CUED 2026-09-04. Lucas on the base clip: "the kettle itself is moving, needs fixing." Same
    # authored fault as canopic's fountain, and the same two halves of it:
    #   * THE BOX. `brazier_smoke` was [0.5475, 0.0162, 0.7394, 0.8441] — nineteen percent of the frame,
    #     top edge in the awning and bottom edge on the paving, containing the amphora stack, the stall
    #     post, the wall and the whole bronze cauldron. Drawn on the STRUCTURE, not on the substance.
    #   * THE PHRASE. It opened "the cauldron on its brazier beside the counter" — the cauldron NAMED as
    #     the moving subject, in a box big enough to move it. The artefact was in the phrase again.
    # The box is now the smoke COLUMN above the pot mouth and nothing else, and the phrase names smoke.
    #
    # THE PIN WAS THE WRONG INSTRUMENT AND IS GONE (second pass, same day). The first fix pinned the
    # cauldron and its stand in the playback mask, which stopped the heaving by stopping the pot dead —
    # and a dead pot is not what the room wants. Lucas: "the kettle in market boast was supposed to be
    # ALIVE, just stationary." A pin cannot express that distinction. It is a per-pixel freeze, so it
    # takes the coal glow and the firelight on the bronze along with the wobble.
    # The pot is therefore held by the PROMPT instead — named in `rigid`, with an explicit "does not
    # rise, sink, swell, rock, swing" line and matching negatives — while what is genuinely alive about
    # a cooking pot is named as its own subject: the COALS breathing under it and the firelight moving
    # on its belly. Both are light, the one category that can be lively without anything travelling.
    # (The night state has carried a `brazier_coals` subject all along; the day state simply never did.)
    # The repair TILE is dropped too. It was rendered for the old giant box, so it pasted the moving
    # cauldron back in; and it made the smoke WEAKER, not stronger (p95 29.7 in the raw render, 16.4
    # after the tile). The raw render's smoke needs no repair.
    "market_boast": {
        "rigid": STREET_RIGID + ", and the great pyramid of stacked amphorae behind the counter, and the "
                                "bronze cauldron, its hanging bail, its iron tripod and the brazier under it",
        "has_document": True,
        "pinned": ["The hanging reject-slate and the open ledger on the counter lie exactly as they are: "
                   "their chalked marks, ruled lines and lettering do not move, smudge, lift, curl or change.",
                   "The great pyramid of stacked amphorae is solid and fixed: no jar shifts, rocks, "
                   "rolls or falls.",
                   "The bronze cauldron and the brazier beneath it are heavy metal standing on stone: "
                   "they do not rise, sink, swell, rock, swing or breathe, and they do not change "
                   "shape or size. Only the fire, the smoke and the light on them move."],
        "negatives": [", people, amphorae falling, the stack collapsing, fire spreading, the stall burning, "
                      "the cauldron rising or sinking, the pot swelling or shrinking, the cauldron rocking "
                      "or swinging, the brazier moving, metal heaving or bulging"],
        "subjects": [
            {"name": "brazier_smoke", "box": [0.608, 0.225, 0.732, 0.630],
             "phrase": "a thin column of smoke standing above the mouth of the cauldron, thickening and "
                       "thinning and curling over on itself in place"},
            {"name": "brazier_coals", "box": [0.626, 0.786, 0.706, 0.884],
             "phrase": "the bed of coals in the brazier under the pot, breathing from dull red to bright "
                       "orange and back as the draught takes them"},
            {"name": "cauldron_sheen", "box": [0.628, 0.646, 0.706, 0.792],
             "phrase": "the firelight on the belly of the bronze cauldron, its highlights swelling and "
                       "fading with the coals below while the metal itself never stirs"},
            {"name": "hanging_drape", "box": [0.565, 0.0, 0.645, 0.32],
             "phrase": "the heavy red drape hung at the end of the stall, stirring and settling against "
                       "the post"},
            {"name": "counter_cloths", "box": [0.32, 0.66, 0.53, 0.92],
             "phrase": "the cloths thrown over the front of the counter, their loose ends lifting slightly "
                       "in the afternoon air"},
            {"name": "stall_canopy", "box": [0.08, 0.0, 0.60, 0.16],
             "phrase": "the worn canopy overhead, its cloth breathing slowly between the poles"},
            {"name": "sea_beyond", "box": [0.0, 0.44, 0.16, 0.64],
             "phrase": "the sea beyond the parapet, its surface glittering and shifting in place"},
        ],
    },
    # ── the Canopic Way in late afternoon: the WATER, and nothing else ────────────────────────────
    # RE-CUED 2026-09-02. Lucas on the first base clip: "the whole fountain is moving up and down in a
    # bizarre way. It really should just be the water." Both causes were authored, and both are the
    # textbook failures in `cinemagraph_tools/AGENTS.md`:
    #   * THE BOX. `fountain_basin` was [0.3505, 0.1597, 0.6054, 0.8588] — drawn on the whole fountain
    #     STRUCTURE. Its top edge sat in the sky above the back wall and its bottom on the pavement, so
    #     the phrase "its surface breaking into rings" named the wall, the lion and the bowl as a water
    #     surface. It is now the water ELLIPSE INSIDE THE RIM and nothing else.
    #   * THE PHRASE. It ended "so the reflected colonnade buckles and settles again" — an explicit
    #     request to buckle the colonnade, while `rigid` in the same prompt declared the colonnade
    #     fixed. Given a contradiction and a box spanning the masonry, the model heaved the fountain.
    #     The artefact was literally in the phrase.
    # `lion_spout` was boxed on the lion's HEAD (a bronze sculpture) with only the top of the jet; it is
    # now the falling jet, from the mouth to the splash.
    # DROPPED: `basin_spill` (thin films on the bowl face — a box that is ~80% stone, sitting exactly
    # where the heaving was worst, and it measured DEAD at 2.87 anyway), `afternoon_cloud` and
    # `low_sun`. Lucas: "just the water ... that's basically it for the Canopic Way."
    "canopic": {
        "rigid": STREET_RIGID + ", the temple, the shrine and the colonnade, and the fountain itself — "
                                "its carved lion, its stone rim, bowl, plinth and the paving around it",
        "negatives": [", people, the fountain overflowing, water flooding the paving, fast moving clouds, "
                      "time-lapse sky, the fountain rising or sinking, the basin swelling or shrinking, "
                      "stonework heaving, breathing or bulging, the lion's head moving"],
        "subjects": [
            # Both measured DEAD on the earlier night pass (lion spout 3.26, basin 3.81) and needed
            # repair tiles. Forced, so a human verdict is not required to get them tiled.
            {"name": "lion_spout", "box": [0.450, 0.428, 0.485, 0.605], "force_repair": True,
             "phrase": "the jet of water falling from the carved lion's mouth into the basin below, "
                       "unbroken and glinting as it falls"},
            {"name": "fountain_basin", "box": [0.372, 0.542, 0.578, 0.618], "force_repair": True,
             "phrase": "the water surface in the fountain basin, breaking into small rings where the jet "
                       "lands and settling flat again"},
        ],
    },
    # ── the Great Library at dusk: RE-AUTHORED 2026-09-03 for the rebuilt hall ───────────────────
    # The room was rebuilt (bigger, wrapped, crowded, water-clock + veils) so the old one-dust-subject
    # spec no longer describes it. Drafted from BOTH required inputs: the committed `library/scene.png`
    # opened and looked at, and the room's stored `authoring.scenePrompt`.
    #
    # WHAT CHANGED THE MOTION PICTURE. The old hall had no legitimate mover at all, which is why it
    # animated the paper (see `cinemagraph_tools/AGENTS.md`). This one has two genuinely large, soft,
    # near-field movers — the linen veils and a broad near shaft — so the model is no longer starved.
    # The starvation, not the subject count, was the fault.
    #
    # THE WATER IS THE WEAK ONE, and it is worth saying so before the render rather than after. Lucas
    # asked for the clepsydra as a hero and visually it is one, but the falling ribbon measures ~12 px
    # wide on the panorama — the "thin far smoke = 2.4 DEAD" class from SCENE_SPEC_GUIDE rule 3a. Its
    # box is widened to take the ribbon AND the tank mouth it lands in, and it is force-repaired so the
    # tile pass gets its shot, but expect DEAD or WEAK. The room does not depend on it.
    "library": {
        # Inherited verbatim by the night state (see `build`), so nothing here may contradict a hall
        # full of deliberately burning lamps: name the SHEETS on the desks, never the desks' contents
        # wholesale, and never the lamps.
        "rigid": ("The hall walls, columns, vaulting, galleries, ladders, scroll-niches and their "
                  "scrolls, the water-clock's dial, pointer, tank, gearing and plinth, the desks and "
                  "the ledgers, scrolls, wax tablets and loose sheets lying on them, the baskets, "
                  "carts and crates, and the floor"),
        "has_document": True,
        # The two prose pins that used to sit here are gone: the generated pin sentence in
        # `library_pins` says the same thing once, more completely, and saying it three times only
        # weights the prompt without holding a single page (`cinemagraph_tools/AGENTS.md` — a fourth
        # "please don't" is the move that does not work; the mask is what holds paper).
        "pinned": [],
        # HARD anti-paper negative, at Lucas's direction (2026-09-04): "negative prompting on paper,
        # scrolls, books". `has_document` already appends NEG_PAPER (curling, page turning, text
        # moving); this names the things NEG_PAPER does not — the rolled scroll ENDS packed in the
        # niches, the stacks, the carts, the shelving itself — because those are what this hall is
        # made of and what the render was actually churning.
        "negatives": [", people, pages turning, pages fluttering, pages lifting, paper moving, "
                      "sheets shifting, loose sheets sliding, books opening or closing, codices "
                      "moving, ledgers moving, scrolls unrolling, scrolls rocking, scrolls rolling, "
                      "scrolls falling, scroll ends swelling, scroll stacks shifting, scroll racks "
                      "changing, shelving moving, the niches rearranging, the clock dial or its "
                      "pointer turning, the clock swaying, fast moving clouds"],
        "subjects": [
            # `window_veils` was the day room's strongest mover (p95 20.9) and is now PINNED with the
            # rest of the paper — see LIB_VEILS above for why, and for how to put it back.

            {"name": "dusk_shaft", "box": [0.646, 0.068, 0.710, 0.330], "force_repair": True,
             "phrase": "the broad shaft of last gold light standing in the high arched window, its fine "
                       "dust turning and settling very slowly inside the beam"},
            {"name": "clock_water", "box": [0.308, 0.330, 0.345, 0.432], "force_repair": True,
             "phrase": "the thin ribbon of water falling from the water-clock's upper cistern into the "
                       "graduated tank below, and the water trembling where it lands"},
            # MOVERS then PINS, both generated from one list — see `library_movers`. The movers are
            # the cloth and the lights and nothing else; everything the movers do not claim plays its
            # still, so the paper cannot move even if the render tries.
        ] + library_movers("base") + library_pins("base"),
    },
    # ── the skiff at nightfall: open water, and the Pharos burning ─────────────────────────────────
    "boat": {
        "rigid": ("The skiff's hull, thwarts, gunwales and oars, the distant tower, the city and the "
                  "moored ships"),
        "negatives": [", the boat moving forward, rowing, the boat sailing, a storm, waves breaking over "
                      "the boat, rain"],
        "subjects": [
            {"name": "pharos_flame", "box": [0.478, 0.01, 0.528, 0.17], "force_repair": True,
             "phrase": "the great signal fire burning at the summit of the Pharos, its flame leaping and "
                       "guttering, throwing hard gold light down the tower's head"},
            {"name": "flame_reflection", "box": [0.45, 0.42, 0.56, 0.68],
             "phrase": "the long broken reflection of that fire lying across the black water, its gold "
                       "shattering and re-forming as the surface moves"},
            {"name": "open_sea", "box": [0.0, 0.44, 1.0, 0.76],
             "phrase": "the open harbour at night, a real chop running across it, wave-tops rising and "
                       "falling in place and catching the light"},
            {"name": "bow_lamp", "box": [0.3603, 0.45, 0.4224, 0.7704],
             "phrase": "the lantern hung at the skiff's bow, its flame live behind the glass, its light "
                       "swinging the smallest amount over the wet timbers"},
            {"name": "city_lights", "box": [0.60, 0.26, 0.99, 0.50],
             "phrase": "the lit windows and quay lamps along the far shore, each one breathing and "
                       "steadying, their reflections trembling on the water below"},
        ],
    },
    # ── the lantern gallery: the sealed door, and the light getting out around it ──────────────────
    # ── the lantern gallery's outer parapet ──────────────────────────────────────────────────────
    # RE-CUED 2026-09-04. Lucas: "in the base for pharos, the water is moving too quickly." Two causes,
    # and the box is again half the story:
    #   * THE BOX. `sea_and_rocks` was [0.84, 0.40, 1.0, 0.96] — its own name admits it. Drawn on the
    #     whole lower-right quarter, it is roughly half CLIFF: the rock spur, the boat, the mooring lamp
    #     and the shelf the parapet stands on all sat inside a region the phrase called "the black sea".
    #     Split into the three parts that are actually water.
    #   * THE PHRASE. "the black sea WORKING AGAINST the rocks ... white water RISING and falling" is a
    #     surf phrase, and the render answered with surf: whole foam patterns appearing and vanishing
    #     between consecutive frames. Every water phrase here now asks for one long slow rhythm, and the
    #     negatives name speed directly, which nothing in the scheme had done before.
    # The rocks join `rigid` — TOWER_RIGID never mentioned them, so the biggest object in the frame's
    # lower half was undeclared.
    "pharos": {
        "rigid": TOWER_RIGID + ", and the cliff, the rock spur below the parapet, the mooring lamp and "
                               "the moored boat",
        "has_document": True,
        "pinned": ["The bronze relief panel beside the door is fixed: its carved symbols and marks do not "
                   "move, shift, glow in sequence or change.",
                   "The great bronze door stays SHUT and does not move, swing or open."],
        "negatives": [", the door opening, the door swinging, people, rain, storm, lightning, "
                      "fast water, rushing water, churning surf, breaking waves, crashing spray, "
                      "foam surging, rapid ripples, choppy water, boiling water, time-lapse water, "
                      "waves at the shore, surf around the rocks, water slapping the boat, "
                      "the rocks moving, the cliff shifting, flashing, strobing, pulsing light, "
                      "throbbing glow, flickering brightness, the scene brightening and darkening, "
                      "exposure changing, the whole image getting lighter or darker, "
                      "light washing across the stone"],
        # MOVERS then PINS, both generated from one list — see `pharos_movers` above.
        "subjects": pharos_movers() + pharos_pins(),
    },
    # ── the lamp chamber: the fire itself, which is the whole point of the building ────────────────
    "lantern": {
        "rigid": TOWER_RIGID + ", and the iron fire-basket, the bronze mirror-shell and the gearing",
        "negatives": [", the fire going out, the fire spreading, the basket tipping, people, rain, the "
                      "mirror turning, the gears turning"],
        "subjects": [
            {"name": "signal_fire", "box": [0.38, 0.03, 0.60, 0.68],
             "phrase": "the great signal fire standing in its iron basket, flames climbing and falling "
                       "back, sparks rising off the top and dying, the whole light of the room pulsing "
                       "with it"},
            {"name": "mirror_flare", "box": [0.4603, 0.0071, 0.6151, 0.7141],
             "phrase": "the huge bronze mirror-shell behind the fire, the hot reflected flare sliding and "
                       "flickering across its beaten surface as the flames move"},
            {"name": "chamber_smoke", "box": [0.73, 0.18, 0.88, 0.68],
             "phrase": "the smoke lifting off the fire and drifting out through the seaward arch, curling "
                       "and thinning as it goes"},
            {"name": "sea_beam", "box": [0.6477, 0.1717, 0.8077, 0.7217],
             "phrase": "the beam of light reaching away over the black water beyond the arch, its edge "
                       "trembling, the distant city lights breathing below it"},
        ],
    },
}


# ── NIGHT ─────────────────────────────────────────────────────────────────────────────────────────
# A variant's spec lives at `motionSpec.states.<state>` (cine_scenario.states_to_run). Authored the same
# way as the base — each night panorama opened and looked at — and they are NOT the day spec with the
# words changed: night reverses which things move. By day the sky and the water carry the scene and the
# lamps are incidental; after dark the lamps ARE the scene, the water's job is to hold their reflections,
# and the sky goes quiet. Every night room therefore names its lamps FIRST and its sky last, and the
# reflections are named as their own subjects because a reflection can be dead while its source burns.
# The rigid lists, the document pins and the negatives carry over unchanged — a door that must not move
# by day must not move by night either.
NIGHT = {
    # RE-CUED 2026-09-04. Lucas on the night clip: "shows a single wave going into the ship." Three
    # authored faults, all of them geometry and wording, none of them the model:
    #   * THE WATERLINE CROSSES THE BOX DIAGONALLY. `night_sea` was [0.0, 0.46, 0.36, 0.76] — one
    #     rectangle over water whose lower boundary is the ship's own bulwark, and that rail RISES from
    #     y=0.786 at the left edge to y=0.679 at x=0.36 as it comes toward the viewer. So the bottom of
    #     that rectangle was hull and wet deck planking for most of its width, and the phrase called all
    #     of it "the dark harbour". Identical to canyon/undercroft's floodwater over the walkway.
    #     It is now THREE boxes that each stop clear above the rail where they sit.
    #   * A TRAVEL WORD. "only a slow swell MOVING under the reflections" asks for net travel, which a
    #     two-ended loop cannot express, and the fight reads as exactly one wave crossing the frame.
    #     Every phrase here is now motion IN PLACE.
    #   * `flame_track` WAS NOT ON THE WATER. [0.27, 0.48, 0.32, 0.60] sits on the Pharos mole itself —
    #     the fort, its rocks and its masonry — while the phrase called that region a reflection lying
    #     on the harbour. The gold reflections are below it, y 0.55-0.73. Named a moving water surface
    #     over stone; the same mistake as calling a wet walkway floodwater.
    # The hull, rail and deck are now PINNED as well, following the rail's slope in three steps. This is
    # the belt to the braces: a wave cannot run into the ship if the ship plays its still.
    "deck": [
        {"name": "pharos_flame", "box": [0.272, 0.17, 0.318, 0.29], "force_repair": True,
         "phrase": "the signal fire burning at the head of the distant Pharos, a hot gold flame leaping "
                   "and guttering against the black sky"},
        {"name": "flame_track", "box": [0.225, 0.548, 0.290, 0.694],
         "phrase": "the broken gold reflections lying on the black water below the lit mole, glinting "
                   "and re-forming where they lie without travelling"},
        {"name": "flame_track_far", "box": [0.292, 0.548, 0.332, 0.668],
         "phrase": "the broken gold reflections lying on the black water below the lit mole, glinting "
                   "and re-forming where they lie without travelling"},
        {"name": "moon_track", "box": [0.046, 0.516, 0.088, 0.694],
         "phrase": "the silver track the moon lays on the water, its scales breaking and closing again "
                   "in place"},
        {"name": "deck_lamp", "box": [0.648, 0.80, 0.695, 0.95],
         "phrase": "the lamp burning in the open deck hatch, its flame live behind the horn, its warm "
                   "light breathing over the timbers"},
        {"name": "city_lights", "box": [0.62, 0.26, 0.99, 0.62],
         "phrase": "the lit windows and quay lamps of the city along the shore, each small light "
                   "breathing and steadying, their reflections trembling on the water beneath"},
        {"name": "night_sea_west", "box": [0.000, 0.520, 0.044, 0.694],
         "phrase": "the dark harbour water wrinkling and settling where it lies, its surface never "
                   "travelling and never rolling toward the ship, only trembling in place under the "
                   "reflections"},
        {"name": "night_sea_mid", "box": [0.090, 0.520, 0.222, 0.694],
         "phrase": "the dark harbour water wrinkling and settling where it lies, its surface never "
                   "travelling and never rolling toward the ship, only trembling in place under the "
                   "reflections"},
        # THE SHIP, pinned in the playback mask. The rail rises toward the viewer, so the pin follows it
        # in three steps rather than as one rectangle — the same reason the water needed three.
        {"name": "hull_west", "box": [0.000, 0.780, 0.150, 1.000], "still": True,
         "phrase": "The ship's bulwark, rail and deck planking are solid timber and completely still: "
                   "no water crosses them, breaks over them or runs up them."},
        {"name": "hull_mid", "box": [0.150, 0.745, 0.300, 1.000], "still": True},
        {"name": "hull_fore", "box": [0.300, 0.690, 0.470, 1.000], "still": True},
    ],
    "quay": [
        {"name": "pharos_flame", "box": [0.498, 0.27, 0.532, 0.37], "force_repair": True,
         "phrase": "the fire burning at the head of the Pharos out on its mole, a hot point of gold "
                   "flame flaring and settling"},
        {"name": "flame_track", "box": [0.495, 0.54, 0.535, 0.92],
         "phrase": "the long gold reflection of that fire running towards the steps across the black "
                   "water, breaking and re-forming"},
        {"name": "ship_lantern", "box": [0.158, 0.58, 0.196, 0.70],
         "phrase": "the lantern hung at the moored ship's rail, its flame live, its light swinging the "
                   "smallest amount over the wet stone"},
        {"name": "quay_lamps", "box": [0.78, 0.50, 0.92, 0.74],
         "phrase": "the oil lamps burning under the great arch and along the quay, their pools of warm "
                   "light breathing on the wet flagstones"},
        {"name": "harbour_water", "box": [0.0, 0.52, 1.0, 0.74],
         "phrase": "the black harbour water lapping along the quay stones, its surface wrinkling and "
                   "settling and carrying every reflection with it"},
        {"name": "bunting", "box": [0.20, 0.46, 0.40, 0.56],
         "phrase": "the strung bunting between the boats' masts lifting and falling in the night air"},
    ],
    "emporion": [
        {"name": "portico_lamps", "box": [0.39, 0.19, 0.77, 0.46], "force_repair": True,
         "phrase": "the row of hanging oil lamps burning the length of the warehouse portico, each flame "
                   "live and wavering, their warm pools breathing on the columns and the stacked jars"},
        {"name": "striped_awning", "box": [0.308, 0.0699, 0.6806, 0.4031], "force_repair": True,
         "phrase": "the long striped awning over the warehouse front, lit from beneath by the lamps, its "
                   "cloth lifting and sagging and its fringed edge stirring"},
        {"name": "pharos_flame", "box": [0.115, 0.30, 0.150, 0.50],
         "phrase": "the fire at the head of the distant Pharos, flaring and settling, laying a broken "
                   "gold line on the water below it"},
        {"name": "trough_water", "box": [0.575, 0.70, 0.735, 0.86],
         "phrase": "the water standing in the long stone trough, its surface trembling and settling, "
                   "holding the lamplight"},
        {"name": "harbour_water", "box": [0.0, 0.40, 0.22, 0.64],
         "phrase": "the dark harbour beyond the quay wall, its surface moving slowly under the moon"},
    ],
    "market_price": [
        {"name": "board_lantern", "box": [0.268, 0.36, 0.312, 0.49], "force_repair": True,
         "phrase": "the lantern hung beside the tall price-board, its flame live behind the glass, its "
                   "light wavering across the chalked face without moving a single mark on it"},
        {"name": "row_lamps", "box": [0.03, 0.39, 0.22, 0.58],
         "phrase": "the small lamps burning at the stalls down the market row, each one breathing and "
                   "steadying, their light lying on the wet paving"},
        {"name": "hanging_cloths", "box": [0.7173, 0.0901, 0.8277, 0.9167],
         "phrase": "the long dyed cloths hanging from the line, swaying and turning heavily in the night "
                   "air, their lower edges lifting and falling"},
        {"name": "hanging_herbs", "box": [0.695, 0.09, 0.765, 0.31],
         "phrase": "the bunches of dried herbs strung beside the cloths, turning slowly where they hang"},
        {"name": "harbour_lights", "box": [0.30, 0.48, 0.72, 0.66],
         "phrase": "the lit windows along the far shore and their long reflections on the black harbour, "
                   "trembling and re-forming"},
    ],
    "market_boast": [
        {"name": "brazier_coals", "box": [0.60, 0.68, 0.74, 0.92], "force_repair": True,
         "phrase": "the bed of coals under the cauldron, glowing hot and dimming and glowing again, "
                   "throwing an unsteady orange light up the stall front"},
        {"name": "brazier_smoke", "box": [0.60, 0.48, 0.72, 0.78],
         "phrase": "the thin column of smoke lifting off the cauldron and curling away into the dark"},
        {"name": "counter_lantern", "box": [0.288, 0.56, 0.342, 0.70],
         "phrase": "the lantern standing on the counter beside the ledger, its flame live, its light "
                   "breathing over the jars behind it"},
        {"name": "counter_lamp", "box": [0.518, 0.60, 0.582, 0.70],
         "phrase": "the small open lamp further along the counter, its flame wavering and settling"},
        {"name": "hanging_drape", "box": [0.585, 0.0, 0.665, 0.32],
         "phrase": "the heavy drape hung at the end of the stall, stirring and settling against the post"},
    ],
    # NIGHT CARRIES THE SAME TWO WATER SUBJECTS, and carried the same two defects — the boxes were drawn
    # on the fountain STRUCTURE and the basin phrase asked for the reflection to "buckle and settle".
    # Corrected here to the same water-only boxes as the day spec (verified against `scene_night.png`:
    # the night wash is a re-light of the same view, so the geometry is identical). The night clip has
    # not been rendered yet, so this costs nothing now and would have cost a re-render later.
    # The flame subjects below are UNTOUCHED — they are the part that worked (Lucas, 2026-08-31:
    # "it didn't animate the water but it did animate the little flames/candles everywhere").
    "canopic": [
        {"name": "lion_spout", "box": [0.450, 0.428, 0.485, 0.605], "force_repair": True,
         "phrase": "the jet of water falling from the carved lion's mouth into the basin below, unbroken "
                   "and catching the lamplight as it falls"},
        {"name": "fountain_basin", "box": [0.372, 0.542, 0.578, 0.618], "force_repair": True,
         "phrase": "the water surface in the fountain basin, breaking into small rings where the jet "
                   "lands and settling flat again"},
        {"name": "basin_spill", "box": [0.39, 0.64, 0.63, 0.84], "force_repair": True,
         "phrase": "the thin films of water running down the outside of the basin wall, wet stone "
                   "glistening as they go"},
        {"name": "colonnade_lamps", "box": [0.0, 0.42, 0.32, 0.56],
         "phrase": "the small lamps burning along the colonnade, each flame live, their pools of light "
                   "breathing on the columns and the wet paving"},
        {"name": "shrine_candles", "box": [0.645, 0.48, 0.745, 0.62],
         "phrase": "the candles standing at the foot of the street shrine, their flames guttering and "
                   "steadying before the statue"},
        {"name": "temple_glow", "box": [0.72, 0.26, 0.92, 0.58],
         "phrase": "the warm lamplight standing between the temple columns, breathing slowly"},
    ],
    # RE-AUTHORED 2026-09-03 with the base spec, from the newly generated `scene_night.png` opened and
    # looked at plus the night variant's own delta prompt. Night REVERSES the room: by day the veils and
    # the dust carry it and the lamps are unlit; after dark the hall's own oil lamps are the scene, the
    # window shaft goes cold, and the veils hang pale rather than gold.
    #
    # NIGHT IS PINNED AS HARD AS DAY, and the first draft of this spec was wrong about that. It carried
    # only three pins on the argument that the day hall animated paper because it was STARVED of licit
    # movers, and that a night hall full of lamps would not be. Measuring the previous night clip killed
    # that argument: it had four movers including two sets of flames, and its paper still measured
    # p95 16.2 on the lectern codex, 16.7 on the niche scrolls and 22.3 on the great table — WORSE than
    # the starved day room ever was. Legitimate movers do not protect the paper. Only pins do.
    #
    # PINS AND FLAMES ARE SEPARATED BY GEOMETRY, since a pin is applied last and would freeze a flame
    # that shared its box. Checked against the night panorama at native resolution: the desk lamps'
    # flames all sit ABOVE y=0.566, so the great-desk pin starts there; the near-right lamp sits to the
    # RIGHT of that desk's ledger at x>0.864, so the ledger pin stops at 0.862.
    "library": [
        {"name": "moon_shaft", "box": [0.646, 0.068, 0.710, 0.330], "force_repair": True,
         "phrase": "the pale cold shaft of moonlight standing in the high arched window, its fine dust "
                   "turning and settling very slowly inside the beam"},
        # `window_veils` is pinned in both states — see LIB_VEILS. Night measured it at 7.8, so the
        # night room loses less than the day room does.

        {"name": "clock_water", "box": [0.308, 0.330, 0.345, 0.432], "force_repair": True,
         "phrase": "the thin ribbon of water still falling from the water-clock's upper cistern into the "
                   "graduated tank below, catching the lamplight as it goes"},
        # MOVERS then PINS, both generated — see `library_movers`. `table_lamps` and `desk_lamps_near`
        # are dropped as separate subjects: every practical light in the hall is now a generated lamp
        # mover, so the two desks no longer carry the whole night on their own.
    ] + library_movers("night") + library_pins("night"),
}

def build(room):
    """The full spec for a room, tagged with room/state for the render's filenames."""
    s = dict(SPECS[room])
    s["room"], s["state"] = room, "base"
    if room in NIGHT:
        # The night spec inherits the room's rigid list, document pins and negatives verbatim — what must
        # not move by day must not move by night — and replaces only the subject list.
        s["states"] = {"night": {"rigid": s.get("rigid"), "pinned": s.get("pinned"),
                                 "negatives": s.get("negatives"), "has_document": s.get("has_document"),
                                 "subjects": [dict(x) for x in NIGHT[room]]}}
    return s


def _main():
    write = "--write" in sys.argv
    bad = 0
    for room in SPECS:
        spec = build(room)
        errs = MS.validate(spec)
        print("%-14s %d subjects  %s" % (room, len(spec["subjects"]), "OK" if not errs else "ERRORS"))
        for e in errs:
            print("    ! " + e)
            bad += 1
        if not write or errs:
            continue
        doc = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
        node = next(r for r in doc["rooms"] if r["key"] == room)
        auth = dict(node.get("authoring") or {})
        auth["motionSpec"] = spec
        r = urllib.request.urlopen(urllib.request.Request(
            HARNESS + "/api/room-patch",
            data=json.dumps({"chapter": CHAPTER, "scenario": SCENARIO, "roomKey": room,
                             "fields": {"authoring": auth}}).encode(),
            headers={"Content-Type": "application/json"}), timeout=60)
        print("               written: %s" % json.load(r).get("ok"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_main())
