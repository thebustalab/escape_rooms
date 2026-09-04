#!/usr/bin/env python3
"""_motion_specs.py — beacons' motion specs, authored once and written onto the room nodes.

WHY THIS EXISTS AS A FILE. A motion spec is a judgement about what should move in a scene; it is not
derivable from the art. So the spec lives on the room node (`authoring.motionSpec`) and this script is
the record of how it was authored — re-run it to restore or revise.

RE-AUTHORED 2026-09-03, AGAINST THE CURRENT ART. An earlier set was authored on 2026-09-02 by
`_scratch/make_motion_specs.py`, which was correct at the time and is superseded here for one reason:
it ran at 14:08 and the room network was RE-LAID at 21:32 the same day, after which nine of the twelve
rooms became wholly different places and every base panorama was regenerated on 2026-09-03. Its subject
boxes were localized against art that no longer exists. Nothing was wrong with its method — the world
rules below are inherited from it almost verbatim — only with its inputs.

Each spec here was drafted from BOTH inputs the protocol requires (`cinemagraph_tools/AGENTS.md` →
*Motion prompts are written by Claude, from TWO inputs*): the committed panorama, opened and looked at
this session, room by room; and the room's stored `authoring.scenePrompt`, which resolves WHICH object
is which when the render holds several similar ones and says what was intended where the image renders
it faintly. Boxes are read off the image, not off the prompt's left-to-right `at` phrases — the render
routinely places an object a good way from where the spec asked for it.

THE PINNED SET IS THE INTERESTING PART FOR THIS WORLD, and it is nearly all "do not":

  * THE RIVER IS A LEVEL, NOT AN EVENT. Light and surface may slide; the water never rises, swells,
    floods or spreads. The scenario's danger is a moraine-dammed tarn bursting, and it happens
    OFF-SCREEN and at night. A day clip showing the river swelling gives away the ending and
    contradicts the story.
  * EVERY BEACON FIRE-BASKET IS COLD. The single night image in the whole scenario is four beacons
    burning; a basket that so much as glows here spends that image early. This is a story constraint
    enforced as a motion constraint, and it is the one pin that matters most.
    ⚠️ SCOPE IT TO THE BEACON BASKETS. `whistlegate` is an interior guardroom with a live domestic
    HEARTH — the best mover in the room, and the only legitimate flame in the daytime scenario. A blanket
    "no fire anywhere" pin, which the superseded set carried, would have frozen it.
  * THE SNOWFIELDS DO NOT AVALANCHE. Two rooms name blown snow as a subject (`broken_tooth`'s banner off
    the massif, `spindle`'s spindrift off the needle) and blowing snow is one bad phrase away from a
    sliding snow-mass. Both are worded as a banner that streams and dissipates, and both rooms pin the
    slope itself.
  * PAPER DOES NOT LIFT. Every room but one carries a ledger, a filed dispatch bundle or a weighted linen
    survey sheet, and the survey sheet is the escape's own instrument. `has_document` on all twelve.

WHAT IS AND ISN'T NAMED. Only oscillatory phenomena — water surfaces, flame, smoke, cloud, blown snow,
grass. The recipe pins frame 0 and frame -1 to the same still, so a two-ended loop cannot express net
travel; naming anything that must GO somewhere only starts a fight the end guide wins. That is why the
`sisters` cloud-river "pours and shreds" in place rather than crossing the saddle, and why `kiln`'s
banner "streams and re-forms" rather than blowing away.

THIS IS A BRIGHT, HARD, STILL WORLD AND THE SUBJECT COUNTS ARE HONESTLY LOW. Hard high-altitude sun in
a clear deep-cobalt sky gives no drifting cloud shadows and no dusk ramp. `anvil` and `kiln` carry two
movers each, and that is the correct answer for a bare pavement summit and a bare red dome — padding
them would mean naming something that is not there, which is how a stabiliser starts inviting the model
to draw it (the failure `make_motion_specs.py` caught when a shared tower string named a parapet and a
fuel-store inside an interior guardroom).

  python3 _motion_specs.py            # validate + render every prompt, write nothing
  python3 _motion_specs.py --write    # write authoring.motionSpec onto each room node
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "cinemagraph_tools"))
import motion_spec as MS  # noqa: E402

P = os.path.join(HERE, "scenario.json")

# ── the world's shared pins ────────────────────────────────────────────────────────────────────────
PIN_RIVER = ("The river is a fixed level: it does not rise, swell, flood, spread or advance, and its "
             "channels stay exactly in their present courses on the gravel.")
PIN_SNOW = ("The snowfields, glaciers and ridgelines are fixed: no avalanche, no sliding snow-mass, no "
            "falling rock, no collapse.")
PIN_BASKET = ("The open iron fire-basket is COLD, empty and unlit — no flame, no ember, no glow and no "
              "smoke rises from it, and no fire appears anywhere on the range.")
PIN_PAPER = ("The dispatch ledgers, filed dispatch copies and the folded linen survey sheet lie flat and "
             "still under their weights; no page lifts, curls, turns, flutters or changes.")

# ⚠️ TWO WORDS WERE REMOVED FROM THIS LIST AFTER READING THE COMPOSED PROMPTS (2026-09-03), which is
# the only place either collision was visible — the subject tables looked fine:
#   * "banners" (meant as flags/pennants) fought `broken_tooth`'s wind-blown powder banner and `kiln`'s
#     banner cloud, both of which are the hero subject of their room. Narrowed to flags/pennants/bunting.
#   * "smoke where none is lit" (meant to stop a beacon smoking) sat in the same list as `fenwatch`'s
#     chimney plume and `whistlegate`'s hearth smoke. The job is already done precisely by PIN_BASKET,
#     which says no smoke rises from the BASKET, and by the per-room "lit beacon" negative.
NEG_WORLD = (", rising water, flooding, water level changing, surging water, waves, splashing, "
             "churning water, avalanche, sliding snow, falling rock, collapsing rock, people, figures, "
             "walking, animals running, birds, flags, pennants, bunting, boats")
NEG_FIRE = ", fire, flame, embers, glow, ignition, sparks, firelight, lit beacon"

# ── the specs ─────────────────────────────────────────────────────────────────────────────────────
SPECS = {
    # ── RUNG 1 · the valley station: dawn mist on the bars, one working chimney ──────────────────
    "fenwatch": {
        "rigid": ("The long stone office and its slate roof, the propped shutters and the writing-desk, "
                  "the sorting bench under its lean-to and its pigeonholes, the drystone yard wall and "
                  "the open yard gate, the water butt and its dipper, the barrow of kindling, the "
                  "flagged yard, the wading stakes and drying racks out on the bars, and the ridgelines "
                  "and snowfields"),
        # NO MAST HERE. The art prompt's negatives say this station carries no tower, and the render has
        # none — the timber uprights at the extreme edges are the gate posts. The superseded spec named
        # "the timber signal mast and its stone plinth", i.e. an object not in the frame.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_PAPER,
                   "The bundled correspondence in the sorting-bench pigeonholes and the stacked wicker "
                   "trays stay exactly as they are stacked."],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "valley_mist", "box": [0.02, 0.30, 0.40, 0.52],
             "phrase": "the low band of dawn mist lying waist-deep along the braided river, breathing "
                       "slowly in place over the pale gravel bars and thinning and thickening where it "
                       "breaks around the drystone windbreaks"},
            {"name": "chimney_smoke", "box": [0.55, 0.12, 0.74, 0.48],
             "phrase": "a broad soft plume of woodsmoke rolling low and heavy off the office chimney and "
                       "out over the cold slates, curling and settling as it goes"},
            {"name": "river_glint", "box": [0.10, 0.41, 0.35, 0.52],
             "phrase": "the milk-jade meltwater sliding between the gravel bars where the mist thins, "
                       "the light travelling slowly down the open channels"},
            {"name": "desk_ledgers", "box": [0.44, 0.62, 0.64, 0.72], "still": True},
        ],
    },

    # ── the knife-edge fin: spindrift off the needle, the green basin far below ──────────────────
    "spindle": {
        "rigid": ("The dry-laid stone platform, the narrow rock fin and its crest, the pale tapering "
                  "needle, the iron fire-basket and its stone-lidded fuel box, the brass spyglass and "
                  "its folding tripod, the walking paths, and the long smooth snow-slopes to either side"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "needle_spindrift", "box": [0.24, 0.03, 0.37, 0.32],
             "phrase": "a fine banner of spindrift streaming off the needle's edge into the cobalt sky, "
                       "feathering out and re-forming against the rock without ever leaving it"},
            {"name": "basin_river", "box": [0.40, 0.52, 0.66, 0.82],
             "phrase": "the single sinuous river winding through the soft green basin far below, its "
                       "surface catching and losing the light in slow travelling patches"},
            {"name": "ridge_grass", "box": [0.63, 0.52, 0.86, 0.74],
             "phrase": "the bleached straw grass along the ridge combed and released by the wind in slow "
                       "shallow waves"},
            {"name": "survey_sheet", "box": [0.55, 0.86, 0.66, 1.0], "still": True},
        ],
    },

    # ── the closed cirque: a black tarn and meltwater off the horn, everything else in shadow ────
    "rams_head": {
        "rigid": ("The horned outcrop and the dark curving cirque wall, the dry-laid platform and its "
                  "rubble shelf, the iron fire-basket on its plinth, the timber fuel-store and its "
                  "stacked cordwood, the wicker basket, the brass spyglass on its boulder, and the one "
                  "path dropping south out of the cirque mouth"),
        "has_document": True,
        "pinned": [PIN_SNOW, PIN_BASKET, PIN_PAPER,
                   "The lace of unmelted ice rimming the tarn is fixed: it does not melt, spread, break "
                   "up or drift.",
                   "The long-haired goats on the near slopes are motionless — they do not walk, graze, "
                   "turn, startle or change shape."],
        "negatives": [NEG_WORLD + NEG_FIRE + ", melting ice, breaking ice, drifting ice floes"],
        "subjects": [
            {"name": "tarn_surface", "box": [0.26, 0.58, 0.49, 0.80],
             "phrase": "the small black tarn filling the floor of the cirque, its dark open surface "
                       "stirring with the faintest slow ripple and the light shifting across its skin"},
            {"name": "horn_meltwater", "box": [0.12, 0.33, 0.23, 0.57],
             "phrase": "thin meltwater running out of the shadowed underside of the horned outcrop and "
                       "down the wet streaked rock in slender wavering threads"},
            {"name": "gap_grass", "box": [0.60, 0.52, 0.73, 0.66],
             "phrase": "the bleached grass on the open slopes at the cirque mouth stirring gently in the "
                       "draught coming up through the gap"},
            {"name": "survey_sheet", "box": [0.59, 0.76, 0.68, 0.87], "still": True},
        ],
    },

    # ── RUNG 2 · the wind-tunnel notch: a river of cloud forced through the saddle ────────────────
    "sisters": {
        "rigid": ("The two leaning cairns of stacked slate, the flat pale reading-slab on its low stones, "
                  "the iron fire-basket on its plinth, the brass spyglass and its folding tripod, the "
                  "flagged platform, the zigzag paths, the flat-topped summit block on the skyline, and "
                  "the wind-packed saddle snow rising on either hand"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER,
                   "The cairns are solid stacked stone: no slab shifts, slides, topples or settles."],
        "negatives": [NEG_WORLD + NEG_FIRE + ", cloud crossing the frame, weather front moving through, "
                      "time-lapse sky, fast moving clouds"],
        "subjects": [
            {"name": "cloud_river", "box": [0.44, 0.24, 0.64, 0.66],
             "phrase": "the dense white river of cloud forced up out of the eastern valley and spilling "
                       "over the lip of the notch, boiling slowly and shredding to nothing as it falls "
                       "down the western side, always pouring and never crossing the frame"},
            {"name": "west_river", "box": [0.24, 0.46, 0.38, 0.74],
             "phrase": "the single sinuous river far below on the western side, a thin bright thread "
                       "with the light sliding slowly along it"},
            {"name": "west_grass", "box": [0.10, 0.60, 0.26, 0.80],
             "phrase": "the pale grass and scree slope on the western side of the notch stirring in the "
                       "draught pulled through the gap"},
            {"name": "slab_ledger", "box": [0.42, 0.71, 0.55, 0.83], "still": True},
        ],
    },

    # ── the overhung hood: a sea of cloud filling the valley, one island of village showing ──────
    "hood": {
        "rigid": ("The great overhanging hood of pale rock and its underside, the flagged platform, the "
                  "iron fire-basket on its drystone plinth, the timber fuel-store and its stacked "
                  "cordwood, the brass spyglass and its folding tripod, the paths, the twin standing "
                  "stones on the far ridge, and the snow-capped range along the horizon"),
        "has_document": True,
        "pinned": [PIN_SNOW, PIN_BASKET, PIN_PAPER,
                   "The slate roofs of the village showing through the cloud stay exactly where they "
                   "are, and no roof, wall or field boundary shifts."],
        "negatives": [NEG_WORLD + NEG_FIRE + ", cloud crossing the frame, time-lapse sky, fast moving "
                      "clouds, the cloud sea rising to swallow the village"],
        "subjects": [
            {"name": "cloud_sea", "box": [0.10, 0.42, 0.68, 0.80],
             "phrase": "the vast sea of cloud filling the valley below, its surface breathing and "
                       "billowing slowly in place, tongues of it curling up and settling back without "
                       "ever rising to cover the island of ground showing through"},
            {"name": "cloud_edge_right", "box": [0.68, 0.44, 0.86, 0.62],
             "phrase": "the ragged eastern edge of the cloud sea working slowly against the rock spur, "
                       "thinning and re-forming where it touches"},
            {"name": "ridge_grass", "box": [0.80, 0.40, 0.93, 0.55],
             "phrase": "the thin straw grass along the sunlit ridge above the cloud moving gently in the "
                       "wind off the tops"},
            {"name": "survey_sheets", "box": [0.72, 0.86, 0.83, 1.0], "still": True},
        ],
    },

    # ── the ladder: a waterfall beside the climb, the glacier trough below ───────────────────────
    "ladder": {
        "rigid": ("The timber ladder and its rungs, the dark wet rock walls, the stone-and-timber "
                  "fuel-store, its plank door and its stacked cordwood, the iron fire-basket, the brass "
                  "spyglass and its folding tripod, the flagged shelf, the cut stone steps climbing "
                  "away, and the glacier, ridgelines and snowfields"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER,
                   "The chalked fuel accounts on the fuel-store door are fixed: the marks do not move, "
                   "smudge, crawl, redraw themselves or change.",
                   "The ladder is rigid and bolted to the rock — it does not sway, flex, creak or shift."],
        "negatives": [NEG_WORLD + NEG_FIRE + ", the waterfall bursting or surging, spray filling the "
                      "frame"],
        "subjects": [
            {"name": "waterfall", "box": [0.26, 0.02, 0.39, 0.80],
             "phrase": "the waterfall pouring steadily down the dark rock beside the ladder, a constant "
                       "living fall of white water at an unchanging volume"},
            {"name": "fall_spray", "box": [0.27, 0.60, 0.42, 0.86],
             "phrase": "fine spray and drifting mist rising off the foot of the fall and hanging in the "
                       "cold air, curling and dissipating in place"},
            {"name": "trough_river", "box": [0.52, 0.54, 0.66, 0.72],
             "phrase": "the braided meltwater river running out of the glacier snout along the floor of "
                       "the trough, its pale channels glinting as the light travels down them"},
            {"name": "horizon_cloud", "box": [0.63, 0.31, 0.78, 0.42],
             "phrase": "a few small white clouds standing over the far ridge, swelling and softening "
                       "very slowly without drifting"},
            {"name": "survey_sheet", "box": [0.48, 0.87, 0.56, 1.0], "still": True},
        ],
    },

    # ── RUNG 3 · the anvil: a bare flagged summit over empty plains. THE TRAP ROOM ────────────────
    "anvil": {
        "rigid": ("The flagged pavement of the summit, the stone writing-slab on its low supports, the "
                  "iron fire-basket on its round plinth, the brass spyglass and its folding tripod, the "
                  "low grassy rims to left and right, and the far plains and their horizon"),
        "has_document": True,
        "pinned": [PIN_SNOW, PIN_BASKET, PIN_PAPER,
                   "The flagstones of the pavement are solid and level: none tilts, lifts, settles or "
                   "shifts."],
        # Two movers, and that is the honest answer for a bare pavement over empty plains — see the
        # module docstring. This is candidate _3, whose horizon was deliberately traded down to bare
        # plains to fix the seam at source, so there are no snowfields here to catch the light either.
        "negatives": [NEG_WORLD + NEG_FIRE + ", dust storm, sandstorm, blowing dust across the pavement"],
        "subjects": [
            {"name": "far_smoke", "box": [0.52, 0.34, 0.59, 0.54],
             "phrase": "a single hair-thin column of grey smoke standing far out on the plain, climbing "
                       "steadily and leaning slowly away downwind as it thins"},
            {"name": "rim_fall", "box": [0.60, 0.61, 0.67, 0.72],
             "phrase": "a thin white thread of water slipping over the rim below the eastern shoulder, "
                       "small and constant"},
            {"name": "slab_ledger", "box": [0.42, 0.78, 0.61, 0.95], "still": True},
        ],
    },

    # ── the shears: two rock blades framing a lenticular cloud and the braided trough ─────────────
    "shears": {
        "rigid": ("The two great blade-like rock fins, the flagged shelf, the drystone fuel-store with "
                  "its slate lintel and stacked cordwood, the wicker basket, the iron fire-basket, the "
                  "brass spyglass and its folding tripod, the village roofs on the flats, and the "
                  "glacier, ridgelines and snowfields"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE + ", the lens cloud drifting away, cloud crossing the frame, "
                      "time-lapse sky"],
        "subjects": [
            {"name": "lens_cloud", "box": [0.34, 0.21, 0.52, 0.37],
             "phrase": "the smooth lens of cloud standing motionless over the peak, holding its station "
                       "exactly while its edges feather and re-form and the light shifts along its "
                       "underside"},
            {"name": "braided_river", "box": [0.32, 0.62, 0.57, 0.97],
             "phrase": "the braided milk-jade river spread across the pale gravel of the trough, its "
                       "channels sliding and glinting as the light travels down them"},
            {"name": "flower_grass", "box": [0.09, 0.78, 0.27, 1.0],
             "phrase": "the tufts of straw grass and the thin scatter of alpine flowers on the near rock "
                       "nodding gently in the wind"},
            {"name": "survey_sheet", "box": [0.67, 0.89, 0.77, 1.0], "still": True},
        ],
    },

    # ── BOSS · the guardroom: an interior, and the only live flame in the daytime scenario ───────
    "whistlegate": {
        "rigid": ("The dry-laid stone walls and the heavy roof beams, the plank sorting bench and its "
                  "bundles, the brass scales, the coiled rope, the oak writing-desk and its ledgers, the "
                  "stone hearth surround and its hanging pot, the framed board on the wall, the heavy "
                  "timber gate and the arched doorway, and the flagged floor"),
        "has_document": True,
        # THE ONE ROOM WHERE FIRE IS CORRECT. This is a domestic hearth in a manned guardroom, not a
        # beacon: the cold-basket rule is about the signal fires on the tops. See the docstring.
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_PAPER,
                   "No beacon or signal fire is lit anywhere outside — the hearth in this room is the "
                   "only flame, and nothing burns on any ridge, tower or summit seen through the "
                   "doorways or the window.",
                   "The framed board on the wall stays blank and flat: no lettering, marks or images "
                   "appear on it and its surface does not ripple.",
                   "The brass scales hang level and do not swing, tilt or sway."],
        "negatives": [NEG_WORLD + ", the fire spreading, sparks flying into the room, the pot swinging, "
                      "smoke filling the room, lit beacon on a ridge"],
        "subjects": [
            {"name": "hearth_fire", "box": [0.54, 0.55, 0.61, 0.73],
             "phrase": "a low live fire burning in the stone hearth, its flames working quietly over the "
                       "embers and flaring and settling again, throwing a warm unsteady light onto the "
                       "surrounding stone"},
            {"name": "hearth_smoke", "box": [0.54, 0.02, 0.62, 0.52],
             "phrase": "a thin thread of woodsmoke rising off the fire and up the dark chimney breast, "
                       "wavering and thinning as it climbs"},
            {"name": "gate_daylight", "box": [0.09, 0.17, 0.22, 0.78],
             "phrase": "the hard daylight standing in the open gateway, its brightness breathing very "
                       "faintly as thin high air moves across the sun"},
            {"name": "desk_ledger", "box": [0.63, 0.54, 0.79, 0.76], "still": True},
        ],
    },

    # ── the broken tooth: a snapped pillar and a banner of blown snow off the massif ─────────────
    "broken_tooth": {
        "rigid": ("The snapped pale pillar of the tooth and the rock stack it stands on, the flagged "
                  "shelf, the iron fire-basket on its round drystone plinth, the timber fuel-store and "
                  "its stacked cordwood, the brass spyglass and its folding tripod, the village roofs on "
                  "the plateau across the gorge, and the smooth snow-slopes to either side"),
        "has_document": True,
        "pinned": [PIN_SNOW, PIN_BASKET, PIN_PAPER,
                   "The broken pillar is solid: it does not lean, crack further, shed rock or settle."],
        "negatives": [NEG_WORLD + NEG_FIRE + ", avalanche, snow slide, powder cloud descending the "
                      "slope, collapsing cornice"],
        "subjects": [
            {"name": "snow_banner", "box": [0.58, 0.32, 0.74, 0.48],
             "phrase": "a fine banner of wind-blown powder streaming off the crest of the massif and "
                       "feathering out into the air, dissipating and re-forming in place high on the "
                       "ridge and never descending the face"},
            {"name": "gorge_haze", "box": [0.32, 0.48, 0.62, 0.60],
             "phrase": "a faint haze of cold air hanging in the shadowed gorge below the plateau, "
                       "shifting slowly and thinning"},
            {"name": "survey_sheet", "box": [0.62, 0.87, 0.71, 1.0], "still": True},
        ],
    },

    # ── the kiln: a bare red dome with a banner cloud streaming off its crest ─────────────────────
    "kiln": {
        "rigid": ("The domed red hill and its bedded rock, the small stone kiln-hut on its shoulder, the "
                  "flagged ground, the iron fire-basket on its round drystone plinth, the timber "
                  "fuel-store, the brass spyglass and its folding tripod, the walking paths, the "
                  "terraced flats across the gorge, and the snow-capped range along the horizon"),
        "has_document": True,
        "pinned": [PIN_SNOW, PIN_BASKET, PIN_PAPER,
                   "The red dome and its bedding are solid: no rock shifts, slides or sheds."],
        # Two movers. A bare red dome under a hard cobalt sky genuinely has a banner and a haze and
        # nothing else — see the docstring on honest subject counts.
        "negatives": [NEG_WORLD + NEG_FIRE + ", cloud crossing the frame, time-lapse sky, dust storm, "
                      "blowing dust off the dome"],
        "subjects": [
            {"name": "banner_cloud", "box": [0.39, 0.15, 0.76, 0.30],
             "phrase": "a long thin banner of cloud torn off the crest of the dome and streaming away "
                       "downwind, its filaments forming and re-forming against the cobalt sky while the "
                       "banner itself holds its station on the summit"},
            {"name": "range_haze", "box": [0.55, 0.40, 0.95, 0.52],
             "phrase": "a thin band of cold haze standing along the foot of the far snow range, "
                       "shifting and settling very slowly"},
            {"name": "survey_sheet", "box": [0.21, 0.83, 0.31, 0.96], "still": True},
        ],
    },

    # ── ESCAPE · the crown: the highest point, the whole chain in view, the sun overhead ──────────
    "crown": {
        "rigid": ("The flagged summit pavement, the drystone hut and its slate roof, the tall louvred "
                  "signal screen in its timber frame, the iron brazier on its stand, the stone "
                  "writing-slab and its weight, the stacked cairns along the ridge, and the glacier, "
                  "ridgelines and snowfields"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_PAPER,
                   "The iron brazier is COLD, empty and unlit — no flame, no ember, no glow and no smoke "
                   "— and no fire burns on any tower, ridge or summit in view.",
                   "The louvred signal screen is fixed: its leaves do not open, close, turn, rattle or "
                   "swing.",
                   "The cairns are solid stacked stone: no slab shifts, slides or topples."],
        "negatives": [NEG_WORLD + NEG_FIRE + ", the sun moving across the sky, time-lapse sun, lens "
                      "flare sweeping, shutters opening"],
        "subjects": [
            {"name": "glacier_lake", "box": [0.26, 0.58, 0.34, 0.68],
             "phrase": "the milky glacial lake below the ice snout, its pale surface stirring with the "
                       "faintest slow movement and the light shifting across it"},
            {"name": "trough_river", "box": [0.35, 0.56, 0.59, 0.74],
             "phrase": "the braided river running away down the trough from the lake, its channels "
                       "glinting as the light travels along them"},
            {"name": "summit_haze", "box": [0.18, 0.36, 0.72, 0.50],
             "phrase": "a thin shimmer of thin cold air standing over the snow range across the trough, "
                       "the far ridgelines trembling very slightly in it"},
            {"name": "slab_sheet", "box": [0.53, 0.74, 0.63, 0.96], "still": True},
        ],
    },
}


def build(room):
    """The full spec for a room, tagged with room/state for the render's filenames."""
    s = dict(SPECS[room])
    s["room"], s["state"] = room, "base"
    return s


def _main():
    write = "--write" in sys.argv
    show = "--show" in sys.argv
    doc = json.load(open(P, encoding="utf-8"))
    keys = [r["key"] for r in doc["rooms"]]
    missing = [k for k in keys if k not in SPECS]
    extra = [k for k in SPECS if k not in keys]
    if missing or extra:
        print("!! room coverage mismatch — missing %s, unknown %s" % (missing, extra))
        return 1

    bad = 0
    for room in keys:
        spec = build(room)
        errs = MS.validate(spec)
        movers = [x for x in spec["subjects"] if not x.get("still")]
        print("%-14s %d movers, %d pinned  %s"
              % (room, len(movers), len(spec["subjects"]) - len(movers), "OK" if not errs else "ERRORS"))
        for e in errs:
            print("    ! " + e)
            bad += 1
        if show:
            print("    + " + MS.render_prompt(spec)[:400] + " …\n")
        if not write or errs:
            continue
        node = next(r for r in doc["rooms"] if r["key"] == room)
        # PRESERVE ANY EXISTING `states` BLOCK. The night sub-specs are authored separately (they need
        # the night art, which is a different picture — `sisters`' cloud river and `spindle`'s spindrift
        # are both simply ABSENT after dark, so a night subject list cannot be derived from the day one).
        # Writing the base over the node wholesale would silently delete them, leaving every full-scene
        # night variant with no spec and therefore no clip — the exact "state with no clip of its own
        # goes completely static" failure in cinemagraph_tools/AGENTS.md.
        prev = (node.get("authoring") or {}).get("motionSpec") or {}
        if prev.get("states") and "states" not in spec:
            spec["states"] = prev["states"]
        node.setdefault("authoring", {})["motionSpec"] = spec

    if write and not bad:
        json.dump(doc, open(P, "w", encoding="utf-8"), indent=2)
        print("\nwritten onto %d room nodes" % len(keys))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_main())
