---
authority: intent
---

# Airship scenario ("The Alembic") — design record

Chapter `data_vis2`, scenario `airship`, codec **id 9** (hospital is id 8). Dataset: **`solvents`**.
Data-Vis-II **Q3** (solvent selection). Design conversation with Lucas, 2026-07-18. Durable schema
lives in `escape_rooms/AGENTS.md`; the mechanic catalogue + chapter principles live in
`../../../notes/puzzle_inventory.md` and `../../../notes/two_phase_escape_design_notes.md`.

## Premise & the two objectives

The player wakes on a runaway steampunk airship over an alien world **with an alien parasite/lesion
spreading on their arm** (infected during boarding). The ship's **medicine and its door-locks both run
on the same solvent rack**, so curing themselves and reaching the sealed bridge are one problem. Second
person, house register.

- **Objective 1 — ANALYSIS (graded → Canvas code).** Working the ship with a brass **field test-kit**,
  each teaching room reads **one property** of the cure; the **boss** combines all three to name the
  cure: the solvent that is immiscible with water, relative_polarity ≈ 0.6, and density < water. This
  is the labelled Data-Vis-II Q3. **Verified answer: 1-butanol.** Swab it → parasite dies AND the
  bridge bulkhead opens.
- **Objective 2 — ESCAPE (ungraded, "alien" echo).** To reach the captain's quarters and take the
  helm, the player re-derives the same solvent from **unlabelled/alien** charts (the transfer test).

## Room ladder (all stubs — art + puzzle content TBD)

| key | location | phase | role |
|-----|----------|-------|------|
| room1 | apothecary bay | analysis | test-kit reads property 1 |
| room2 | weather **deck** | analysis | test-kit reads property 2 |
| room3 | cargo **hold** | analysis | test-kit reads property 3 |
| boss  | bridge bulkhead | analysis | the full 3-condition cure (Q3) → Canvas code |
| nest  | **crow's nest** chart room | escape | the star-astrolabe: **plate-dial + mapview + star-log clue** (co-located) |
| captain | captain's quarters | escape | the **lock** (type 11D9) → take the helm |

Teaching rooms must exercise Data-Vis-II **plot-craft** (multi-variable aesthetic mappings, geom_tile,
regression), NOT chapter-3 filtering — and must **mirror hospital's question style** (the two are a
pre/post-test pair). Locations chosen per Lucas: get out on deck, go deep in the hold, up the crow's
nest; walking between rooms is deliberate (accustoms students to it for future interlocked mechanics).

## The star-astrolabe escape (dial → mapview → lock; RE-THEMED + BUILT, 2026-07-22)

> **REDESIGN DONE (2026-07-22).** The mechanic (dial → mapview → lock) is unchanged; its content moved
> off the solvents data to a true data-free meta-echo. The three mapview PNGs are now **three plates of
> the captain's star-astrolabe** — one field of **named stars** under three projections (`nest/
> make_starchart.py`, matplotlib, no network, deterministic). The **dial** (room1) is the astrolabe's
> plate-selector; the **star-log clue** (`nest` obj_starlog) names the one **"homeward house" (the
> Anchor)** without the answer; exactly one star — **SOLIRA** — holds the Anchor across all three plates,
> and its **name** is the helm lock (`captain` obj_lock, `answer:"SOLIRA"`, `length:6`). **All 17 star
> names are 6 letters** so the lock stays fixed-length. `nest/codes.json` is the source of truth
> (`answer_star`, `per_plate_in_house`); the crow's-nest scenePrompt + designNote are the night
> star-astrolabe. Guarded by `test_airship.py` (40 checks green). **`make_maps.py` is now orphaned**
> (superseded; flag for archival). Pre-escape copy: `_scratch/scenario.json.pre_story.bak`.
>
> **Original solvent-chart escape (retired 2026-07-22), for the record:**

- **Dial** (`room1` obj_dial, `type:"dial"`, key `mapping`) — three **alien sigils** ◈ ⬢ ✶ with opaque
  values m1/m2/m3 (so inspecting the JSON doesn't leak the meaning). Flipping it sets `gameState.mapping`.
- **Mapview** (`nest` obj_chart, `type:"mapview"`, key `mapping`) — shows `nest/map_<state>.png` for the
  current dial state. The three PNGs are **different aesthetic mappings** of the solvents data, axes
  unmarked, bottles shown only by coded label: ◈/m1 density×polarity, ⬢/m2 polarity×miscibility,
  ✶/m3 density×miscibility. The one code in-region across all three = 1-butanol.
- **Lock** (`captain` obj_lock, `type:"lock"`) — answer **11D9** (1-butanol's code).
- **Codes + PNGs:** `nest/make_maps.py` (matplotlib) fetches solvents.csv, assigns each solvent a stable
  `md5[:4]` code, writes `nest/codes.json` + the three PNGs, and prints the answer code. **Rerun it to
  regenerate; the lock answer must match the printed code.** Engine support (`dial`/`mapview` hotspot
  types) is in `shared/pano-player.js`.

## Drafted teaching questions (2026-07-18) — mirror hospital's multi-variable-mapping style

All puzzle hotspots are **the field test-kit** (a reskin of the "laptop" `puzzle` hotspot: WebR console
+ MCQ; solving opens the door). Each room maps multiple solvent properties to aesthetics and reads a
*relationship / group / region* — DV-II plot-craft, not chapter-3 filtering — and narrates one property
of the cure. Answers verified against `solvents.csv` (32 solvents). Drop these into each room's
`hotspots` (a `puzzle` with `question`) when the room is built + art placed.

**Room 1 — apothecary bay · property: WON'T MIX WITH WATER.**
Kit reagent: the parasite only recoils from solvents that don't dissolve into water — find what sets
those apart. Plot: `aes(x = relative_polarity, y = density, color = miscible_with_water)`.
Q: "Colour the solvents by whether they mix with water. How do the two groups sit along relative
polarity?" Options → **correct: "Water-mixing solvents tend to have HIGHER relative polarity"**
(verified: mixers mean 0.536 vs non-mixers 0.187); distractors: lower polarity / unrelated / all
denser than water / only chlorinated mix / higher density. Reveal: so your cure — which does NOT mix
with water — lives among the lower-polarity, water-shy solvents. *Teaches: categorical→colour, read
group separation.*

**Room 2 — weather deck · property: LIGHTER THAN WATER.**
Kit reagent: the cure must float on the wound-wash, not sink — but whole families of solvent are heavy.
Plot: `aes(x = density, y = category, color = category)` (+ a line at density = 1).
Q: "Most of the solvents denser than water belong to which chemical category?" Options: alcohol;
hydrocarbon; **chlorinated ✓**; oxygen_containing; nitrogen_containing; sulfide; amide (verified: of the
7 solvents with density > 1, four — CCl4, chloroform, DCM, chlorobenzene — are chlorinated). Reveal: so
the cure is NOT a chlorinated solvent; you want a lighter family. *Teaches: categorical→aesthetic, read
which group crosses a threshold.*

**Room 3 — cargo hold · THE TAUGHT TRAP: the pooled polarity rule breaks inside the alcohols.**
*(Reworked 2026-07-22, verified against solvents.csv — supersedes the earlier "combine three readings →
region" draft, preserved below. This adds the taught trap the `escape_room_puzzles` skill requires in
every scenario, makes the airship a true post-test echo of hospital's proxy-then-facet subversion, and
gives room 3 a distinct chapter plot-craft move — `facet_wrap` — fixing the room-1/room-2 plateau. The
correct option stays at **index 2**, so the decoder key `DATA_VIS2_AIRSHIP_KEY correct = c(1,3,2,4)` and
`test_*` lockstep are untouched. **PENDING: apply into `scenario.json` room3 `puzzle` hotspot before the
art step; leave the cargo-hold scenePrompt unchanged — the plot lives on the laptop, so no art regen.*)*

Technique: `facet_wrap(~ category)` small-multiples — read *within* a single family. Combines room 1
(polarity) + room 2 (density) and then **subverts** room 1's pooled rule.
Plot: `aes(x = relative_polarity, y = density, color = miscible_with_water)` + `facet_wrap(~ category)`,
read the alcohol panel.
Verified within the alcohols (n=6): mixers = methanol 0.762 / ethanol 0.654 / 1-propanol 0.617 /
2-propanol 0.546 (all mix); non-mixers = 1-butanol 0.586 / 1-octanol 0.537 (don't mix). **Polarity does
NOT separate them** — 2-propanol *mixes* yet is *less* polar (0.546) than 1-butanol (0.586), which
doesn't. **Density DOES, cleanly, no overlap** — every mixer ≤ 0.803, every non-mixer ≥ 0.810 (the
longer-chain, heavier alcohols stop mixing; gap 0.007).
Q (raw; method pushed to the wrong-hint): "Room 1's rule — water-mixers are the more polar solvents —
was read across the whole rack. Look inside one family, the alcohols, coloured by whether they mix with
water: what actually separates the alcohols that mix from those that don't?"
Options (6, data-derived; **correct = idx 2**):
0. "The same rule holds — the alcohols that mix are simply the more polar ones." *(the trap: naively
   extends room 1's pooled rule; FALSE — 2-propanol mixes yet is less polar than 1-butanol, which
   doesn't)*
1. "Nothing separates them — every alcohol mixes with water." *(FALSE — 1-butanol and 1-octanol don't)*
2. ✓ "Polarity barely separates them; it's the heavier, longer-chain alcohols that stop mixing, so
   density tells them apart — not polarity." *(CORRECT)*
3. "The alcohols that mix are the denser ones." *(FALSE — inverted; the two non-mixers are the densest)*
4. "Only chlorinated alcohols fail to mix." *(FALSE — category confusion; there are no chlorinated
   alcohols)*
5. "The alcohols that don't mix are simply the least polar ones." *(FALSE — 1-butanol (non-mix, 0.586)
   is more polar than 2-propanol (mix, 0.546), so no polarity cutoff can split them)*
Correct feedback (short, answer-naming, narrows to the boss): "Exactly — inside the alcohols polarity
overlaps, but density (chain length) decides. Only two polar alcohols refuse to mix with water:
1-butanol and 1-octanol — and your cure is one of them. The companionway to the bridge grinds open."
Wrong hint[0] (method, axis-agnostic): "Split the rack into small multiples by `category` and look only
at the alcohol panel; colour by `miscible_with_water` and check whether polarity actually separates the
two colours, or whether it's density."
Starter: `'solvents'` (bare data object — no solving pipeline).
*Teaches: `facet_wrap` small-multiples + within-group reasoning + that a pooled correlation can be
confounded (the chapter's faceting move; the airship's mirror of hospital's room-3 facet subversion).
Load-bearing: the cure, 1-butanol, is itself one of the polar-but-immiscible exceptions, so a student
who trusts "polar = mixes with water" would have discarded it.*

<details><summary>Superseded room-3 draft (region-combine — no taught trap; kept for the record)</summary>

Kit reagent: the cure is neither too water-loving nor too oily — a middling polarity — now combine all
three readings. Plot: the boss plot, `aes(x = relative_polarity, y = density, color = miscible_with_water)`.
Q: "The kit says the cure won't mix with water, is lighter than water, and sits at a middling polarity
(~0.6). Which region of a relative-polarity × density plot (coloured by miscibility) should you search?"
Options (regions) → **correct: "middling polarity (~0.6), low density, among the water-immiscible
points"**; distractors: the other five corners. Reveal: you've cornered it — one region, a handful of
bottles. *Teaches: combine three aesthetics, locate a region.*
</details>

**Boss — bridge bulkhead · the exact solvent (the real Q3, graded).**
Q: "Identify the solvent that is not miscible with water, has a relative polarity nearest 0.6, and is
less dense than water." Options: the ~21 solvent names from exercises.csv Q3. **Correct: 1-butanol.**
Swab it → the parasite dies AND the bulkhead opens → Canvas code.

Pre/post check vs hospital: hospital asks the same *shape* of questions (read a relationship / group /
region from a multi-aesthetic plot) on `alaska_lake_data`; keep them parallel so they work as pre/post.

## Narrative (STORY phase — `escape_room_story`, 2026-07-22)

Design conversation with Lucas, 2026-07-22. The premise was already strong (the world IS the technique:
the ship's medicine and its door-locks run off one solvent rack, so curing = escaping). This phase adds
a **clock, a temporal arc (day→night), a star-navigation world**, and **rebuilds the escape as a data-
free meta-echo**. Ship name settled as **the Alembic** (an alembic is a distillation still — ties the
name to the solvent chemistry the scenario grades; supersedes the "Astrolabe" drift in the old title/
story, and "astrolabe" is reclaimed as the escape *object*).

**Logline.** Wake on a runaway steampunk airship, *the Alembic*, adrift over an archipelago of floating
islands under a green evening sky, with an alien parasite spreading on your arm — cure yourself with the
ship's own solvents and climb to the helm to steer her off the peaks, reading your way home by the stars.

**Stakes + clock.** Concrete stake: the parasite is killing you *and* the ship is falling toward the
rocks; both are solved by reading the ship. The clock is **the descent into night** — the Alembic is
sinking as the light dies, and the only way to steer clear is to navigate by stars that only appear once
it's dark. The dark is both the danger (you can't see the peaks) and the tool (the stars you steer by).

**World from the analog.** The chapter's move is *reading multi-variable mappings* — mapping data to
aesthetics and reading a relationship/region off the picture. Two in-world places where a person does
that by hand: an **apothecary/still** reading a cure off charts of solvent properties (the graded spine),
and **celestial navigation** reading a bearing off the sky through an instrument (the escape). The Alembic
runs on both — a solvent rack for medicine and locks, an astrolabe for steering.

- **Landmarks (sited so the visit is earned).** The **floating-island archipelago** under a **green
  twilight sky**; the **star field** that comes out over it; the **crow's-nest chart room** at the mast-
  top where the **captain's star-astrolabe** lives. The **boss** is sited at the sealed **bridge
  bulkhead** (the cure opens it); the **escape** is sited up in the **crow's nest under full stars** — you
  climb there because the story needs you there.
- **Signature travel mechanic.** A **vertical ascent through the ship**, deck by deck, into the gathering
  night: apothecary bay → out onto the weather deck → down into the hold → up to the bridge → up the mast
  to the crow's nest → the helm. Walking between rooms is deliberate (per the original design) and the
  climb rises as the light falls.
- **Environmental arc (hand-off to design).** **Late-afternoon brass light → dusk on the weather deck
  (first stars) → dark lantern-lit hold → twilight at the bridge → full blazing night at the crow's nest
  → night at the helm.** Elevation rises as day turns to night; **unidirectional** (no toggle). The clock,
  the stakes, and the ascent all ride this one arc.
- **Cast economy — zero live characters.** No one appears (house "no people in art" rule). The **captain**
  exists only through what they left: the star-astrolabe and a **star-lore clue** naming the homeward
  house. The two-part goal (cure + steer home by the stars) is **front-loaded in the opening**, so the
  finale is a helm the player already knows to reach and a sky they already know to read.

**Beats (one per rung; graded spine = chemistry, escape = navigation).**
1. **Apothecary bay** — you wake, find the lesion and the brass field test-kit; the still and the solvent
   rack establish that medicine and locks are one problem. *Read property 1:* the cure won't mix with
   water → it's among the lower-polarity, water-shy solvents. (The astrolabe **plate-dial** was moved
   from here to the nest, co-located with the astrolabe, so the escape has no cross-ship back-nav.)
2. **Weather deck** — out into the dusk wind, first stars showing; the kit's next panel needs open air.
   *Read property 2:* the cure must float, not sink → the heavy families (chlorinated) are out.
3. **Cargo hold** — down into the swaying, lantern-lit dark. *The taught trap:* the kit says the cure is
   fairly polar yet won't mix with water — a contradiction. Facet into the **alcohols** and find that
   polarity can't separate the mixers from the non-mixers there; **density (chain length)** does. The cure
   is one of those polar-but-immiscible alcohols — trusting "polar = mixes" would have discarded it.
4. **Boss — bridge bulkhead** — twilight, the bridge dark behind sealed brass. *Name the one solvent*
   satisfying all three readings (immiscible, light, polarity nearest 0.6) = **1-butanol**. Swab it: the
   lesion dies and the same solvent opens the bulkhead. **Misdirection:** 1-octanol is the tempting near-
   miss (also a polar immiscible alcohol) — the careful "nearest 0.6" read wins.

**The escape (the payoff — designed here; DATA-FREE meta-echo).** Up the mast in full night, the
**captain's star-astrolabe**. It carries **three plates**, each projecting the *same* field of named
stars a different way (reusing the plot renderer, reskinned as a star chart — points→stars, axes→celestial
scales). The **dial** rotates the active plate (an astrolabe's plate genuinely rotates — the mechanic is
now diegetic). A **captain's star-lore clue** names **one** "homeward house" (a single target region —
kept to one, per Lucas, given by the clue so it's recognition not computation). Across the three plates,
**exactly one star holds that house in every projection** while the others drift in and out — that
invariant star is the safe bearing. Its **name** (all star names the same length → fixed-length lock) is
entered at the **helm lock** in the captain's quarters. **Ceremonial gesture:** setting the wheel to that
bearing is the player's own release — one control, one target, one motion — swinging the Alembic off the
rocks toward the one island the whole sky agreed on. It re-poses the boss's move (find the one member
invariantly in-region across multiple mappings) on **the world's own sky**, with no CSV, no solvent
values, no console — the decoupling the skill wants, and it resolves the crash rather than re-finding the
cure the boss already named.

**Voice notes.** Earnest, concrete, cinematic — never jokey. Sensory anchors from *this* world: brass and
canvas, green twilight, wind on the weather deck, lantern-sway in the hold, cold close stars at the mast-
top. Mood arcs warm→lonely→wondrous as day turns to night. People live only in the text (the captain's
log, the voice of the kit). Keep entry cards short — a beat, not a recap.

**Draft story-map text** (applied to `scenario.json` 2026-07-22; escape-finish written to the *star*
escape ahead of its build):
- **title:** The Alembic — **subtitle:** Data Visualization II · multiple mappings + solvent selection
- **story / entry cards / done / escapeDone:** see `scenario.json` (revised this pass). `done` = cure +
  bulkhead; `escapeDone` = star-astrolabe → set the helm → safe harbour.

## Open decisions / next steps

1. **Teaching-room questions (rooms 1–3 + boss)** — DONE and wired into `scenario.json` (prompts, 6–7
   data-derived options, correct indices `1,3,2,4` = decoder key, feedback, bare-data starters; all
   answers re-verified against `solvents.csv` 2026-07-22). Room 3 was **reworked to the alcohol facet
   taught-trap** (full spec above) and **applied into `scenario.json` 2026-07-22** (correct stays idx 2 →
   decoder unchanged). All four answers + the dial/mapview/lock escape lockstep are now guarded by
   **`test_airship.py`** (stdlib; 33 checks green) — re-run it after any scenario/data/`make_maps.py`
   change. Pre-rework copy saved at `_scratch/scenario.json.pre_room3_trap.bak`.
2. **Story / narrative — DONE** (`escape_room_story`, 2026-07-22). See `## Narrative`. Ship = **the
   Alembic**; day→night arc + star-navigation world added; story-map text (title/subtitle/story/6 entry
   cards/done/escapeDone) applied to `scenario.json`; escape redesigned to the star-astrolabe (below).
   Pre-story copy at `_scratch/scenario.json.pre_story.bak`.
3. **Escape rebuild (star-astrolabe) — DONE (2026-07-22).** Star field + `make_starchart.py` + 3 plate
   PNGs + `codes.json` built; lock = **SOLIRA** (len 6); star-log clue, dial + mapview + scenePrompt +
   designNote re-themed; `test_airship.py` updated (40 green). `make_maps.py` orphaned (flag for archival).
   Still-open sub-item: the crow's-nest **scenePrompt was rewritten** to the night star-astrolabe — good
   to send to art; the other five scenePrompts stand.
4. **Codec key — DONE.** `DATA_VIS2_AIRSHIP_KEY correct = c(1,3,2,4)` filled + in lockstep (guarded by
   `test_airship.py`).
5. **Art prompts — DONE + pre-art readiness pass (2026-07-22).** All six `scenePrompt`s rewritten so each
   depicts (a) its hotspots — every analysis room now shows a **brass field test-kit** (room2/room3 had
   none; "laptop" reskinned to the kit in room1/boss), the nest shows the **astrolabe + plate-dial +
   star-log + a companionway down**, the captain shows the **keypad door onto the helm/wheel** — and (b)
   the **day→night arc**: room1 late-afternoon → room2 dusk+first stars → room3 dark evening → boss
   twilight → nest deep night → captain starlit night. **Dial moved room1→nest** (co-located with the
   astrolabe; mapview reads the state on each open, so it's engine-safe). Pre-art copy:
   `_scratch/scenario.json.pre_artprompts.bak`. Ready for the harness: generate art → place boxes.
6. **Nav graph — pre-stubbed (2026-07-22), NEEDS BROWSER PLAYTEST once built.** Door hotspots stubbed with
   `to`/`direction`/`requires` (placeholder boxes to reposition on the art): analysis forward chain
   room1→room2→room3→boss→nest; escape = nest→captain via an **always-live `back` door** (the nest is a
   gateless reading room, so a *forward* door there would never open — see engine `doorIsOpen`), captain
   holds the lock + a **forward way-out door** (`requires:obj_lock`, no `to` → fires `escapeDone`), plus a
   back door up to the nest; `captain.unlockedWhen={solved:boss}`. Guarded structurally by `test_airship.py`
   (47 green). **Not yet play-verified in a browser** — nav can't run until rooms are `built:true` (the
   harness needs `isBuilt`); confirm the escape flow on a real playtest. Fallback if the two-room escape
   nav proves awkward: collapse the astrolabe + lock into one escape room.
7. **Hotspot content moved to `plannedHotspots` for art annotation — DONE (2026-07-27).** All six rooms'
   authored content was converted from `hotspots` (placeholder boxes) to each room's **`plannedHotspots`**
   manifest, with `hotspots: []` — the `squirrel` pre-art shape, so the harness click-to-place checklist
   shows every expected box to annotate on the generated art (content attaches at commit via
   `_attach_planned_content`). Also fixed a latent bug: the star-log clue used `text`, but the engine
   renders `clue.body` — now `body` (guarded). `test_airship.py` updated to read planned-or-placed
   (48 checks green); backup at `_scratch/scenario.json.pre_plannedhotspots.bak`.
9. **Map + environment redesign — OPEN-WORLD, ship-coherent (2026-07-27, with Lucas).** The linear corridor
   didn't make ship-sense. Reworked (Phase A, done):
   - **Re-themed rooms:** boss `bridge bulkhead` → **engine room / dispensary** (embodies the medicine=locks
     conceit; way cooler climax); `captain` → **`bridge`** (the helm belongs on the bridge, not a cabin).
   - **Open world:** every room `unlockedWhen:true`, every door `direction:"open"`. **Weather deck = hub**
     (reaches apothecary, crow's nest up the mast, bridge). Interior descends apothecary→hold→engine room.
     Crow's nest hangs off the deck, not the boss. Journey shape: descend to cure the body, rise for stars+helm.
   - **Order on the puzzles, not the doors:** `availableWhen` chain room1→room2→room3→**boss
     `{allSolved:...}`** (pins the boss to the engine room, per Lucas) + `lockedBody`; helm lock `{solved:boss}`.
   - **Environment:** dropped the day→night per-room clock (fights backtracking) → **constant** per-place
     light. Tension now rides two progressive state-driven overlays (no health bar; `hud:infection` removed):
     a **heel** listing right as puzzles solve, and a **sickness dim** deepening then clearing on the cure.
     **`heel`/`sickness` fields authored; engine support is Phase B (NOT built) — see below.**
   - **All six scenePrompts rewritten** (constant light + open passages depicted) → **regenerate all art**.
     `test_airship.py` rewritten for the open world (63 green). Backup: `_scratch/scenario.json.pre_openworld.bak`.
10. **Phase B — progressive environment engine — BUILT (2026-07-27).** `shared/pano-player.js`
    `updateEnvironment()` (called from `startRoom` + `solveRoom`): (a) progressive **heel** — CSS var
    `--heel-base` grows the heelRoll keyframe's base list angle 0→`maxDeg` (7°) to the right across the four
    analysis solves; (b) **sickness dim** — a `#sickness` radial vignette whose opacity ramps 0→`maxDim`
    (0.55) over the three *practice* rooms then clears when `analysisComplete()` (the boss = the cure). Pure
    helpers `heelBaseDeg`/`sicknessDim`; opt-in + backward-compatible (`heel:true` = constant roll, absent
    `sickness` = no-op); reduced-motion keeps the existing no-tilt rule. Cache bumped **js v=55→56, css
    v=52→53** across all 5 play.html + test_play.html. Verified: node syntax OK, unit 23/23, e2e smoke (2
    built scenarios boot, no page errors) + solve_advance/mixer_solve green; the full alaska playthrough runs
    the solve→finish flow clean (its only failure is a **pre-existing stale `#codeWrap` assertion**,
    unrelated). **Still needs a visual playtest once the airship rooms are `built:true`** — no built scenario
    carries the config yet, so the effect itself hasn't been seen on screen.
11. **Scene-consistency pass (2026-07-27, `escape_room_scene_validator`).** Two classes of break fixed +
    the skill strengthened to enforce them:
    - **World backdrop:** the bridge window said "dark peaks rushing past" — renders ground mountains in a
      floating-islands world. Fixed to floating crags in the art, and "peaks"→"crags" in `story`/`escapeDone`/
      bridge `entry` too. All exterior views now show floating islands at one constant night.
    - **Bidirectional transitions:** cargo-hold→engine-room was a level passage one way but a ladder *up*
      the other (walk in, climb out). Fixed to a ladderway down/up on both ends. room1↔room2 aligned to a
      shared deck-hatch+companion-ladder; room2↔bridge tied to the same gangway. All 5 passage pairs now
      agree (type + inverse direction). `escape_room_scene_validator` check 3 (bidirectional passages) +
      check 5 (world-backdrop continuity) added. Backup `_scratch/scenario.json.pre_transitionfix.bak`.
8. **Back-door navigation added to the analysis chain + scenePrompts fixed — DONE (2026-07-27).** The
   analysis rooms had only forward doors; mirroring the hospital twin, added an always-live `back` door to
   every non-first analysis room (room2→room1, room3→room2, boss→room3). Depicted the missing doors in four
   scenePrompts: **room2** (doorway back inside to the apothecary bay), **room3** (ladder up to the weather
   deck), **boss** (companionway down to the cargo hold), **captain** (ladder up to the crow's nest — the
   `door_up` hotspot already existed but wasn't drawn). Every hotspot in every room now has a depicted
   object in its prompt. Guarded by a back-door-chain check in `test_airship.py` (49 green). **These four
   prompts changed → regenerate their art.** Backup: `_scratch/scenario.json.pre_backdoors.bak`.
