#!/usr/bin/env python3
"""_motion_specs.py — the canyon's motion specs, authored once and written onto the room nodes.

WHY THIS EXISTS AS A FILE. A motion spec is not derivable from the art: it is a judgement about what
should move in a scene, and the handoff's standing complaint is that a variant shipped with **no recorded
prompt at all** (quay's night). So the spec lives on the room node (`authoring.motionSpec`), and this
script is the record of how it was authored — re-run it to restore or revise.

BOXES. Taken from the scene spec's own left-to-right layout convention (`scene_spec.approx_boxes` maps
"to the left" / "dead ahead in the centre" / … onto x-slots), with the y-range set by what the feature IS
rather than by that helper's fixed 0.25–0.80 band: water sits on the floor, sky sits overhead, a light
shaft spans the wall. Coarse on purpose — these boxes are measurement regions for the liveness gate, not
hotspot boxes, and p95-within-box is what makes a small bright thing in a large box still readable
(motion_spec's measurement decision 1).

WHAT IS AND ISN'T NAMED. Only oscillatory phenomena — water surfaces, falls, spray, haze, drifting dust,
breathing lamplight. The recipe pins frame 0 and frame -1 to the same still, so a two-ended loop cannot
express net travel; naming anything that must GO somewhere just produces a fight the end-guide wins.
REVISION 2 (Lucas's review of the first nine clips, 2026-08-31). What his eye caught that the metrics
did not, and the fix for each:
  * **undercroft — "water taking over and flooding the scene, not cyclic."** still_flood measured 22.4
    ALIVE, which is the metric agreeing that something moved a lot; it cannot tell a rippling surface
    from a rising one. The phrase now pins the WATERLINE, and the negatives name flooding outright.
  * **"Throughout, lanterns are pretty still if not totally static."** They were never named. A subject
    that is not in the prompt is not animated and not measured — the scheme's blind spot is whatever you
    forgot to list. Every room now carries a lantern/candle subject, boxed by the localizer.
  * **j_c7 — "too intense, clouds dominate with really fast motion."** upslot_daylight measured 47.5,
    the highest number in the set, and nothing flagged it: the thresholds have a floor and no ceiling.
    Over-driven reads as excellent to a DEAD/WEAK/ALIVE scale.
  * **skies weak across the set, j_c5 too still.** Both are now `force_repair` subjects: WEAK is not
    auto-repaired by design, so a human verdict is how they get tiled.

REVISION 3 (Lucas's review of the re-baked set, 2026-09-01) — three rooms sent back for a full
re-render, and the diagnosis for each was in the PROMPT rather than in the model:
  * **undercroft — "water moving weirdly fast and over the stone walkway, there shouldn't be water
    there."** Both halves were authored. `still_flood`'s box ran to x=0.36, y=1.0 and the waterline
    crosses that rectangle DIAGONALLY, so its lower-right corner is flagged walkway that the prompt was
    calling "black floodwater"; the paving is wet-looking polished stone, so the model had every reason
    to believe it. The box is now the pool, the walkway is explicitly PINNED as dry stone, and
    `trunk_arch_water`'s "sliding slowly away ... as it goes" — a request for TRAVEL the loop cannot
    express — is now a motion in place.
  * **j_c5 — "the light is like a weird search light, and the droplets are too large."** The searchlight
    was asked for in as many words: "brightening and dimming as it goes". Worse, `light_shaft`'s box was
    three times the beam's real width, so blazing daylight was being named over the right-hand cliff.
    The droplets were asked for too — "single fat drops ... throwing a slow ring" — in a room whose name
    is The still pool. Both phrases are rewritten, both boxes measured off the panorama, and the
    `force_repair` flags dropped so the full frame is judged before anything is tiled.
  * **j_c7 — "good except everything is moving too fast."** Second rejection for speed. `upslot_daylight`
    is DELETED rather than calmed: there is no sky in this room, the upper-left is dark canyon wall, and
    naming "grey daylight" over it invited an invented moving sky that measured 47.53 — the highest in
    the set. Revision 2 tried to pin it still, but pinning a thing that is not there does not work.

THE PROMPT BUG UNDERNEATH ALL THREE. Lantern subjects are per-location (lights_1/2/3) because each
needs its own measurement box, but they share one phrase, and `render_prompt` was joining them
naively — so every prompt said "a live, restless flame that gutters and flares ... pulsing" THREE
TIMES, tripling the weight of the most energetic sentence in the scheme. `render_prompt` now
de-duplicates. That is very likely a bigger contributor to the over-driven clips than any single
phrase, and it applies to every room in every scenario.

Documents are the inverse trap: the drowned hall's hide map and the trunk's incised wall-map must be
explicitly PINNED, because the deck render grew a curling corner with crawling text until it was.
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "cinemagraph_tools"))
import motion_spec as MS  # noqa: E402

HARNESS = "http://127.0.0.1:8752"
CHAPTER, SCENARIO = "hierarchical_clustering", "canyon"

CANYON_RIGID = ("The canyon walls, banded rock, stone shelves, piers, survey stones, reading-tables, "
                "ladders and ground")
HALL_RIGID = ("The hall walls, carved piers, flagged floor, stone table, engraved panel, ladder and "
              "stonework")

# The calmed flame, for a room that came back over-driven. Same object, same behaviour, lower energy:
# "gutters and flares" and "pulsing" are strong words and they appear in every room's prompt.
# REV 5. The flame, and ONLY the flame. "their pools of amber light easing slowly on the wet stone"
# licenses the CAST LIGHT to change across whatever area it falls on — and in j_c7 a lamp stands right in
# front of the great carved wall-map, so that licence was being spent on a 15-unit luminance oscillation
# across the map's face. Rev 4 held the scene's overall brightness constant and halved the pulse; it did
# not remove it, because this sentence still asked for exactly the thing being forbidden elsewhere.
SLOW_FLAME_PHRASE = ("the hanging oil lanterns, the small flame inside each one wavering and settling "
                     "gently within its glass; the light they cast on the surrounding stone holds "
                     "steady and does not swell, pulse or spread")

SPECS = {
    # ── the drowned hall: still black water and lamplight, before the flood rises ──────────────────
    "undercroft": {
        "rigid": HALL_RIGID,
        "has_document": True,
        "pinned": ["The rolled hide map lies flat and still on the stone table; its incised channel "
                   "lines and marks do not move, lift, curl or change.",
                   "The water level is fixed: the flood does not rise, spread, surge or advance.",
                   "The flagged stone walkway and the paving across the foreground and the right of "
                   "the hall are DRY solid stone — wet-looking and polished, but stone. They do "
                   "not ripple, flow, shimmer or behave like water, and no water covers, creeps over "
                   "or spreads onto them."],
        "negatives": [", rising water, flooding, water level changing, water spreading across the floor, "
                      "surging water, waves, tide coming in, splashing, water covering the paving, "
                      "water creeping over the walkway, flooded walkway, wet floor rippling, the stone "
                      "floor turning to water, fast ripples, choppy water, churning water, rapid "
                      "surface motion, current, flowing water, sloshing"],
        "subjects": [
            # REV 3 BOX. The old box ran to x=0.36 and y=1.0, and the waterline runs DIAGONALLY across
            # that rectangle — so its lower-right corner is flagged walkway, and the prompt was
            # calling that corner "black floodwater". Measured off the panorama, the pool sits left of
            # x~0.30 and its edge falls from y~0.75 at x=0.37 to y=1.0 at x=0.13.
            {"name": "still_flood", "box": [0.03, 0.61, 0.22, 0.92],
             "phrase": "the black floodwater in the left of the hall lying dead flat and utterly level, "
                       "its mirrored lamplight stretching and easing across the surface in one very "
                       "slow breath — the waterline stays exactly where it is, hard against the "
                       "stone kerb, and the water neither rises, spreads nor creeps onto the paving"},
            # "sliding away ... as it goes" asked for TRAVEL, which a two-ended loop cannot express, so
            # the end-guide fights it, and that fight is what reads as speed.
            {"name": "trunk_arch_water", "box": [0.72, 0.62, 0.90, 0.86],
             "phrase": "dark water standing in the low carved arch on the right, its surface creasing "
                       "and smoothing very slowly in place"},
            # The haze box covered the whole central wall and measured 38.98 in a clip Lucas rejected.
            # Confined to the vault, and dialled down to almost nothing.
            {"name": "hall_air", "box": [0.30, 0.06, 0.72, 0.30],
             "phrase": "the faintest possible suggestion of damp air high under the hall's vault, "
                       "almost imperceptible"},
        ],
    },
    # ── j_c1 the high confluence: two clear spring-slots meeting under a ribbon of storm sky ───────
    "j_c1": {
        "rigid": CANYON_RIGID,
        "subjects": [
            {"name": "spring_fall", "box": [0.10, 0.18, 0.30, 0.86],
             "phrase": "a strong steady fall of clear water pouring down the throat of the left "
                       "tributary slot, breaking white where it lands and throwing up a shivering "
                       "spray that beads and runs off the wet rock"},
            {"name": "confluence_pool", "box": [0.34, 0.60, 0.68, 1.0],
             "phrase": "the clear pool where the two spring-slots run together, its surface alive with "
                       "wavelets and swirling eddies turning in place, the light shattering and "
                       "re-forming across it"},
            {"name": "sky_ribbon", "box": [0.0, 0.0, 1.0, 0.14],
             "phrase": "the thin ribbon of bruised pre-storm sky far overhead, its cloud churning slowly "
                       "in place"},
            {"name": "drifting_dust", "box": [0.56, 0.14, 0.88, 0.70],
             "phrase": "fine dust drifting slowly through the warm light against the shadowed banded "
                       "rock"},
        ],
    },
    # ── j_c2 the orphan junction: a milky seep braiding into clear spring water ────────────────────
    "j_c2": {
        "rigid": CANYON_RIGID,
        "subjects": [
            {"name": "orphan_seep", "box": [0.08, 0.26, 0.30, 0.88],
             "phrase": "the milky opalescent spring seeping out of the crack in the left wall and "
                       "running down the rock in thin threads"},
            {"name": "braided_pool", "box": [0.46, 0.58, 0.80, 1.0],
             "phrase": "the pool below the table where the milky seep and the clear spring water braid "
                       "together, the two waters curling past each other without mixing"},
            {"name": "sky_ribbon", "box": [0.0, 0.0, 1.0, 0.14], "force_repair": True,
             "phrase": "the narrow strip of bruised sky far above, its cloud rolling and folding in place"},
        ],
    },
    # ── j_c3 the left fork: two canyons folding into one faster channel ────────────────────────────
    "j_c3": {
        "rigid": CANYON_RIGID,
        "subjects": [
            {"name": "joined_channel", "box": [0.50, 0.58, 0.88, 1.0],
             "phrase": "the joined channel running fast below the shelf, the two waters folded into one, "
                       "its surface breaking and glinting as it goes"},
            {"name": "wall_seeps", "box": [0.04, 0.22, 0.32, 0.88],
             "phrase": "thin threads of water tracing down the banded rock at the mouths of the upper "
                       "slots, wet stone glistening"},
            {"name": "sky_hairline", "box": [0.0, 0.0, 1.0, 0.12], "force_repair": True,
             "phrase": "the hairline of bruised sky far overhead, its cloud rolling and folding in place"},
        ],
    },
    # ── j_c4 the bitter confluence: a sulphurous pool, slow bubbles, haze ──────────────────────────
    "j_c4": {
        "rigid": CANYON_RIGID,
        "subjects": [
            {"name": "bitter_pool", "box": [0.48, 0.58, 0.84, 1.0],
             "phrase": "the dull green-yellow pool where the two waters meet, slow bubbles rising and "
                       "breaking on its surface"},
            {"name": "bitter_haze", "box": [0.44, 0.32, 0.86, 0.72],
             "phrase": "a faint haze hanging over the bitter water, curling and thinning in place"},
            {"name": "crust_seep", "box": [0.06, 0.26, 0.32, 0.90],
             "phrase": "water trickling over the pale yellow mineral crust and the long rust-orange "
                       "stains bleeding down the left wall"},
            {"name": "sky_ribbon", "box": [0.0, 0.0, 1.0, 0.13], "force_repair": True,
             "phrase": "the strip of bruised sky far above, its cloud rolling and folding in place"},
        ],
    },
    # ── j_c5 the still pool: a mirror basin and a dust-thick shaft of daylight ─────────────────────
    "j_c5": {
        "rigid": CANYON_RIGID,
        # REV 3. Both of this room's headline subjects were asking for the artefact Lucas got.
        "negatives": [", pulsing light, flickering beam, strobing, searchlight, sweeping beam, moving "
                      "light beam, beam brightening and dimming, shafts of light sweeping, lens flare, "
                      "falling droplets, water drops, large droplets, dripping, splashes, ripple rings "
                      "spreading, raindrops, rain"],
        "subjects": [
            # The drops were AUTHORED: "single fat drops ... each one throwing a slow ring". The model
            # rendered what it was asked for, at the only scale it had ("fat"), and Lucas's verdict was
            # "the droplets are too large for the scene". A still pool is the room's NAME; nothing needs
            # to fall into it. Box pulled off the foreground rock ledge below y=0.88.
            {"name": "still_basin", "box": [0.09, 0.58, 0.40, 0.88],
             "phrase": "the wide mirror pool lying almost perfectly still, its reflection of the banded "
                       "walls easing and settling with the faintest slow swell — nothing falls "
                       "into it and nothing breaks its surface"},
            # THE SEARCHLIGHT, and it has two causes. (1) "brightening and dimming as it goes" is a
            # request for the beam's intensity to modulate, which is what a searchlight does. (2) the
            # box ran to x=0.78, three times the beam's actual width — it covered the right-hand
            # cliff, its lantern and the stone platform, so "blazing daylight" was named over solid
            # rock. Measured off the panorama the beam stands at x 0.535-0.615, reaching y~0.80.
            {"name": "light_shaft", "box": [0.535, 0.02, 0.615, 0.80],
             "phrase": "the soft column of pale daylight standing in the slot far above, its brightness "
                       "absolutely constant and unchanging, with only the finest motes of dust drifting "
                       "slowly within it"},
            # REV 4 (Lucas, 2026-09-01: "the water on the right hand side needs a patch"). This water
            # was NEVER NAMED. The room has two waters — the still mirror pool on the left and a
            # stepped weir-and-channel on the right — and only the pool was a subject, so the
            # channel was never prompted for, never measured and never repaired. It sat at p95 6.85:
            # WEAK, which by design is reported rather than auto-tiled, and there was no subject for
            # it to be reported under. The scheme's blind spot is whatever you forgot to list.
            {"name": "right_channel", "box": [0.60, 0.63, 0.82, 0.93],
             "phrase": "the stepped watercourse on the right, water running down over its weir and "
                       "along the cut channel below, breaking white on the stones and glinting as it "
                       "turns, the small fall at its head churning in place"},
            # Sky is visible only in the notch at top centre; a full-width box measured mostly rock.
            {"name": "sky_ribbon", "box": [0.44, 0.0, 0.56, 0.13],
             "phrase": "the narrow strip of bruised sky far overhead, its cloud turning over very "
                       "slowly in place"},
        ],
    },
    # ── j_c6 the right fork: the mirror of j_c3, running faster ────────────────────────────────────
    "j_c6": {
        "rigid": CANYON_RIGID,
        "subjects": [
            {"name": "joined_channel_r", "box": [0.50, 0.58, 0.88, 1.0],
             "phrase": "the joined channel running fast below the shelf, both waters folded into one, "
                       "its surface breaking white over the rock"},
            {"name": "wall_seeps", "box": [0.04, 0.22, 0.34, 0.88],
             "phrase": "thin threads of water tracing down the crusted rock at the mouths of the upper "
                       "slots, the wet stone glistening"},
            {"name": "sky_hairline", "box": [0.0, 0.0, 1.0, 0.10], "force_repair": True,
             "phrase": "the hairline of grey sky far overhead, its cloud rolling and folding in place"},
        ],
    },
    # ── j_c7 the trunk: every water in one deep channel, under the incised wall-map ────────────────
    "j_c7": {
        "rigid": CANYON_RIGID + ", and the incised wall-map and its cut lines",
        "has_document": True,
        # REV 3. Rejected TWICE for speed ("too intense ... really fast motion" 2026-08-31; "everything
        # is moving too fast" 2026-09-01), so this room gets the calmed flame as well as calmed phrases
        # — the lantern line is the one that appears in every room and it is the most energetic
        # sentence in the prompt.
        "flame": SLOW_FLAME_PHRASE,
        "pinned": ["The towering incised wall-map is cut into solid rock: its lines, clusters and marks "
                   "are perfectly still and do not move, shift or change.",
                   # REV 4. The word that has to be here is BRIGHTNESS, not movement. Rev 3 said every
                   # movement should be "a long, lazy, barely-there drift" and got a long, lazy drift
                   # of the whole centre's LUMINANCE — which is not movement, so nothing in the
                   # prompt forbade it and no gate looks for it (colour drift is measured and
                   # deliberately not gated, because a flame-lit room legitimately swings).
                   "The overall brightness of this scene is CONSTANT. The image does not brighten or "
                   "darken as a whole, no large area of wall or floor changes its luminance, and the "
                   "lamplight does not pulse across the scene. Only the small flames themselves vary.",
                   "The great carved wall-map face keeps exactly the same brightness from the first "
                   "frame to the last: it does not glow, dim, brighten, or have light wash across it.",
                   "Each movement is small and slow, and stays where it is."],
        "negatives": [", fast motion, rapid movement, hurried motion, churning, racing, time-lapse, "
                      "sped up, frantic, turbulent, choppy water, rushing water, whitewater, "
                      "flickering, strobing, fast moving clouds, racing clouds, churning sky, storm "
                      "rolling in, dramatic sky motion, global brightness change, exposure change, "
                      "scene brightening, scene darkening, whole image pulsing, luminance pulse, "
                      "glow expanding, light blooming across the wall, fade in, fade out"],
        "subjects": [
            # "moving deep and smooth" reads as FLOW, i.e. travel, which the loop forbids. Box lifted
            # off the dry paving in the lower left of the old rectangle.
            {"name": "trunk_channel", "box": [0.55, 0.68, 0.92, 0.97],
             "phrase": "the great dark channel where every water in the canyon has come together, lying "
                       "deep and nearly still, its surface creasing very slowly in place and holding "
                       "the lamplight"},
            # "its GLOW SWELLING and easing very slowly" is a request for a large area to change
            # brightness, and with rev 3's other subjects removed there was little else to spend motion
            # on, so it took the whole centre of the frame with it (18.7 luma swing against ~1 in the
            # rooms Lucas passed). Brightness held constant; the variation moved to the EDGE of the
            # light, which is a small thing that can move without the wall moving with it.
            {"name": "stair_lamplight", "box": [0.60, 0.34, 0.82, 0.84],
             "phrase": "the small warm pool of lamplight on the low arch and the worn steps below the "
                       "channel, holding a constant brightness, only its edge trembling very slightly "
                       "where it meets the stone"},
            # REV 4. Two more waters, deliberately. Rev 3 cut this room to three subjects and the model
            # spent its motion budget inventing a luminance ramp instead; competition for the frame is
            # a documented lever (cine_stage: an object animates when it is the dominant subject), and
            # it runs the other way too. Both of these are real water in the panorama.
            {"name": "left_channel", "box": [0.15, 0.55, 0.28, 0.80],
             "phrase": "the narrow channel below the left stair, its water creasing and glinting in "
                       "place as it passes"},
            {"name": "right_cascade", "box": [0.70, 0.24, 0.80, 0.58],
             "phrase": "the thin cascade slipping down the far right wall, breaking white on the ledges "
                       "it falls across"},
            # `upslot_daylight` IS DELETED, not calmed. THERE IS NO SKY IN THIS ROOM — the upper
            # left of the panorama is dark canyon wall. Naming "grey daylight" over near-black rock
            # invited the model to invent a bright moving sky there, and that subject then measured
            # 47.53, the highest number in the canyon set and the one Lucas called out both times.
            # Revision 2 tried to pin it still; pinning a thing that is not there does not work. The
            # room's own stale repair patch was for this subject and goes with it.
        ],
    },
    # ── works: the same hall with the flood rising and water pouring in ────────────────────────────
    "works": {
        "rigid": HALL_RIGID + ", and the iron sluice-wheel",
        "has_document": True,
        "pinned": ["The unrolled hide map lies flat and pinned on the stone table; its channel lines and "
                   "marks do not move, lift, curl or change."],
        "subjects": [
            {"name": "risen_flood", "box": [0.06, 0.52, 0.40, 1.0],
             "phrase": "the risen black floodwater lapping at the feet of the carved piers, its surface "
                       "heaving and slapping against the stone"},
            {"name": "pour_arch", "box": [0.66, 0.42, 0.94, 1.0],
             "phrase": "water pouring steadily in through the low carved arch and breaking white where "
                       "it lands"},
            {"name": "spray_air", "box": [0.32, 0.12, 0.80, 0.58],
             "phrase": "spray and heavy damp air hanging and curling through the lamplit hall"},
        ],
    },
}



# ── the practical lights, MEASURED (find_lights.py), not guessed ────────────────────────
# REVISION 3 (2026-08-31). Revision 2 added lantern/candle subjects on boxes from `localizer.py`, which
# returned a box per room at confidence 1.00 whether or not a lantern was there: j_c1's and j_c5's
# pointed at bare sandstone. Four tile repairs were spent animating rock, and — the part that matters —
# the LANTERNS WERE NEVER DEAD. Re-measured at their true boxes on the very same clips, every room
# scores 14-54 (ALIVE is >= 8). The prompt had named them all along; only the measurement was wrong.
#
# The lesson is narrow and worth keeping: a subject's BOX is part of the measurement, so a wrong box
# reports on whatever is inside it and says nothing about the thing you named. "Dead" always has two
# possible causes — it did not animate, or you are not looking at it.
LIGHTS = {
    "undercroft": [
        [
            0.6023,
            0.3441,
            0.621,
            0.4107
        ],
        [
            0.178,
            0.7055,
            0.1874,
            0.7336
        ],
        [
            0.2328,
            0.5307,
            0.2851,
            0.6295
        ]
    ],
    "j_c1": [
        [
            0.6673,
            0.558,
            0.6716,
            0.5816
        ],
        [
            0.4025,
            0.6674,
            0.4949,
            0.7498
        ],
        [
            0.7212,
            0.5385,
            0.7255,
            0.5621
        ]
    ],
    "j_c2": [
        [
            0.7351,
            0.551,
            0.7444,
            0.5896
        ],
        [
            0.4544,
            0.5055,
            0.4594,
            0.5355
        ],
        [
            0.376,
            0.5057,
            0.3975,
            0.5523
        ]
    ],
    "j_c3": [
        [
            0.8238,
            0.5457,
            0.8611,
            0.6896
        ],
        [
            0.7868,
            0.5854,
            0.7939,
            0.609
        ],
        [
            0.2877,
            0.7133,
            0.292,
            0.7262
        ]
    ],
    "j_c4": [
        [
            0.4193,
            0.5664,
            0.4251,
            0.6094
        ],
        [
            0.5055,
            0.5568,
            0.5199,
            0.5948
        ],
        [
            0.3185,
            0.6424,
            0.3264,
            0.6896
        ]
    ],
    "j_c5": [
        [
            0.2395,
            0.5451,
            0.2553,
            0.5782
        ],
        [
            0.8143,
            0.5761,
            0.8245,
            0.5899
        ],
        [
            0.7882,
            0.1215,
            0.7925,
            0.1344
        ]
    ],
    "j_c6": [
        [
            0.5794,
            0.5129,
            0.5837,
            0.5408
        ],
        [
            0.6743,
            0.5238,
            0.6786,
            0.5475
        ],
        [
            0.2719,
            0.6332,
            0.2776,
            0.6676
        ]
    ],
    "j_c7": [
        [
            0.5509,
            0.2313,
            0.5552,
            0.2463
        ],
        [
            0.2508,
            0.735,
            0.2645,
            0.808
        ],
        [
            0.7303,
            0.6465,
            0.7404,
            0.6787
        ]
    ],
    "works": [
        [
            0.2323,
            0.4898,
            0.2674,
            0.5629
        ],
        [
            0.5058,
            0.5687,
            0.5251,
            0.6354
        ],
        [
            0.3801,
            0.5957,
            0.3959,
            0.6602
        ]
    ]
}

FLAME_PHRASE = ("the hanging oil lanterns burning with a live, restless flame that gutters and flares, "
                "their pools of amber light pulsing on the wet stone")


def light_subjects(room):
    """One subject per measured light cluster. No `force_repair`: they animate on their own.

    A room may override the phrase with `flame` in its spec. j_c7 does, because it was rejected twice
    for over-driven motion and this is the most energetic sentence in any prompt. Note the subjects all
    SHARE one phrase and `render_prompt` de-duplicates it: the boxes are per-lantern because each has to
    be measured, but the prompt names lanterns once."""
    phrase = (SPECS.get(room) or {}).get("flame") or FLAME_PHRASE
    return [{"name": "lights_" + str(i), "box": b, "phrase": phrase}
            for i, b in enumerate(LIGHTS.get(room, []), 1)]


# The floodworks' OPEN state (2026-09-02). The scene is the same hall with the escape tunnel standing
# open, so it animates identically — the water and the lanterns are unchanged by the door. What it needs
# is a PIN: the opened tunnel is the payoff the player just earned, and a model given a dark rectangle
# will happily swing it, fill it, or close it. It is named as fixed, and the mouth is named as staying
# dark and empty so nothing is invented in the passage beyond.
WORKS_OPEN_PINNED = [
    "The escape tunnel stands OPEN and stays open: its stone door does not move, swing, close or change, "
    "and the dark passage beyond it stays empty — nothing appears in it, moves in it or comes out of it.",
    "The great iron sluice-wheel has been thrown and is at rest: it does not turn.",
]
WORKS_OPEN_NEG = (", door closing, door swinging, gate shutting, stone door moving, wheel turning, "
                  "figure in the doorway, light coming down the tunnel, something emerging from the passage")


def build(room):
    """The full spec for a room: subjects + framing, tagged with room/state for the render's filenames."""
    s = dict(SPECS[room])
    s.pop("flame", None)                       # authoring-side only; not part of the stored spec
    s["subjects"] = list(s["subjects"]) + light_subjects(room)
    if room == "works":
        # A variant's spec lives at `motionSpec.states.<state>` (cine_scenario.states_to_run). Same
        # subjects, same rigid list, plus the door pins — a variant is a DELTA, and the delta here is a
        # door that must not move, not a different set of things that move.
        s["states"] = {"open": {
            "rigid": s.get("rigid"),
            "subjects": [dict(x) for x in s["subjects"]],
            "pinned": list(s.get("pinned") or []) + WORKS_OPEN_PINNED,
            "negatives": list(s.get("negatives") or []) + [WORKS_OPEN_NEG],
            "has_document": s.get("has_document"),
        }}
    s["room"], s["state"] = room, "base"
    return s


def _main():
    write = "--write" in sys.argv
    bad = 0
    for room in SPECS:
        spec = build(room)
        errs = MS.validate(spec)
        print("%-12s %d subjects  %s" % (room, len(spec["subjects"]), "OK" if not errs else "ERRORS"))
        for e in errs:
            print("    ! " + e)
            bad += 1
        if not write or errs:
            continue
        # Read-modify-write the whole `authoring` blob: /api/room-patch sets top-level room fields, so
        # patching `authoring` wholesale would clobber the scene spec sitting beside it.
        doc = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
        node = next(r for r in doc["rooms"] if r["key"] == room)
        auth = dict(node.get("authoring") or {})
        auth["motionSpec"] = spec
        r = urllib.request.urlopen(urllib.request.Request(
            HARNESS + "/api/room-patch",
            data=json.dumps({"chapter": CHAPTER, "scenario": SCENARIO, "roomKey": room,
                             "fields": {"authoring": auth}}).encode(),
            headers={"Content-Type": "application/json"}), timeout=60)
        print("             written: %s" % json.load(r).get("ok"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_main())
