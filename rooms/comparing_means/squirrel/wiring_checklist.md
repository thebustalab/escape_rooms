---
authority: intent
---

# Wiring checklist — `comparing_means/squirrel` ("Seedfall")

Per-room hotspot + field checklist for the **wiring stage** (after Lucas generates the 13 scene images on
the `:8751` harness). Applies the **canyon open-maze authoring recipe** to squirrel's circle. The MCQ/clue
**content is already authored** on each room's `plannedHotspots` in `scenario.json` (prompts, 7 options,
correct index, feedback, clue bodies, the grid spec) — at commit the harness attaches it by
`(type, slug(label))`, so wiring is mostly: **generate art → draw each box → set the open-maze fields
below**. Durable facts in `AGENTS.md`; full design record in `notes.md`. Run the `escape_room_wiring` skill
for the canonical process; this is the scenario-specific manifest.

## 0. Global (do once)

- [ ] **Every door is an open passage:** set `direction:"open"` + its `to` on **all 26 door hotspots** (the
      ring is fully walkable; there are **no** forward/back-gated or closed doors, no `panoramaOpen` swap).
- [ ] `state` = `{rooms_solved:0}` (no `heights_read` — the escape is ungated on leaps). `ambient:"leaves"`.
- [ ] Confirm **WebR** runs the course stats wrappers (`shapiroTest`/`leveneTest`/`tTest`/`wilcoxTest`/
      `anovaTest`/`tukeyHSD` or the `rstatix` equivalents); `setup` loads `rstatix`. If a wrapper has no wasm
      build, fall back to base-R/`rstatix` calls in the `starterCode`.

## 1. Per-room hotspots (13 rooms, ring order)

Legend: **P** puzzle · **C** clue · **G** grid · **D** door. Every door → `direction:"open"`.

| Room | Scene (unique art) | Hotspots to place + fields to set |
|------|--------------------|-----------------------------------|
| **mother_oak** (hub/START) | Mother Oak crown | C "The cache-frame panel" (foreshadow body) · D→`roost` · D→`red_a` |
| **red_a** (RUNG 1, t-test) | red maple + lantern | P "The surveyor's lantern" — `starterCode:"nut_census"`, question **correct 1**, **availableWhen: none/TRUE** (first). Room `onSolve:[{set:"red_a_solved"},{inc:"rooms_solved"}]` · C "This stand's height" · D→`mother_oak` · D→`red_b` |
| **red_b** (empty) | quiet red maple | C "A second red maple…" · D→`red_a` · D→`t_rg` |
| **t_rg** (LEVEL) | red↔green level glide | C "The height between the stands" (level body) · D→`red_b` · D→`green_a` |
| **green_a** (RUNG 2, Wilcox) | green oak + lantern | P question **correct 2**, **availableWhen:`{solved:"red_a"}`**. `onSolve:[{set:"green_a_solved"},{inc:"rooms_solved"}]` · C height · D→`t_rg` · D→`green_b` |
| **green_b** (empty) | quiet green oak | C · D→`green_a` · D→`t_gg` |
| **t_gg** (UP-one) | green→gold climb | C (up-one body) · D→`green_b` · D→`gold_a` |
| **gold_a** (RUNG 3, ANOVA+Tukey) | golden aspen + lantern | P question **correct 0**, **availableWhen:`{solved:"green_a"}`**. `onSolve:[{set:"gold_a_solved"},{inc:"rooms_solved"}]` · C height · D→`t_gg` · D→`gold_b` |
| **gold_b** (empty) | quiet gold aspen | C · D→`gold_a` · D→`t_gs` |
| **t_gs** (DOWN-two) | gold→silver big drop | C (down-two body) · D→`gold_b` · D→`silver_a` |
| **silver_a** (BOSS) | silver birch + lantern | P question **correct 3**, **`puzzleType:2`, `isBoss:true`, `deliverable:{type:"figure",submitCodec:true}`**, **availableWhen:`{allSolved:["red_a","green_a","gold_a"]}`**. `onSolve:[{set:"silver_a_solved"},{inc:"rooms_solved"}]` · C height · D→`t_gs` · D→`silver_b` |
| **silver_b** (empty) | quiet silver birch | C · D→`silver_a` · D→`roost` |
| **roost** (ESCAPE, `phase:"escape"`) | oak heartwood + cache-frame | **G "The cache-frame"** — `items` (4 kinds) × `buckets` (Tallest/Middle/Lowest), `answer:{gold:"high",red:"mid",green:"mid",silver:"low"}`, **availableWhen:`{allSolved:["red_a","green_a","gold_a","silver_a"]}`** + `lockedBody`, feedback · C "The cache-rite" · D→`silver_b` · D→`mother_oak` |

**Sanity:** 4 puzzle boxes (red_a/green_a/gold_a/silver_a) · 1 grid (roost) · 1 foreshadow clue (mother_oak)
· 1 cache-rite clue (roost) · height/flavour clue in every tree + transition · 26 door boxes (13 rooms × 2),
all `direction:"open"`.

## 2. Decoder (`decoder/decode_codes.R`) — codec lockstep

- [ ] Add **`JAY_KEY`** (`scenario_id = 13`) with the 4 graded rooms' correct indices, **in this room order**
      as the codec expects: `red_a → 1`, `green_a → 2`, `gold_a → 0`, `silver_a (boss) → 3`. (The `roost`
      escape is **out** of the codec.)
- [ ] Run `decoder/validate_keys.py` → green. (Note: `id 13` is not yet in the decoder — same state spa/id 12
      is in; add both when convenient.)

## 3. Tests

- [ ] Add `_scratch/test_squirrel.py` (or extend the suite) pinning **each graded answer to the shipped
      `data/nut_census.csv`** by re-running the analysis — the R1/R2/R3/boss values + names, and the boss
      Tukey CLD + the R2 t-vs-Wilcox flip. (The generator `build_nut_census.py` already asserts these; the
      test guards the *shipped CSV* against drift.)
- [ ] **Browser-playtest the grid-select** in `play.html` (engine BUILT 2026-07-26, logic-tested only):
      confirm the cache-frame renders, one-bucket-per-kind selection works, the `lockedBody` shows before the
      survey is done, and a correct grouping fires `escapeDone`.
- [ ] Playtest the **open-maze ordering**: from the start you can roam the whole ring, each locked lantern
      shows its `lockedBody` (not the console) until its predecessor is solved, and `analysisComplete` mints
      the codec when all 4 lanterns are solved.

## 4. Art (Lucas, `:8751`)

- [ ] Generate **13 unique scene images** (mother_oak, roost, red_a, red_b, green_a, green_b, gold_a, gold_b,
      silver_a, silver_b, t_rg, t_gg, t_gs) + the **cover** (`coverPrompt` set). Prompts are place-constant
      (no time/season sequence); the four survey-trees show a lantern, the empty trees don't.
- [ ] Recognition fairness: the transition scenes (`t_rg`/`t_gg`/`t_gs`) and the tree scenes must make the
      **heights unmistakable** (gold clearly tallest, red≈green level, silver clearly lowest) — the escape is
      judged by eye.

## 5. Ambience (wiring)

- [ ] **Per-room sfx** (harness "Sounds" step) — leaf-rustle / wingbeat / lantern-hum / a settling *chunk*
      for the cache seal. Source via the `sound_pull` observer utility.
- [ ] **Music:** none chosen yet (TBD) — optional woodland loop via `youtube_audio` if wanted.

## Open judgement calls (from `notes.md`, confirm at wiring)

- **Grid is 4 kinds × 3 tiers** (Tallest/Middle/Lowest), not 4×4 — the data has 3 height levels (red & green
  share the middle, which is the CLD lesson). Add a 4th empty tier only if the "4×4" look is wanted.
- **Escape ungated on leaps** (Lucas) — gated only on the survey (`allSolved` the 4 lanterns).
- **Boss at the silver birch** (ring-order flow; it analyses all kinds).
- **No git commit on this box** (Mac-only repo; Syncthing carries edits).
