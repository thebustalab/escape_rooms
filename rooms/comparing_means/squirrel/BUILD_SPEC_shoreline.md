---
authority: intent
---

# Build spec — Seedfall shoreline rebuild + spa re-siting (2026-10-17, session "new room")

Everything here was agreed with Lucas in chat on 2026-10-17. The live design record is now `notes.md`
(this folder); the decision trail through the abandoned settings is
`z_archive/redesign_genoa_notes_2026-10-17.md`.

## The design in one paragraph

**Seedfall (`comparing_means/squirrel`, codec id 13) is the graded, in-class, two-player scenario.**
The world is one long, steep Genoa-style shoreline city: tall ochre, salmon and slate stucco palazzi stacked
in five levels up a near-vertical sea cliff, with terraced nut-orchard gardens and loggias/balconies over the
water. Travel is by iron-and-glass lift towers and stone stairways. A line of bell towers and a stone-lidded
aqueduct runs along the clifftop. There is a harbour at one end and a lighthouse at the other.

The two players start at **opposite ends**: the lower player at the harbour on level 1, the upper player
just outside the lighthouse below the level-5 garden. Each does an out-and-back on their own levels (lower 1-3, upper 3-5), turning at
the **middle garden on level 3**, which both share. **The first snow sets in for the return.**

Split the METHOD over shared data: one player parametric, the other rank-based (hub canon → *TWO-PLAYER
SCENARIOS*). No server sync. The escape is data-free: **five garden varieties, one per level.** The lower
player learns the order of levels 1-3, the upper player levels 3-5, and the level-3 variety links them.
Only the pair together can order all five. Each player enters the answer on their own console at their
own start.

**`comparing_means/spa` (codec id 12) becomes at-home practice in the same world, the morning after the
first snow.** A separate, ungraded whole-class rehearsal will later reuse this world. It is not part of
this spec.

## Art already settled (do not regenerate)

- Master plate: `_world/plate.png` (= `world_plates/shore_master_maxres_20261017/shore_master_2.png`,
  3520x2352, `--quality max`, generated from scratch).
- Plate set, each made in one step from the master with the master as reference:
  `world_plates/shore_set_20261017/`.
  - `first_snow.png`: the snow state.
  - `snow_dawn.png`: spa's morning.
  - `from_harbour_up.png`: the lower player's start.
  - `middle_close.png`: the turn.
  - `from_lighthouse.png`: the lighthouse end (seen from above the lighthouse).
- Harness card strip: `_world/plate_display.png`. Viewing only. Never pass it to a generation
  (`harness_server._world_plate_display_abs`).
- **Art rules from Lucas.**
  - No edit-of-an-edit chains. They drift cartoony. Every image is either generated from scratch or one
    step from an accepted master.
  - Flat plates use `--size 3520x2352 --quality max`.
  - Room panoramas follow the normal pipeline (`xhigh`, `scene_spec.render_prompt`; see
    `authoring_v2/ref_plates_and_model.md`). Per-room `authoring.plateRefs` can name the plate-set files.
- The lift-ride proof of concept is in `_scratch/lift_transit/`. It has two known flaws, listed in the
  redesign notes. It is reusable for travel clips later. Not in scope here.

## Step 1 — make the folder's canon tell the truth

1. Park the jay-era material **before** rewriting anything. Use a temp path, then a single bare `mv` into
   a new `z_archive/` in this folder (root AGENTS → *Wrong content gets removed* / *Co-locate archives*).
   - Park: `notes.md`, `AGENTS.md`, `scenario.json`, `wiring_checklist.md`, `HANDOFF.md` (now a pointer to
     this spec), and the superseded plate menus (`vibe_menu_*`, `island_*`, `city_menu_*` except
     `menu_genoa_vertical_old_town.png`, `genoa_menu_*`, `fin_*`, `spur_*`, `gardens_mtn_*`,
     `cloudsea_derive_*`, `shore_2026*`, `shore_styleref_*`, `shore_steep_*`).
   - The `world_plates/` menus are optional: ask Lucas in your final summary rather than moving them
     unasked if unsure.
2. Write a new `AGENTS.md` (`authority: canon`, gitignored): scenario identity, the design paragraph
   above, dataset contract, ladder, rooms, engine dependencies. Keep it lean; don't record build state
   (hub rule).
3. Write a new `notes.md` (`authority: intent`). Fold in the still-true parts of
   `redesign_genoa_notes.md`, then archive that file into the same `z_archive/`.
4. Build a new `scenario.json` skeleton with a re-runnable builder in `_scratch/` (as the jay design
   had).
   - Two `enterButtons` (`[{label, role, startRoom}]`), one per player.
   - Rooms per the route below, each with `authoring.sceneSpec` / `plannedHotspots` stubs and
     `authoring.plateRefs`.
   - `state`, the snow variant, and `availableWhen` gating so each rung gates only its own player's next
     room.
   - Keep `id: 13`.
5. Run `validate_scenes.py`. It walks reachability from EVERY declared start (hub → `enterButtons`
   trap). Also run any scenario tests that exist.

## Step 2 — rebuild the dataset around soil (skill: `escape_room_puzzles`)

- Replace `data/nut_census.csv` with rooftop-garden soil or substrate chemistry. Write a deterministic
  generator in `_scratch/` with a fixed seed that **asserts** every property below. The old
  `_scratch/build_nut_census.py` is the template.
- **Ladder shape** (chapter 11): two means t-test → Wilcoxon (mean-vs-median trap) → ANOVA + Tukey /
  Kruskal-Wallis + Dunn → pairwise + multiple-comparison correction boss.
- **Two parallel ladders on the SAME data.**
  - The parametric player's rungs use t / ANOVA + Tukey / pairwise t + correction.
  - The rank player's rungs use Wilcoxon / Kruskal-Wallis + Dunn / pairwise Wilcoxon + correction.
  - Engineer the skew so the two methods **agree in most places and split in exactly the designed
    ones**, where both answers are defensible.
  - Which player (lower or upper) is parametric is open: pick one, flag it for Lucas.
- **Assert the escape is unsolvable from the CSV:** no column or level name encodes cliff level or
  variety height order.
- Every answer must have: exact value + exact name + a single-winner margin + at least 6 data-derived
  distractors (skill rules). The functions must run in WebR (hub *WebR compatibility*).

## Step 3 — room network → scene specs (skills: `escape_room_network`, `escape_room_scenes`, then `escape_room_content` for prompts)

**Lower player's route** (the upper player mirrors it on levels 5 → 3 from the lighthouse):

| # | Room | Move in |
|---|---|---|
| 0 | Harbour garden, level 1 | START + escape console |
| 1 | Level 1 garden | walk |
| 2 | Level 2 garden | lift up (rung 1) |
| 3 | Level 2 garden | walk |
| 4 | Level 3 garden | stairs up (rung 2) |
| 5 | MIDDLE garden, level 3 | walk. The turn, shared by both players; snow begins |
| 6 | Level 1 garden | cart down two (rung 3, now in snow); the boss is here |
| 7 | Level 2 garden | stairs up |
| 8 | Level 1 garden | lift down |
| 9 | Harbour garden | walk back to start: the escape board, then the stair to the light |

- This is about 9 transits each, with 3-4 lift rides. Lucas asked for at least 8. Every vertical move
  teaches one above/below relation. Each garden's variety must be legible in its art.
- Every room needs **both states** (clear evening + first snow), because backtracking is allowed.
- The snow switch fires at the turn.
- Write each room's `sceneSpec` against the plate. Then run the pre-art gate (`authoring_v2/preflight.py`)
  and `validate_story.py` for the landing text.
- **Do not generate room art in this pass** unless Lucas says so. Specs, content and gates only.

## Step 4 — re-site spa (`rooms/comparing_means/spa/`, its `AGENTS.md` + `notes.md`)

- **Setting:** the city's bathhouse, cut into the cliff at the waterline. The saltwater bath is now
  sea-fed. The rival arrives by funicular up the cliff from the harbour. Set the morning after Seedfall's
  first snow. Use `world_plates/shore_set_20261017/snow_dawn.png` as its plate reference.
- **Names:** give Fjellro and Dagny Vold Italian equivalents (propose two or three options each for
  Lucas).
- **Escape:** move it from `piste` (ski slope) to a **clifftop bell tower**. Its unbuilt mechanic #16 is
  a bell-pull, so the bell cords are now literal. Keep the candle-size recognition logic unless it
  conflicts.
- **Art (Lucas, 2026-10-17): ALL spa room art is redone** — every room, plus the new bell-tower escape
  room. The only art that stands anywhere in this world is Seedfall's plate set. So re-spec every spa
  room's `sceneSpec` against the shoreline plate (`snow_dawn.png` as its plate reference); mark the old
  art for replacement; don't generate the new art in this pass unasked.
- Data, ladder and codec id 12 stay unchanged. Update the landing text, entry cards and names
  consistently.

## Status (2026-10-18) and the next step — Lucas's sign-off, then art

Steps 1-4 above and harness flow step 4 (`escape_room_geography`) are DONE and Sonnet-checked, except
the one sign-off that is Lucas's. The settled design is in `AGENTS.md` and `notes.md`.

- **Plates** unchanged (frozen). **Specs reconciled to them** in `_scratch/scene_specs.py`: the lighthouse
  stands below the level-5 lighthouse garden on its own rocky crag at the sea (`LIGHTHOUSE_LOW`), and the
  upper player's board is set into the keeper's house wall at the lighthouse; the per-terrace tree exclusion stays, with
  a far black cypress skyline allowed (`SKYLINE_CYPRESS`) in rooms that see the clifftop; `lo_2a`'s
  outlook puts the harbor to the right along the cliff foot.
- **Landing text drafted** in the builder: `story`, `done` (+ `byRole`), `escapeDone`, `debrief` intro,
  every `lockedBody`, the guild card. `validate_story.py` runs clean apart from the missing snapshot.
- **Verify scripts**: `_scratch/verify_ladder.py` (re-derives all eight option sets in R) and
  `_scratch/verify_escape.py` (CSV cannot encode the level order; LEAF_WORD/VARIETIES one-to-one).
- **Escape redesign (Lucas, 2026-10-18)** wired: wordless emblem × leaf-colour planting board, a
  spiral-stair room and a light room with a lever per player (`lo_stair`, `lo_lantern`, `up_stair`,
  `up_lamp`), decoy colours, and the upper start moved outside the lighthouse with a rock-stair connector
  (`up_rock`) to the clifftop garden (`up_5g`); 24 rooms, the lamp-lighting stakes in the landing text, new done and escape cards. Design in
  `notes.md` → *Escape purpose, mechanism and finale*; `verify_escape.py` (3) pins the wiring.
- **Pre-art gate PASSED and stamped 2026-10-18** after Lucas approved the opener (the agent ran
  `validate_story.py --accept` at his explicit request). One non-blocking box-overlap warning: the
  harbour's stair door shares a slot with its walkway.

**Next (Lucas, 2026-10-18: "the usual order"): the CONTENT step first, then the art.**

1. **Content step: DONE 2026-10-18.**
   - All eight graded puzzles are on `plannedHotspots`, written by the builder: `CONTENT`, `final_options()` and `rung()`.
   - Option texts come only from `soil_ladder_key.json`. The R1 and R2 curation follows notes.md.
   - `ladderPlain` and `escapeBrief` are written.
   - The hints use the book's own calls (`tTest`, `tukeyTest` and the rest), which the shared console provides.
   - `verify_ladder.py` section (6) re-derives the WIRED option sets in R and pins the content rules. Its break test fails as it should.
   - Preflight re-stamped. A Sonnet check confirmed it, and its two findings are fixed: no key sits first or last, and each `ladderPlain` entry is one sentence.
   - The book's test functions now come from the shared console. They are browser-verified, including the `p.adj` columns and the Holm default. A full Seedfall play-through in a browser is still owed at closeout.
2. **RELAUNCHED 2026-10-18 15:47 EDT**, with the ERP guide on every room and the harbour water kept off the seam wall. The 15:10 run was stopped and archived as `z_archive/_long_agent_room_iterate_flat_2026-10-18`, and its two flat stills were discarded.
   **First launched 2026-10-18 15:10 EDT** on Lucas's go: `room_iterate` for all 24 rooms, max 2 renders per room and 72 generations, not End-Day-gated. The detached driver (`--max-hours 22`, log `/tmp/squirrel_drive.log`) is chained to `finish_scenario_art.py`. Job state: `_long_agent/state.json`.
   **The overnight art run** (`escape_room_art_pipeline` skill, `room_iterate`) for all 24 rooms,
   on Lucas's go-ahead. Image jobs need `OPENAI_API_KEY` (login shell only: `setsid nohup bash -lic`).
   Watch first renders of `lighthouse`, `up_rock`, `up_5g`, `up_stair`, `up_lamp`, `lo_lantern`: the
   frozen plates show the lighthouse LIT and every still must show it dark (`LAMP_DARK` is appended to
   those prompts). The finale transit (lever → lamp lights → pull-back to a 360 of the lit, snowy city)
   is noted on each lever's planned door.

Open contents detail: the `harbour` room puts the moored boat "to the right" while facing the
lighthouse; on the plates the basin lies harbor-ward, behind that facing.

## Working method (Lucas asked for this)

- **Use subagents to help AND to check their work.**
  - Fan out genuinely parallel pieces (e.g. the dataset generator vs the spa re-siting) to subagents
    with tight briefs carrying the goal and priorities (root AGENTS → *Brief a worker on the why*).
  - Name the relevant `escape_room_*` skill file in each brief: subagents don't inherit skills.
- **Checking:** after each step, run the `adversarial_check` skill. The adversary is always **Sonnet**.
  It verifies against the real files and runs the tests itself. Fold its findings back in before the
  next step.
- **Long runs:** in-process `Agent` subagents die at the turn boundary on mobile. Anything long (a
  multi-draw image job, an overnight build) goes through the detached launcher
  `Utilities/security_audit/unattended_claude.py launch ...` with an explicit tool list (root AGENTS),
  or `setsid nohup bash -lic` for scripts.

## Acceptance checks

- No live file in this folder mentions the jay, the wood, the fin or the cloud sea except as history in
  `z_archive/`.
- `scenario.json` parses, has two `enterButtons`, and passes `validate_scenes.py` from both starts.
- The dataset generator re-runs deterministically and its asserts pass:
  - the method agreements and splits are as designed
  - every answer has a single winner and at least 6 distractors
  - the escape is not recoverable from the CSV
- Every room has a `sceneSpec` and both states; the pre-art gate passes or its failures are listed.
- Spa: new names proposed, the escape relocated in its spec, every room re-specced against the shoreline plate,
  and its `AGENTS.md` updated.
- Each step has a Sonnet adversarial-check pass whose findings were addressed or reported.

## Open for Lucas (list these in your final summary; don't block on them)

Settled 2026-10-17: methods alternate per rung (each player two parametric, two rank; partners opposite at
every rung); placeholder varieties kept; spa names Calmarupe / Diana Volpe; spa keeps five candles in the
belfry; superseded plate menus archived. Still open:

- Protagonist wording (human rooftop gardener; role name open).
- The middle garden as two room nodes (one per player's end).
- The dataset's garden and soil-mix names.
