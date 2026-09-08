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

# ── shared phrases ────────────────────────────────────────────────────────────────────────────────
# RE-AUTHORED 2026-09-07 TO ONE HERO PER STATE (see the header note). A phrase is defined once here
# when several rooms name the same kind of thing, because `render_prompt` de-duplicates on the exact
# string — three rooms whose river phrase differs only in wording would each get their own sentence.
PH_RIVER_NIGHT = ("the pale braided channels of the river on the dark valley floor far below glimmering "
                  "faintly and shifting very slowly in place, small highlights forming and fading along "
                  "the wet gravel bars while the channels stay exactly in their present courses")
PIN_STARS = ("The night sky is completely fixed: every star holds its exact position and its exact "
             "brightness for the whole loop — the stars do not drift, swarm, shimmer, stream, appear or "
             "disappear, and no new star, cloud, glow or light appears anywhere in the sky.")
PIN_NO_FLAME_HERE = ("No candle, lamp, lantern, taper, torch or flame of any kind appears anywhere on "
                     "this platform, on the survey sheet, on the fuel box or in the fire-basket.")
PIN_TARN = ("The tarn is a fixed level: it does not rise, drain, spread or overflow, and its ice-laced "
            "rim and shoreline stay exactly where they are.")

# ── the specs ─────────────────────────────────────────────────────────────────────────────────────
SPECS = {
    # ── RUNG 1 · the valley station: dawn mist on the bars ────────────────────────────────────────
    # HERO: the mist band. Lucas, 2026-09-07: "it should just focus on making that kind of misty smoke
    # undulate. That's the only thing this cinemagraph needs to focus on." Confirmed on the panorama —
    # a broad waist-deep band over the braided river, the largest soft-edged thing in the frame, and it
    # already measured p95 10.6 ALIVE in the superseded clip. The chimney plume and the river glint are
    # deliberately UNNAMED now: both animated fine, and neither is wanted.
    "fenwatch": {
        "rigid": ("The long stone office and its slate roof, the propped shutters and the writing-desk, "
                  "the sorting bench under its lean-to and its pigeonholes, the drystone yard wall and "
                  "the open yard gate, the water butt and its dipper, the barrow of kindling, the "
                  "flagged yard, the wading stakes and drying racks out on the bars, and the ridgelines "
                  "and snowfields"),
        # NO MAST HERE. The art prompt's negatives say this station carries no tower, and the render has
        # none — the timber uprights at the extreme edges are the gate posts.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_PAPER,
                   "The bundled correspondence in the sorting-bench pigeonholes and the stacked wicker "
                   "trays stay exactly as they are stacked."],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "valley_mist", "box": [0.02, 0.31, 0.44, 0.51], "hero": True,
             "phrase": "the waist-deep band of dawn mist lying along the braided river undulating slowly "
                       "in place over the pale gravel bars, its soft upper edge lifting and settling "
                       "again and the whole band thinning and thickening where it breaks around the "
                       "drystone windbreaks"},
            {"name": "desk_ledgers", "box": [0.44, 0.62, 0.64, 0.72], "still": True},
        ],
    },

    # ── the knife-edge fin: spindrift off the needle ───────────────────────────────────────────────
    # HERO: the spindrift. "it just needs to focus on that like spin drift coming off of the large rock
    # formation itself. If it can just get that, and even if everything else is still, that will be just
    # fine." Kept verbatim from the superseded spec — it measured p95 10.27 ALIVE, so the phrase works
    # and only its company has changed. The four object pins the overnight loop added here
    # (platform_stone, fire_basket, spyglass_tripod, fuel_box) are GONE: `rigid` names all four in one
    # sentence, and anything that still moves is a paint-out.
    "spindle": {
        "rigid": ("The dry-laid stone platform, the narrow rock fin and its crest, the pale tapering "
                  "needle, the iron fire-basket and its stone-lidded fuel box, the brass spyglass and "
                  "its folding tripod, the walking paths, and the long smooth snow-slopes to either side"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "needle_spindrift", "box": [0.24, 0.03, 0.37, 0.32], "hero": True,
             "phrase": "a fine banner of spindrift streaming off the needle's edge into the cobalt sky, "
                       "feathering out and re-forming against the rock without ever leaving it"},
            {"name": "survey_sheet", "box": [0.55, 0.86, 0.66, 1.0], "still": True},
        ],
    },

    # ── the closed cirque: the black tarn ─────────────────────────────────────────────────────────
    # HERO: the tarn surface. "it just needs to focus on getting like rippling in the water in that pool.
    # That's all it needs." Measured p95 15.63 ALIVE. PIN_TARN is added and is a STORY pin, not tidying:
    # the scenario's disaster is a moraine-dammed tarn bursting, so a tarn that visibly rises or spreads
    # in a daytime clip gives away the ending.
    "rams_head": {
        "rigid": ("The horned outcrop and the dark curving cirque wall, the dry-laid platform and its "
                  "rubble shelf, the iron fire-basket on its plinth, the timber fuel-store and its "
                  "stacked cordwood, the wicker basket, the brass spyglass on its boulder, and the one "
                  "path dropping south out of the cirque mouth"),
        "has_document": True,
        "pinned": [PIN_SNOW, PIN_BASKET, PIN_PAPER, PIN_TARN],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "tarn_surface", "box": [0.26, 0.58, 0.47, 0.80], "hero": True,
             "phrase": "the black tarn's surface rippling gently in place, fine wind-ruffles crossing it "
                       "and smoothing away again while its ice-laced rim holds exactly its present shape"},
            {"name": "survey_sheet", "box": [0.62, 0.78, 0.72, 0.90], "still": True},
        ],
    },

    # ── the twin peaks: the cloud river in the saddle ──────────────────────────────────────────────
    # HERO: the cloud river. "all it needs to focus on is getting those clouds in the kind of the middle
    # of the frame, getting those clouds kind of like moving and rippling slowly. That's all it needs to
    # do. Nothing else." Measured p95 11.55 ALIVE. Phrased to POUR IN PLACE — the recipe pins frame 0
    # and frame -1 to the same still, so a cloud that crosses the saddle loses the fight to the end guide.
    "sisters": {
        "rigid": ("The two slate peaks and the saddle between them, the dry-laid platform and its slab "
                  "table, the stacked slate cairns, the iron fire-basket, the fuel store, and the paths "
                  "in and out of the saddle"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "cloud_river", "box": [0.44, 0.24, 0.64, 0.66], "hero": True,
             "phrase": "the slow river of cloud standing in the saddle between the two peaks, rippling "
                       "and shredding softly in place, its billows swelling and sinking back again "
                       "without the mass ever crossing the gap or drifting out of it"},
            {"name": "slab_ledger", "box": [0.30, 0.74, 0.44, 0.88], "still": True},
        ],
    },

    # ── the cloud-sea terrace ──────────────────────────────────────────────────────────────────────
    # HERO: the cloud sea. "it just needs to focus on getting the clouds kind of like rippling and
    # rolling or moving or undulating or whatever they do."
    # THREE BOXES, ONE PHRASE, ONE HERO. The superseded single box ran [0.1,0.42,0.68,0.8] and swallowed
    # the stone parapet and the whole village-and-pasture island in the middle of the cloud, which is
    # why the room's own subject measured only p95 5.43 WEAK while the cloud beside it read 9.67: most
    # of the box was static ground. Boxes checked photometrically — the left mass is 89% cloud, the far
    # band 70%, the right mass 65%, against 57% for the old box. Only the left mass carries `hero`,
    # because `hero_deaths` convicts on ANY dead hero and there is no reason to make three promises
    # where the strongest box already proves the render did the work.
    "hood": {
        "rigid": ("The rock arch overhead and its stone piers, the flagged terrace and its parapet, the "
                  "iron fire-basket and its stone base, the woodpile and lean-to, the brass spyglass and "
                  "its tripod, the reading slab, and the far snow range and its ridgelines"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "cloud_sea_left", "box": [0.17, 0.55, 0.29, 0.70], "hero": True,
             "phrase": "the sea of cloud filling the valley rolling and undulating very slowly in place, "
                       "its soft upper surface breathing as low billows swell, lean and sink back again "
                       "without the sheet ever drifting across the valley or opening"},
            {"name": "cloud_sea_far", "box": [0.16, 0.435, 0.66, 0.525],
             "phrase": "the sea of cloud filling the valley rolling and undulating very slowly in place, "
                       "its soft upper surface breathing as low billows swell, lean and sink back again "
                       "without the sheet ever drifting across the valley or opening"},
            {"name": "cloud_sea_right", "box": [0.50, 0.53, 0.66, 0.66],
             "phrase": "the sea of cloud filling the valley rolling and undulating very slowly in place, "
                       "its soft upper surface breathing as low billows swell, lean and sink back again "
                       "without the sheet ever drifting across the valley or opening"},
            {"name": "survey_sheets", "box": [0.72, 0.74, 0.84, 0.86], "still": True},
        ],
    },

    # ── the ladder pitch ──────────────────────────────────────────────────────────────────────────
    # UNCHANGED, and deliberately: "The ladder during the day is fine." Left exactly as authored
    # 2026-09-03 so the committed clip stays valid — this room is not in the re-render queue.
    "ladder": {
        # KEPT VERBATIM — Lucas, 2026-09-07: "The ladder during the day is fine."
        # `keep` means RECORD ONLY: `_main` does not rewrite the node and does not apply the
        # one-or-two-hero check, because this state ships a clip that is already accepted and
        # re-deriving its spec could only invalidate finished art. The text is here so this file
        # stays the complete record of how every beacons spec was authored.
        "keep": True,
          "rigid": "The timber ladder and its rungs, the dark wet rock walls, the stone-and-timber fuel-store, its plank door and its stacked cordwood, the iron fire-basket, the brass spyglass and its folding tripod, the flagged shelf, the cut stone steps climbing away, and the glacier, ridgelines and snowfields",
          "has_document": True,
          "pinned": [
            "The river is a fixed level: it does not rise, swell, flood, spread or advance, and its channels stay exactly in their present courses on the gravel.",
            "The snowfields, glaciers and ridgelines are fixed: no avalanche, no sliding snow-mass, no falling rock, no collapse.",
            "The open iron fire-basket is COLD, empty and unlit — no flame, no ember, no glow and no smoke rises from it, and no fire appears anywhere on the range.",
            "The dispatch ledgers, filed dispatch copies and the folded linen survey sheet lie flat and still under their weights; no page lifts, curls, turns, flutters or changes.",
            "The chalked fuel accounts on the fuel-store door are fixed: the marks do not move, smudge, crawl, redraw themselves or change.",
            "The ladder is rigid and bolted to the rock — it does not sway, flex, creak or shift."
          ],
          "negatives": [
            ", rising water, flooding, water level changing, surging water, waves, splashing, churning water, avalanche, sliding snow, falling rock, collapsing rock, people, figures, walking, animals running, birds, flags, pennants, bunting, boats, fire, flame, embers, glow, ignition, sparks, firelight, lit beacon, the waterfall bursting or surging, spray filling the frame"
          ],
          "subjects": [
            {
              "name": "waterfall",
              "box": [
                0.26,
                0.02,
                0.39,
                0.8
              ],
              "phrase": "the waterfall pouring steadily down the dark rock beside the ladder, a constant living fall of white water at an unchanging volume"
            },
            {
              "name": "fall_spray",
              "box": [
                0.27,
                0.6,
                0.42,
                0.86
              ],
              "phrase": "fine spray and drifting mist rising off the foot of the fall and hanging in the cold air, curling and dissipating in place"
            },
            {
              "name": "trough_river",
              "box": [
                0.52,
                0.54,
                0.66,
                0.72
              ],
              "phrase": "the braided meltwater river running out of the glacier snout along the floor of the trough, its pale channels glinting as the light travels down them"
            },
            {
              "name": "horizon_cloud",
              "box": [
                0.63,
                0.31,
                0.78,
                0.42
              ],
              "phrase": "a few small white clouds standing over the far ridge, swelling and softening very slowly without drifting"
            },
            {
              "name": "survey_sheet",
              "box": [
                0.48,
                0.87,
                0.56,
                1.0
              ],
              "still": True
            }
          ]
    },

    # ── the bare tableland: the far woodsmoke column ───────────────────────────────────────────────
    # HERO: the smoke column. "it should just focus on getting the smoke rising slowly in the distance."
    # ⚠️ THE ART MAY NOT SUPPORT THIS AND THE EVIDENCE IS ALREADY IN. `far_smoke` measured p95 3.22 (DEAD,
    # bar 4.5) and the overnight loop then rendered it ALONE as a dedicated 320x288 tile, where it scored
    # 2.05 against 2.08 for the bare sky beside it — i.e. indistinguishable from nothing. Looked at
    # natively, the column is a ~30 px thread in a 215x204 box: the "angular size decides what can
    # animate" case in the motion skill, which no prompt reaches. `force_repair` asks for the tile anyway
    # because that is the documented remedy for a dead subject and it is the one lever not yet spent in
    # combination with a one-subject prompt. If this comes back dead a THIRD time the fix is a stills
    # regeneration of the plume, not another motion prompt.
    "anvil": {
        "rigid": ("The shattered rock-plate tableland and its shoulders, the dry-laid slab table, the "
                  "iron fire-basket on its plinth, the timber fuel-store and stacked cordwood, the brass "
                  "spyglass and its tripod, the cairns at the extreme edges, and the far ranges"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "far_smoke", "box": [0.52, 0.34, 0.59, 0.54], "hero": True, "force_repair": True,
             "phrase": "the single grey column of woodsmoke standing over the far benches, billow after "
                       "billow lifting and unrolling slowly up the column and fading out at its top, the "
                       "column itself staying exactly over its own spot on the ground"},
            {"name": "slab_ledger", "box": [0.42, 0.78, 0.61, 0.95], "still": True},
        ],
    },

    # ── the shears: the lenticular cloud ──────────────────────────────────────────────────────────
    # HERO: the lens cloud. "It just needs to go for that cloud in the distance, slowly, like rippling,
    # not spinning, but just kind of rippling in the wind."
    # NOT SPINNING IS AN EXPLICIT INSTRUCTION and it goes in the negatives, because a lenticular cloud is
    # the one cloud shape a model will happily rotate. Box tightened from [0.34,0.21,0.52,0.37] onto the
    # lens itself: the old box was a third sky and a third snow peak, and the subject sat at p95 4.50 —
    # exactly ON the dead bar — with lit_pct 100, so the sparse-lit path could not rescue it either.
    "shears": {
        "rigid": ("The two shear rock blades and the notch between them, the dry-laid platform, the iron "
                  "fire-basket on its stone base, the fuel store, the brass spyglass and its tripod, the "
                  "reading slab, and the snow peak and far ranges"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE + ", rotating cloud, spinning cloud, swirling, revolving, "
                      "turning, vortex, cloud drifting away, cloud growing, cloud dispersing"],
        "subjects": [
            {"name": "lens_cloud", "box": [0.362, 0.236, 0.505, 0.327], "hero": True,
             "phrase": "the great lens-shaped cloud standing over the snow peak rippling very slowly in "
                       "place, fine ribs forming and smoothing along its underside and its rim "
                       "feathering and re-knitting, the whole lens holding its shape, its size and its "
                       "position over the summit"},
            {"name": "survey_sheet", "box": [0.60, 0.76, 0.72, 0.90], "still": True},
        ],
    },

    # ── the guardroom ─────────────────────────────────────────────────────────────────────────────
    # UNCHANGED: "The whistle gate during the day is fine. The whistle gate at night is also fine."
    "whistlegate": {
        # KEPT VERBATIM — Lucas, 2026-09-07: "The whistle gate during the day is fine. The whistle gate at night is also fine."
        # `keep` means RECORD ONLY: `_main` does not rewrite the node and does not apply the
        # one-or-two-hero check, because this state ships a clip that is already accepted and
        # re-deriving its spec could only invalidate finished art. The text is here so this file
        # stays the complete record of how every beacons spec was authored.
        "keep": True,
          "rigid": "The dry-laid stone walls and the heavy roof beams, the plank sorting bench and its bundles, the brass scales, the coiled rope, the oak writing-desk and its ledgers, the stone hearth surround and its hanging pot, the framed board on the wall, the heavy timber gate and the arched doorway, and the flagged floor",
          "has_document": True,
          "pinned": [
            "The river is a fixed level: it does not rise, swell, flood, spread or advance, and its channels stay exactly in their present courses on the gravel.",
            "The snowfields, glaciers and ridgelines are fixed: no avalanche, no sliding snow-mass, no falling rock, no collapse.",
            "The dispatch ledgers, filed dispatch copies and the folded linen survey sheet lie flat and still under their weights; no page lifts, curls, turns, flutters or changes.",
            "No beacon or signal fire is lit anywhere outside — the hearth in this room is the only flame, and nothing burns on any ridge, tower or summit seen through the doorways or the window.",
            "The framed board on the wall stays blank and flat: no lettering, marks or images appear on it and its surface does not ripple.",
            "The brass scales hang level and do not swing, tilt or sway."
          ],
          "negatives": [
            ", rising water, flooding, water level changing, surging water, waves, splashing, churning water, avalanche, sliding snow, falling rock, collapsing rock, people, figures, walking, animals running, birds, flags, pennants, bunting, boats, the fire spreading, sparks flying into the room, the pot swinging, smoke filling the room, lit beacon on a ridge"
          ],
          "subjects": [
            {
              "name": "hearth_fire",
              "box": [
                0.54,
                0.55,
                0.61,
                0.73
              ],
              "phrase": "a low live fire burning in the stone hearth, its flames working quietly over the embers and flaring and settling again, throwing a warm unsteady light onto the surrounding stone"
            },
            {
              "name": "hearth_smoke",
              "box": [
                0.54,
                0.02,
                0.62,
                0.52
              ],
              "phrase": "a thin thread of woodsmoke rising off the fire and up the dark chimney breast, wavering and thinning as it climbs"
            },
            {
              "name": "gate_daylight",
              "box": [
                0.09,
                0.17,
                0.22,
                0.78
              ],
              "phrase": "the hard daylight standing in the open gateway, its brightness breathing very faintly as thin high air moves across the sun"
            },
            {
              "name": "desk_ledger",
              "box": [
                0.63,
                0.54,
                0.79,
                0.76
              ],
              "still": True
            },
            {
              "name": "bench_scales",
              "box": [
                0.23,
                0.5,
                0.33,
                0.78
              ],
              "still": True
            }
          ]
    },

    # ── the broken tooth: the powder banner ───────────────────────────────────────────────────────
    # HERO: the snow banner. "it just needs to focus on getting that kind of like slow, gentle avalanche
    # of snow in the distance moving and rippling." Measured p95 9.20 ALIVE.
    # ⚠️ THE WORD "AVALANCHE" IS NOT USED IN THE PROMPT, ON PURPOSE. Lucas's description is of the visible
    # effect; the world's own PIN_SNOW forbids a sliding snow-mass because the scenario's disaster is a
    # tarn burst, not a slide, and the header note records that blowing snow is one bad phrase away from
    # becoming one. It stays a wind-blown powder banner streaming off the shoulder — which is what the
    # frame actually shows — and PIN_SNOW stays in place.
    "broken_tooth": {
        "rigid": ("The broken summit tooth and its shattered crest, the dry-laid platform, the iron "
                  "fire-basket, the fuel store and cordwood, the brass spyglass and its tripod, the "
                  "reading slab, the gorge walls, and the green shelf and its villages across the gorge"),
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "snow_banner", "box": [0.58, 0.32, 0.74, 0.48], "hero": True,
             "phrase": "the long banner of wind-blown powder snow streaming off the massif's shoulder, "
                       "rippling and feathering in place as it thins out into the sky and re-forms "
                       "against the ridge, the snowfield beneath it never moving"},
            {"name": "survey_sheet", "box": [0.44, 0.80, 0.56, 0.94], "still": True},
        ],
    },

    # ── the kiln ──────────────────────────────────────────────────────────────────────────────────
    # UNCHANGED: "The kiln at day is fine. The kiln at night is also fine."
    "kiln": {
        # KEPT VERBATIM — Lucas, 2026-09-07: "The kiln at day is fine. The kiln at night is also fine."
        # `keep` means RECORD ONLY: `_main` does not rewrite the node and does not apply the
        # one-or-two-hero check, because this state ships a clip that is already accepted and
        # re-deriving its spec could only invalidate finished art. The text is here so this file
        # stays the complete record of how every beacons spec was authored.
        "keep": True,
          "rigid": "The domed red hill and its bedded rock, the small stone kiln-hut on its shoulder, the flagged ground, the iron fire-basket on its round drystone plinth, the timber fuel-store, the brass spyglass and its folding tripod, the walking paths, the terraced flats across the gorge, and the snow-capped range along the horizon",
          "has_document": True,
          "pinned": [
            "The snowfields, glaciers and ridgelines are fixed: no avalanche, no sliding snow-mass, no falling rock, no collapse.",
            "The open iron fire-basket is COLD, empty and unlit — no flame, no ember, no glow and no smoke rises from it, and no fire appears anywhere on the range.",
            "The dispatch ledgers, filed dispatch copies and the folded linen survey sheet lie flat and still under their weights; no page lifts, curls, turns, flutters or changes.",
            "The red dome and its bedding are solid: no rock shifts, slides or sheds."
          ],
          "negatives": [
            ", rising water, flooding, water level changing, surging water, waves, splashing, churning water, avalanche, sliding snow, falling rock, collapsing rock, people, figures, walking, animals running, birds, flags, pennants, bunting, boats, fire, flame, embers, glow, ignition, sparks, firelight, lit beacon, cloud crossing the frame, time-lapse sky, dust storm, blowing dust off the dome"
          ],
          "subjects": [
            {
              "name": "banner_cloud",
              "box": [
                0.39,
                0.15,
                0.76,
                0.3
              ],
              "phrase": "a long thin banner of cloud torn off the crest of the dome and streaming away downwind, its filaments forming and re-forming against the cobalt sky while the banner itself holds its station on the summit"
            },
            {
              "name": "range_haze",
              "box": [
                0.55,
                0.4,
                0.95,
                0.52
              ],
              "phrase": "a thin band of cold haze standing along the foot of the far snow range, shifting and settling very slowly"
            },
            {
              "name": "survey_sheet",
              "box": [
                0.21,
                0.83,
                0.31,
                0.96
              ],
              "still": True
            }
          ]
    },

    # ── the crown ─────────────────────────────────────────────────────────────────────────────────
    # UNCHANGED: "The crown during the day is fine. The crown at night is fine. And the crown with the
    # order sent status is fine." All three states keep their committed clips.
    "crown": {
        # KEPT VERBATIM — Lucas, 2026-09-07: "The crown during the day is fine. The crown at night is fine. And the crown with the
    # order sent status is fine." All three states keep their committed clips.
        # `keep` means RECORD ONLY: `_main` does not rewrite the node and does not apply the
        # one-or-two-hero check, because this state ships a clip that is already accepted and
        # re-deriving its spec could only invalidate finished art. The text is here so this file
        # stays the complete record of how every beacons spec was authored.
        "keep": True,
          "rigid": "The flagged summit pavement, the drystone hut and its slate roof, the tall louvred signal screen in its timber frame, the iron brazier on its stand, the stone writing-slab with the linen survey sheet weighted flat on it, the stacked cairns along the ridge, and the glacier, ridgelines and snowfields",
          "has_document": True,
          "pinned": [
            "The folded linen survey sheet lies FLAT on the stone slab under its two cobble weights and does not move at all: it never lifts, rears, rises, billows, bellies, curls, flaps, turns, slides or leaves the slab, and no part of it stands up off the stone or crosses in front of the valley behind.",
            "The dispatch ledgers and filed dispatch copies lie flat and still under their weights; no page lifts, curls, turns, flutters or changes.",
            "The river is a fixed level: it does not rise, swell, flood, spread or advance, and its channels stay exactly in their present courses on the gravel.",
            "The snowfields, glaciers and ridgelines are fixed: no avalanche, no sliding snow-mass, no falling rock, no collapse.",
            "The iron brazier is COLD, empty and unlit - no flame, no ember, no glow and no smoke - and no fire burns on any tower, ridge or summit in view.",
            "The louvred signal screen is fixed: its leaves do not open, close, turn, rattle or swing.",
            "The cairns are solid stacked stone: no slab shifts, slides or topples."
          ],
          "negatives": [
            ", billowing cloth, lifting linen, cloth rearing up off a table, sheet standing on end, flapping fabric, sail, cloth blowing in the wind, paper curling, parchment lifting, page turning, document deforming, rising water, flooding, water level changing, surging water, waves, splashing, churning water, avalanche, sliding snow, falling rock, collapsing rock, people, figures, walking, animals running, birds, flags, pennants, bunting, boats, fire, flame, embers, glow, ignition, sparks, firelight, lit beacon, the sun moving across the sky, time-lapse sun, lens flare sweeping, shutters opening, louvres turning, slats moving"
          ],
          "subjects": [
            {
              "name": "glacier_lake",
              "box": [
                0.26,
                0.58,
                0.34,
                0.68
              ],
              "phrase": "the milky glacial lake below the ice snout, its pale surface stirring with the faintest slow movement and the light shifting across it"
            },
            {
              "name": "trough_river",
              "box": [
                0.35,
                0.56,
                0.59,
                0.74
              ],
              "phrase": "the braided river running away down the trough from the lake, its channels glinting as the light travels along them"
            },
            {
              "name": "summit_haze",
              "box": [
                0.18,
                0.36,
                0.72,
                0.5
              ],
              "phrase": "a thin shimmer of thin cold air standing over the snow range across the trough, the far ridgelines trembling very slightly in it"
            },
            {
              "name": "slab_sheet",
              "box": [
                0.545,
                0.5,
                0.685,
                1.0
              ],
              "still": True,
              "phrase": "the reading slab just right of centre with the folded linen survey sheet weighted flat and motionless on it under two river cobbles, the brass rule and charcoal lying still across the corner"
            }
          ]
    },
}

# ── the NIGHT sub-specs ───────────────────────────────────────────────────────────────────────────
# NEW HOME, 2026-09-07. These used to exist ONLY on the room nodes in scenario.json, written straight
# there by the overnight loop — so the one thing this file exists to be, the record of HOW a spec was
# authored, did not cover half the states. Every night state Lucas asked to change is now authored here;
# a state absent from this dict is left exactly as it is on the node (`_main` merges rather than replaces),
# which is what keeps fenwatch/night, rams_head/night, sisters/night, whistlegate/night, kiln/night and
# all three crown states on their committed clips.
#
# THE NIGHT PATTERN IS THE RIVER, NOT THE LAMPS. Five of these six name the valley river, and that is a
# measurement decision as much as an aesthetic one: the distant village lamps occupy well under 1% of
# their box (rams_head 0.79%), which is the "angular size decides what can animate" trap — the box p95
# is arithmetically blind to them and the sparse-lit rescue is measuring a handful of specks. The one
# state that DOES keep the lamps as its hero is broken_tooth, where the villages sit on a shelf directly
# across the gorge from the viewer and measured p95 6.88 / lit 26.43 ALIVE.
NIGHT = {
    "spindle": {
        # PER-STATE `rigid`. Without it `render_prompt` falls back to DEFAULT_RIGID — "The
        # buildings, walls, stonework, ground and horizon" — which names BUILDINGS on a bare rock
        # platform. Naming a thing that is not in the frame is how a stabiliser starts inviting
        # the model to draw it, which is the failure the header note records for the guardroom.
        "rigid": ("The dry-laid stone platform, the narrow rock fin and its crest, the pale tapering needle, the iron fire-basket and its stone-lidded fuel box, the brass spyglass and its folding tripod, the walking paths, and the long smooth snow-slopes to either side"),
        # "it could just aim to getting like the slow motion of the little, of the river down in the
        # valley." And the complaint that named the pin: "it has kind of like put a little candle on the
        # paper." The superseded night spec carried NO pins and no `has_document` at all — which is
        # exactly how a candle gets drawn onto a survey sheet — so the document pin and an explicit
        # no-flame-on-this-platform line go in, with the sheet's box read off the night art.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER, PIN_NO_FLAME_HERE, PIN_STARS],
        "negatives": [NEG_WORLD + NEG_FIRE + ", candle, candlelight, taper, lit lamp, lantern glow"],
        "subjects": [
            {"name": "river_glimmer", "box": [0.49, 0.52, 0.66, 0.69], "hero": True,
             "phrase": PH_RIVER_NIGHT},
            {"name": "survey_sheet", "box": [0.575, 0.855, 0.670, 0.995], "still": True},
        ],
    },
    "hood": {
        # PER-STATE `rigid`. Without it `render_prompt` falls back to DEFAULT_RIGID — "The
        # buildings, walls, stonework, ground and horizon" — which names BUILDINGS on a bare rock
        # platform. Naming a thing that is not in the frame is how a stabiliser starts inviting
        # the model to draw it, which is the failure the header note records for the guardroom.
        "rigid": ("The rock arch overhead and its stone piers, the flagged terrace and its parapet, the iron fire-basket and its stone base, the woodpile and lean-to, the brass spyglass and its tripod, the reading slab, and the far snow range and its ridgelines"),
        # "And the same at night. It just needs to focus on getting the clouds moving gently. That's the
        # only motion needed." There was no cloud subject here at all — the night spec named only the
        # lamps and the river — so this is authored fresh against `scene_night.png`, where the moonlit
        # cloud sea fills the middle of the frame and reads mean luma 42 against 23 for the sky, with
        # 1905 pixels above the lit bar (so no `unlit` misfire).
        # THE STAR PIN STAYS, and it is not tidying: the loop added it because the sky was swarming, and
        # a swarming star field makes the clip unusable rather than merely untidy. It arrived with an
        # EMPTY phrase, which meant it only ever existed as a mask blackout and said nothing to the
        # render; it now carries PIN_STARS so the prompt asks for the same thing the mask enforces.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER, PIN_STARS],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "cloud_sea_night", "box": [0.14, 0.46, 0.64, 0.72], "hero": True,
             "phrase": "the moonlit sea of cloud filling the valley below undulating very slowly in "
                       "place, its soft surface breathing as low billows swell and sink back again, the "
                       "gaps over the village lights neither opening nor closing"},
            {"name": "star_field", "box": [0.0, 0.0, 1.0, 0.38], "still": True},
        ],
    },
    "ladder": {
        # PER-STATE `rigid`. Without it `render_prompt` falls back to DEFAULT_RIGID — "The
        # buildings, walls, stonework, ground and horizon" — which names BUILDINGS on a bare rock
        # platform. Naming a thing that is not in the frame is how a stabiliser starts inviting
        # the model to draw it, which is the failure the header note records for the guardroom.
        "rigid": ("The timber ladder and its rungs, the dark wet rock walls, the stone-and-timber fuel-store, its plank door and its stacked cordwood, the iron fire-basket, the brass spyglass and its folding tripod, the flagged shelf, the cut stone steps climbing away, and the glacier, ridgelines and snowfields"),
        # "all it needs to focus on is getting slow motion in the river down below. That's all it needs."
        # `ladder_head` — the loop's pin on the sheer face above the ladder — is dropped; `rigid` covers
        # it. The fire-basket pin STAYS: a lit basket here spends the scenario's one burning-beacon image
        # early, which is the world pin the header note calls the one that matters most.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER, PIN_STARS],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "river_glimmer", "box": [0.54, 0.555, 0.62, 0.72], "hero": True,
             "phrase": PH_RIVER_NIGHT},
            {"name": "fire_basket", "box": [0.02, 0.52, 0.22, 1.0], "still": True},
        ],
    },
    "anvil": {
        # PER-STATE `rigid`. Without it `render_prompt` falls back to DEFAULT_RIGID — "The
        # buildings, walls, stonework, ground and horizon" — which names BUILDINGS on a bare rock
        # platform. Naming a thing that is not in the frame is how a stabiliser starts inviting
        # the model to draw it, which is the failure the header note records for the guardroom.
        "rigid": ("The shattered rock-plate tableland and its shoulders, the dry-laid slab table, the iron fire-basket on its plinth, the timber fuel-store and stacked cordwood, the brass spyglass and its tripod, the cairns at the extreme edges, and the far ranges"),
        # "it could just go for the stars moving over the river."
        # READ AS THE WATER, NOT THE SKY, and this is the one place I have chosen an interpretation.
        # Taken literally it asks for two things this pipeline cannot give: stars are point lights (the
        # angular-size trap) and "moving over" is net travel, which a two-ended loop expresses only as
        # something crossing the frame. Canon has the exact case — "never name a rigid thing as the thing
        # that moves, not even as a reflection; if you want a reflection to move, say the WATER moves" —
        # so the hero is the river carrying broken starlight, and PIN_STARS holds the sky itself dead
        # still. One word changes it back if the sky is what he meant.
        # This state is also the parked colour-drift case: its whole-frame brightness arc is not something
        # a render fixes, so if the new clip still breathes, tick `flatten brightness` in the Baked tab.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER, PIN_STARS],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "river_glimmer", "box": [0.44, 0.51, 0.68, 0.62], "hero": True,
             "phrase": "the pale braided channels of the river on the dark flats far below glimmering "
                       "faintly and shifting very slowly in place, the reflected starlight breaking and "
                       "re-forming in small points along the wet gravel while the channels stay exactly "
                       "in their present courses"},
            {"name": "fire_basket", "box": [0.31, 0.53, 0.40, 0.70], "still": True},
        ],
    },
    "shears": {
        # PER-STATE `rigid`. Without it `render_prompt` falls back to DEFAULT_RIGID — "The
        # buildings, walls, stonework, ground and horizon" — which names BUILDINGS on a bare rock
        # platform. Naming a thing that is not in the frame is how a stabiliser starts inviting
        # the model to draw it, which is the failure the header note records for the guardroom.
        "rigid": ("The two shear rock blades and the notch between them, the dry-laid platform, the iron fire-basket on its stone base, the fuel store, the brass spyglass and its tripod, the reading slab, and the snow peak and far ranges"),
        # "it should just focus on slow movement and the river down below." Measured p95 15.80 ALIVE, the
        # liveliest river in the night set, so the phrase is the shared one and the work is all in the
        # company it keeps: the lamps are unnamed and the basket stays pinned.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER, PIN_STARS],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "river_glimmer", "box": [0.36, 0.70, 0.50, 0.88], "hero": True,
             "phrase": PH_RIVER_NIGHT},
            {"name": "fire_basket", "box": [0.83, 0.46, 0.90, 0.58], "still": True},
        ],
    },
    "broken_tooth": {
        # PER-STATE `rigid`. Without it `render_prompt` falls back to DEFAULT_RIGID — "The
        # buildings, walls, stonework, ground and horizon" — which names BUILDINGS on a bare rock
        # platform. Naming a thing that is not in the frame is how a stabiliser starts inviting
        # the model to draw it, which is the failure the header note records for the guardroom.
        "rigid": ("The broken summit tooth and its shattered crest, the dry-laid platform, the iron fire-basket, the fuel store and cordwood, the brass spyglass and its tripod, the reading slab, the gorge walls, and the green shelf and its villages across the gorge"),
        # "just needs to focus on twinkling lights in the village." THE ONE STATE WHERE LAMPS ARE THE
        # HERO, and it earns it: these villages are on the green shelf directly across the gorge, not
        # down on a distant valley floor, and they measured p95 6.88 with lit p95 26.43 — ALIVE. Canon's
        # rule is that "twinkling lights" needs a carrier and a distant point of light is not one; here
        # the carrier is a lit WINDOW with real area on screen.
        # The pin below was called `river_glimmer` by the loop while its phrase pinned the cliff and the
        # fire-basket — a name that would send the next reader looking for water. Renamed to what it is.
        "has_document": True,
        "pinned": [PIN_RIVER, PIN_SNOW, PIN_BASKET, PIN_PAPER, PIN_STARS],
        "negatives": [NEG_WORLD + NEG_FIRE],
        "subjects": [
            {"name": "village_lamps", "box": [0.35, 0.425, 0.77, 0.50], "hero": True,
             "phrase": "the lit windows of the three small villages on the green shelf across the gorge "
                       "twinkling gently, each window holding its own place and its own steady glow "
                       "while its light shivers very slightly as if seen through cold moving air"},
            {"name": "cliff_and_basket", "box": [0.40, 0.50, 0.60, 0.60], "still": True,
             "phrase": "The sheer cliff face below the shelf and the cold iron fire-basket in front of "
                       "it are fixed and dark: no water, no glimmer, no flame and no ember appears on "
                       "either of them."},
        ],
    },
}


def build(room):
    """The full spec for a room, tagged with room/state for the render's filenames.

    Returns None for a room carrying `keep` — "leave this one exactly as it is". Those rooms have
    committed clips Lucas has asked to keep (ladder, whistlegate, kiln, crown), and re-deriving their
    spec from this file would be a silent way to invalidate art that is already finished. Their spec
    text is still HERE, verbatim, because this file's job is to be the complete record; `keep` separates
    "we know how this was authored" from "we intend to write it again".
    """
    if SPECS.get(room) is None or SPECS[room].get("keep"):
        return None
    s = dict(SPECS[room])
    s["room"], s["state"] = room, "base"
    return s


def build_night(room):
    """The night sub-spec for a room, or None if this file does not author one.

    None means "whatever is on the node stays" — see the NIGHT docstring. A state authored here REPLACES
    the node's copy for that state and nothing else in `states` is touched.
    """
    n = NIGHT.get(room)
    if n is None:
        return None
    s = dict(n)
    s["room"], s["state"] = room, "night"
    return s


def _main():
    write = "--write" in sys.argv
    show = "--show" in sys.argv
    doc = json.load(open(P, encoding="utf-8"))
    keys = [r["key"] for r in doc["rooms"]]
    missing = [k for k in keys if k not in SPECS]
    extra = [k for k in SPECS if k not in keys]
    night_extra = [k for k in NIGHT if k not in keys]
    if missing or extra or night_extra:
        print("!! room coverage mismatch — missing %s, unknown %s, unknown night %s"
              % (missing, extra, night_extra))
        return 1

    bad = 0
    for room in keys:
        node = next(r for r in doc["rooms"] if r["key"] == room)
        prev = (node.get("authoring") or {}).get("motionSpec") or {}
        spec = build(room)
        night = build_night(room)

        if spec is None and night is None:
            print("%-14s unchanged (kept on the node)" % room)
            continue

        # ---- validate everything we are about to write, base and night alike -----------------------
        for tag, s in (("base", spec), ("night", night)):
            if s is None:
                continue
            errs = MS.validate(s)
            movers = [x for x in s["subjects"] if not x.get("still")]
            heroes = [x for x in movers if x.get("hero")]
            print("%-14s %-5s %d mover(s), %d hero, %d pinned  %s"
                  % (room, tag, len(movers), len(heroes), len(s["subjects"]) - len(movers),
                     "OK" if not errs else "ERRORS"))
            # ONE OR TWO HEROES IS THE POLICY (cinemagraph_tools/AGENTS.md -> GET THE HERO MOTION ALIVE,
            # THEN STOP), and a spec with none is the failure that policy is most likely to reintroduce:
            # it silently falls back to the legacy "only convict when EVERYTHING is dead" rule, so the
            # room can ship with its intended motion missing and nothing objects. Checked here rather
            # than in `motion_spec.validate`, which must keep accepting the pre-flag specs.
            if not heroes:
                print("    ! no `hero` subject — the liveness gate has nothing to hold this state to")
                bad += 1
            elif len(heroes) > 2:
                print("    ! %d heroes (%s) — one or two" % (len(heroes), ", ".join(h["name"] for h in heroes)))
                bad += 1
            for e in errs:
                print("    ! " + e)
                bad += 1
            if show:
                print("    + " + MS.render_prompt(s)[:600] + " …\n")

        if not write or bad:
            continue

        # ---- merge, never replace -------------------------------------------------------------------
        # PRESERVE THE STATES BLOCK. Night sub-specs for rooms this file does not author (and the whole
        # `order_sent` state on crown) live only on the node, and writing a base spec over the node
        # wholesale would delete them — leaving a full-scene variant with no spec and therefore no clip,
        # which is the "a state with no clip of its own goes completely static" failure in
        # cinemagraph_tools/AGENTS.md.
        out = dict(spec) if spec is not None else dict(prev)
        states = dict(prev.get("states") or {})
        if night is not None:
            states["night"] = night
        if states:
            out["states"] = states
        node.setdefault("authoring", {})["motionSpec"] = out

    if write and not bad:
        json.dump(doc, open(P, "w", encoding="utf-8"), indent=2)
        print("\nwritten")
    elif write:
        print("\n!! NOT written — %d problem(s) above" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_main())
