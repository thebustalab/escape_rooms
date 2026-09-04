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

SPECS = {
    # ── first light on the moored ship: a glassy harbour and the Pharos still lit ──────────────────
    "deck": {
        "rigid": SHIP_RIGID,
        "has_document": True,
        "pinned": ["The written tablet and the open ledger on the deck table lie flat and still; their "
                   "ruled lines and lettering do not move, lift, curl or change."],
        "negatives": [", rising water, waves breaking over the deck, the ship sailing away, sails "
                      "unfurling, fast moving clouds, time-lapse sky"],
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
    "market_boast": {
        "rigid": STREET_RIGID + ", and the great pyramid of stacked amphorae behind the counter",
        "has_document": True,
        "pinned": ["The hanging reject-slate and the open ledger on the counter lie exactly as they are: "
                   "their chalked marks, ruled lines and lettering do not move, smudge, lift, curl or change.",
                   "The great pyramid of stacked amphorae is solid and fixed: no jar shifts, rocks, "
                   "rolls or falls."],
        "negatives": [", people, amphorae falling, the stack collapsing, fire spreading, the stall burning"],
        "subjects": [
            {"name": "brazier_smoke", "box": [0.5475, 0.0162, 0.7394, 0.8441], "force_repair": True,
             "phrase": "the cauldron on its brazier beside the counter, a thin column of smoke rising off "
                       "it and curling away, the coals beneath glowing and dimming"},
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
        "pinned": ["Every open ledger, scroll, wax tablet and written sheet in the hall lies flat and "
                   "dead still: no page turns, lifts, curls or changes, and no lettering moves.",
                   "The scrolls stacked in the wall-niches and piled on the floor do not move, shift, "
                   "roll or fall."],
        "negatives": [", people, pages turning, pages fluttering, pages lifting, books opening or "
                      "closing, scrolls unrolling, scrolls rocking, the clock dial or its pointer "
                      "turning, the clock swaying, fast moving clouds"],
        "subjects": [
            {"name": "window_veils", "box": [0.735, 0.140, 0.888, 0.552],
             "phrase": "the tall sheer linen veils hung down the right-hand wall, breathing slowly in "
                       "and out in the draught and settling back against the shelving"},
            {"name": "dusk_shaft", "box": [0.575, 0.075, 0.722, 0.555], "force_repair": True,
             "phrase": "fine dust hanging thick in the broad shaft of last gold light from the high "
                       "arched window, turning and drifting slowly down through the beam"},
            {"name": "clock_water", "box": [0.308, 0.330, 0.345, 0.432], "force_repair": True,
             "phrase": "the thin ribbon of water falling from the water-clock's upper cistern into the "
                       "graduated tank below, and the water trembling where it lands"},
            # STILL PINS — enforced in the playback mask, not merely asked for. The hall is now full of
            # open ledgers and stacked scrolls, so the paper risk is far larger than it was in the bare
            # room; these are the largest and most legible written surfaces in the frame.
            {"name": "clock_dial", "box": [0.290, 0.145, 0.362, 0.328], "still": True,
             "phrase": "The great bronze clock dial and its long pointer are motionless."},
            {"name": "clock_tank", "box": [0.283, 0.432, 0.378, 0.872], "still": True,
             "phrase": "The clock's graduated tank, its gearing and its stone plinth are solid and "
                       "completely still."},
            {"name": "great_table_docs", "box": [0.450, 0.540, 0.570, 0.645], "still": True,
             "phrase": "The open ledgers heaped on the archivist's great desk lie flat and unmoving."},
            {"name": "mid_right_desks", "box": [0.700, 0.560, 0.845, 0.740], "still": True},
            {"name": "right_desks", "box": [0.840, 0.585, 1.000, 0.880], "still": True,
             "phrase": "The scrolls, ledgers and tablets covering the near working desks are fixed "
                       "where they lie."},
            {"name": "left_scrolls", "box": [0.000, 0.600, 0.130, 0.870], "still": True,
             "phrase": "The bundles of rolled scrolls stacked along the foot of the wall are inert."},
        ],
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
    "pharos": {
        "rigid": TOWER_RIGID,
        "has_document": True,
        "pinned": ["The bronze relief panel beside the door is fixed: its carved symbols and marks do not "
                   "move, shift, glow in sequence or change.",
                   "The great bronze door stays SHUT and does not move, swing or open."],
        "negatives": [", the door opening, the door swinging, people, rain, storm, lightning"],
        "subjects": [
            {"name": "door_edge_glow", "box": [0.435, 0.10, 0.565, 0.82], "force_repair": True,
             "phrase": "the hot gold light escaping around all four edges of the sealed bronze door, its "
                       "brightness surging and easing as the fire behind it works"},
            {"name": "floor_rays", "box": [0.39, 0.70, 0.63, 1.0],
             "phrase": "the long rays of that light thrown across the paving, brightening and dimming "
                       "with it"},
            {"name": "sea_and_rocks", "box": [0.84, 0.40, 1.0, 0.96],
             "phrase": "the black sea working against the rocks below the parapet, white water rising and "
                       "falling back in place"},
            {"name": "city_lights", "box": [0.62, 0.30, 0.99, 0.44],
             "phrase": "the lamps of the city along the far shore, each small light breathing and steadying"},
            {"name": "stair_lamp", "box": [0.595, 0.73, 0.635, 0.84],
             "phrase": "the small lamp burning at the head of the stair, its flame live and wavering"},
        ],
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
    "deck": [
        {"name": "pharos_flame", "box": [0.272, 0.17, 0.318, 0.29], "force_repair": True,
         "phrase": "the signal fire burning at the head of the distant Pharos, a hot gold flame leaping "
                   "and guttering against the black sky"},
        {"name": "flame_track", "box": [0.27, 0.48, 0.32, 0.60],
         "phrase": "the broken gold reflection of that fire lying on the dark harbour below it, "
                   "shattering and re-forming as the water moves"},
        {"name": "moon_track", "box": [0.05, 0.46, 0.11, 0.86],
         "phrase": "the long silver track the moon lays across the water, breaking and closing again"},
        {"name": "deck_lamp", "box": [0.648, 0.80, 0.695, 0.95],
         "phrase": "the lamp burning in the open deck hatch, its flame live behind the horn, its warm "
                   "light breathing over the timbers"},
        {"name": "city_lights", "box": [0.62, 0.26, 0.99, 0.62],
         "phrase": "the lit windows and quay lamps of the city along the shore, each small light "
                   "breathing and steadying, their reflections trembling on the water beneath"},
        {"name": "night_sea", "box": [0.0, 0.46, 0.36, 0.76],
         "phrase": "the dark harbour lying almost still, only a slow swell moving under the reflections"},
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
        {"name": "table_lamps", "box": [0.455, 0.515, 0.575, 0.564], "force_repair": True,
         "phrase": "the oil lamps standing among the ledgers on the archivist's great desk, each flame "
                   "live and unsteady, throwing moving warm light without moving a single page"},
        {"name": "desk_lamps_near", "box": [0.864, 0.568, 0.898, 0.620], "force_repair": True,
         "phrase": "the lamp burning on the near working desk, its flame wavering and steadying and its "
                   "pool of light breathing on the scrolls and the shelving behind"},
        {"name": "moon_shaft", "box": [0.575, 0.075, 0.722, 0.555], "force_repair": True,
         "phrase": "the pale cold shaft of moonlight falling from the high arched window, fine dust "
                   "turning and drifting slowly down through it"},
        {"name": "window_veils", "box": [0.735, 0.140, 0.888, 0.552],
         "phrase": "the tall linen veils hanging pale in the moonlight down the right-hand wall, "
                   "breathing slowly in and out in the night draught"},
        {"name": "clock_water", "box": [0.308, 0.330, 0.345, 0.432], "force_repair": True,
         "phrase": "the thin ribbon of water still falling from the water-clock's upper cistern into the "
                   "graduated tank below, catching the lamplight as it goes"},
        {"name": "clock_dial", "box": [0.290, 0.145, 0.362, 0.328], "still": True,
         "phrase": "The great bronze clock dial and its long pointer are motionless."},
        {"name": "clock_tank", "box": [0.283, 0.432, 0.378, 0.872], "still": True,
         "phrase": "The clock's graduated tank, its gearing and its stone plinth are solid and "
                   "completely still."},
        {"name": "great_table_docs", "box": [0.424, 0.566, 0.570, 0.606], "still": True,
         "phrase": "The open ledgers and scrolls spread across the archivist's great desk lie flat and "
                   "dead still."},
        {"name": "right_ledger", "box": [0.820, 0.598, 0.862, 0.652], "still": True,
         "phrase": "The great open ledger on the near working desk does not move a page."},
        {"name": "right_cart_scrolls", "box": [0.858, 0.648, 0.946, 0.885], "still": True},
        {"name": "right_scroll_stacks", "box": [0.962, 0.650, 1.000, 0.760], "still": True},
        {"name": "left_scrolls", "box": [0.000, 0.600, 0.130, 0.870], "still": True,
         "phrase": "The bundles of rolled scrolls stacked along the foot of the wall are inert."},
    ],
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
