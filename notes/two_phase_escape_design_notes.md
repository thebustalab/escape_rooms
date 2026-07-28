---
authority: intent
---

# Two-objective structure — graded data analysis, then an instruction-free escape

**Status:** intent / design notes. Concept agreed with Lucas 2026-07-17 (explorations session).
**Discuss + document now; build later** — this reconfigures both live scenarios and extends the
`scenario.json`/engine model, so it's phased work, not a quick edit. Companion to
`puzzle_design_resources_notes.md` (the meta-puzzle / combination-lock / data-as-world mechanics this
draws on) and `doors_plan.md` (back-navigation, which this makes load-bearing).

## The core idea — two separate objectives, in order

A scenario now has **two objectives**, and the player hits them in sequence:

1. **Objective 1 — the data analysis (required, graded, first).** The **boss-room** puzzle ends this
   phase and hands over the **Canvas code** (the existing submission codec) — proof the student
   completed the analysis. This is the clean, gradeable endpoint of the academic work.
2. **Objective 2 — the actual escape (optional, ungraded, after).** With the Canvas code in hand, the
   experience **continues** into a new area beyond the boss, where a **Myst/Riven-style puzzle with no
   explicit instructions** is the real "escape." Its answer is **synthesised from all the earlier
   rooms' puzzles**.

**Why this is the right shape.** Separating the objectives lets the required work have a clean graded
completion *and* lets the escape puzzle be properly hard (no hand-holding, full synthesis) **without
ever threatening a grade** — the graded outcome is already banked. The instruction-free lock and the
"data as world" ideas belong here, in the *escape* objective, not on the graded path.

## The objective boundary and the two "codes"

- **The Canvas code** = the current submission codec + watermarked figure. Minted at the **boss solve**
  (end of Objective 1), shown on an "analysis complete — here's your Canvas code" interstitial. This is
  the graded deliverable; it is **unchanged** in what it encodes.
- **The escape code/action** = the synthesis puzzle's answer (Alaska's helicopter code; Hawai'i's valve
  choice). It is **not** part of the codec and **not** graded — it's the game win only.
- So the boss room's interstitial must **stop being terminal**: instead of the finish screen, it shows
  the Canvas code AND offers a door onward into the escape phase. A **second, distinct finish screen**
  ("you escaped!") fires when the synthesis puzzle is solved.

## Per-scenario reconfiguration

### Alaska — "Signal in the Cold"
- Add a room **beyond the boss** (the helipad prep room): step **outside** onto the floodlit pad where
  the second helicopter waits.
- The **helicopter-entry code** must be **synthesised from all four earlier room answers** (the pH
  lake, the nitrogen lake, the chloride lake, the warmest lake) — a combination lock with **no
  instructions**. Leans toward a cipher/synthesis (e.g. digits/letters/counts derived from the answers;
  exact scheme TBD + data-verified).
- Solving it = starting the helicopter = escape.

### Hawai'i — "Saltwater Intrusion"
- After the wellroom boss (Canvas code minted), a **door in the underground wellroom** opens — via a
  **code/sensor** (the synthesis gate) — onto a **bank of valves**.
- The escape is a **data-grounded** choice: **shut off the intruding well (KEEI_B / aquifer_6) while
  sparing the clean wells**, stopping the contamination spreading across the island. Possibly two-step:
  the synthesis code opens the valve door, then the correct valve choice completes the escape.
- Keeps the enrichment layer *grounded in the analysis* — the win is "which well was intruding,"
  synthesised from everything measured.

## Engine / `scenario.json` implications (additive to the current schema)

- **Phase boundary.** Mark rooms as analysis-phase vs escape-phase — e.g. a room-level
  `phase: "analysis" | "escape"` (default `analysis`), or an `isEscape` flag on rooms after the boss.
  The boss is no longer the terminal node.
- **Codec fires at the boss, not the very end.** `submitCodec`/`deliverable` stays on the boss and mints
  the **Canvas code** there; the finish flow splits (see below). Escape-phase rooms carry **no codec
  effect** and are excluded from the code (like today's stub rooms are excluded).
- **Two terminal screens.** The scenario needs both the current `done` (recast as "analysis complete +
  Canvas code + continue?") and a new **escape-finish** screen (e.g. `escapeDone:{title,body}`) fired by
  the synthesis solve.
- **New puzzle type — the synthesis / combination lock.** A hotspot that opens a **modal with free
  inputs** (dials / fields), **no MCQ options and no printed prompt**, graded by matching a target code
  (or a `check:` expression). **Not recorded in the codec.** Slots into the existing hotspot→modal
  pattern (it's a puzzle variant whose "answer" is a combination). Needs a sensible attempt limit so it
  isn't brute-forced.
- **Prior-answer access.** If the synthesis code is *computed* from earlier answers, the lock's check
  needs read access to `roomResults`/`gameState`; if the code is *fixed*, it must be **derivable from
  re-reading the world/data** (preferred, more Myst-like).
- **New rooms + art.** Alaska exterior/helipad-outside room; Hawai'i valve room. New `scenePrompt`/
  `doorPrompt`, regenerated via the `:8751` harness; new hotspot boxes.

## Fairness — keep the instruction-free puzzle Riven-good, not frustrating
The whole risk of an instruction-free synthesis lock is the knife-edge between brilliant and annoying.
Riven stays fair because the world always contains everything needed to re-derive the answer. Treat two
things as near-mandatory:
- **Back-navigation** (`doors_plan.md`) so any earlier room can be revisited to re-derive its answer.
- Probably an **accruing "field notebook"** that logs each room's finding as it's solved — so "synthesise
  the previous answers" is genuine inference, not a memory test.
Playtest this specifically.

## Open decisions (resolve during build)
- **Synthesis-code scheme** per scenario — exactly how the four answers combine into the helicopter code
  / the valve choice. Design it, then **verify against the dataset**.
- **Recall mechanism** — back-nav only, an accruing field notebook, or both.
- **Onward door gating** — does the boss→escape door open freely once analysis is done, or require the
  Canvas code / a first synthesis step?
- **Hawai'i valve step** — one action (synthesis code opens door = win) or two (code opens door, then a
  data-driven valve choice completes it)?
- **Lock ↔ prior answers** — expose `roomResults` to the lock's check, or keep the code fixed-and-
  derivable-from-the-world?
- **Phasing** — pilot the phase-boundary + finish-split + lock mechanic on **one** scenario (engine
  first) before reconfiguring both and regenerating art.

## Build log

### Slice 1 — the two-phase spine — BUILT 2026-07-17 (pilot: Alaska)
Engine support for the objective boundary, minted with **placeholder** escape content so the flow is
click-through-testable before any new art or the real lock.

- **`shared/pano-player.js`:** rooms carry `phase:"analysis"|"escape"` (default analysis, via
  `phaseOf`). **`finishAnalysis()`** mints the graded Canvas code over **analysis rooms only**
  (`mintCode("analysis")`). **Trigger updated 2026-07-18:** it fires the moment **all analysis puzzles
  are solved** (`analysisComplete()`, checked in `solveRoom`) — completion, not room order — and the
  code window now just shows a **Close** button (`#continueOut`) that dismisses back to the room. It no
  longer navigates ("Step outside" auto-hand-off removed): the player walks to the escape phase through
  a door themselves, keeping the code window independent of room structure. `goThrough()` still advances
  within-phase and calls **`showEscapeDone()`** (terminal, no code) when the escape phase runs out. The
  old single `showDone()` is gone.
- **Codec contract preserved.** Escape rooms are excluded from the code in the browser (`mintCode`
  filters `phase`) **and** in `decoder/validate_keys.py` (skips `phase:"escape"`). Alaska's decoder key
  stays `c(3,2,4,1)` (4 analysis rooms); `decode_codes.R` untouched. Verified: `validate_keys.py` PASS
  (both scenarios), `Rscript decode_codes.R` self-test green.
- **Alaska `scenario.json`:** added room **`escape1`** (`phase:"escape"`, `unlockedWhen:{solved:"boss"}`)
  reusing `boss/scene_open.png` as placeholder art, a throwaway MCQ puzzle + a "board the helicopter"
  door, an `entry` interstitial, and a scenario-level **`escapeDone`** screen. All of `escape1` is
  clearly marked `[PLACEHOLDER]`.
- **Cache:** `play.html` bumped `?v=13 → v=14` (Alaska + Hawai'i).
- **To test (Lucas):** open Alaska `play.html`, play through the four analysis rooms → solving the last
  analysis puzzle shows the **Canvas code + a Close button** (fires on completion, whatever room you're
  in) → Close → walk through the door into the placeholder helipad room → solve the throwaway puzzle →
  board the helicopter → the separate **"Airborne (placeholder)"** finish. Confirm the Canvas code
  appears on analysis completion and the escape finish carries **no** code.

### Slice 2 — the real combination lock — BUILT 2026-07-17 (pilot: Alaska)
The no-instructions keypad mechanic + the Alaska synthesis code. Scene art still the boss stand-in.

- **`shared/pano-player.js`:** new hotspot **`type:"lock"`** — `onHotspot` routes it to `openLock`,
  which opens a keypad modal via `buildLockCard` with **NO prompt text** (a monospace input + "Enter"),
  matching a fixed `answer` compared through `normalizeCode` (uppercase, strip non-alphanumerics, so
  case/spacing don't matter). Unlimited tries by default (`maxAttempts:0`), optional `feedback:{correct,
  wrong,out}`. On success it calls the same `solveRoom` path (opens the door / swaps panorama). Schema:
  `{ type:"lock", box, label?, answer, length?, maxAttempts?, feedback? }`. Excluded from the codec by
  virtue of being in an escape-phase room.
- **The Alaska synthesis code = `NWNL`** — the first initial of each room's answer lake, in room order:
  **N**orth_Killeak (room1, pH > 8) · **W**alker (room2, top nitrogen) · **N**orth_Killeak (room3, top
  chloride) · **L**ava (boss, warmest). **Verified against the real dataset** (`alaska_lake_data.csv`,
  fetched + recomputed 2026-07-17): pH>8 → North_Killeak only; top N → Walker_Lake (0.19); top Cl →
  North_Killeak (337.23); warmest → Lava_Lake (20.18°C).
- **`escape1` scenario.json:** placeholder MCQ replaced by the `esc_lock` hotspot (answer `NWNL`,
  length 4); entry + `escapeDone` text de-placeholdered (with a small pilot note that the scene art is
  still the boss stand-in). Kept the `esc_door`.
- **Cache:** `play.html` bumped `v=14 → v=15`. **Verified:** `validate_keys.py` PASS (escape room
  correctly skipped, Alaska key still `c(3,2,4,1)`), `decode_codes.R` self-test all round-trips TRUE.
- **No-instructions on purpose.** The keypad shows only four slots and the label "The helicopter
  keypad" — no hint that the code is the four lakes' initials. The solve feedback ("Four rooms, four
  lakes") gives the post-hoc *aha*. This is the knife-edge to playtest: if it reads as an unfair wall,
  the fairness levers (an oblique diegetic clue, and/or the accruing field notebook) are the next move
  — deliberately held back so the click-through tells us whether they're needed.
- **To test (Lucas):** finish the analysis + boss → Canvas code → **Step outside** → on the pad, click
  the keypad marker → a bare 4-slot keypad opens with no instructions → type **NWNL** → the hatch
  releases → board → **Airborne** finish (no code). Also try a wrong code ("Nothing happens") and
  confirm case/spacing don't matter (e.g. "nwnl" or "n w n l" still work).

### Harness support for locks — BUILT 2026-07-18
Locks are now first-class in the authoring harness (so they drop into *any* room, not just hand-JSON):
- **`hotspots_edit.html`:** `"lock"` added to `TYPES` — it's a selectable box type, and (critically)
  the "coerce unknown type → puzzle" normaliser no longer clobbers a lock on load/save. Content panel
  points to the puzzle tab.
- **`puzzle_edit.html`:** a **lock card** (answer / length / max-tries / feedback correct·wrong·out) now
  renders for `type:"lock"` hotspots, alongside puzzles and clues.
- **Server:** no change — `/api/room-patch` writes the hotspots array verbatim, so lock fields ride
  along.
- **`escape1` art:** added an `authoring:{tag,scenePrompt,doorPrompt}` block (floodlit night helipad,
  house style, closed hatch + keypad) so the harness Step-2 can generate the real exterior; the boss
  stand-in stays until Lucas commits the generated scene.

### Option B — per-gate solve state — BUILT 2026-07-18
Lucas chose **(B)**: one room can now carry two independent gates (e.g. a graded puzzle AND a separate
escape lock). Engine + harness both done.
- **`shared/pano-player.js`:** new `solvedGates` set (hotspot ids of solved puzzle/lock gates, cleared
  on Enter). Helpers `primaryGate(r)` (first puzzle, else first lock), `isPrimarySolved(r)`, and
  `doorIsOpen(h,r)` (back ⇒ open; `door.requires` gate id(s) all solved ⇒ open; else the room's primary
  gate). `solveRoom(result, h)` now takes the solving hotspot: it marks the gate; **only the PRIMARY
  gate** records the codec (graded puzzles only — locks never) + adds to `solvedRooms` + runs `onSolve`.
  Door gating, puzzle/lock re-entry, and hotspot "done/open" styling all read per-gate now, not the old
  room-level `solved` (which survives only for entry-image selection). Fully backward-compatible: a
  single-puzzle room has that puzzle as its primary gate and behaves exactly as before.
- **Schema:** a `door` gains optional **`requires`** — a gate hotspot id, or an array of ids; the door
  opens when all are solved. Absent ⇒ the room's primary gate (legacy).
- **Harness:** hotspots editor gained a door **"requires gate"** dropdown (lists the room's puzzle/lock
  hotspots); combined with the `lock` type + the puzzle-editor lock card, a boss-room-with-escape-lock
  is fully authorable in-UI.
- **Cache:** `play.html` bumped `v=15 → v=16`. **Verified:** JSON parses, `validate_keys.py` PASS
  (codec unaffected — locks/escape rooms still excluded). No JS runtime on this box, so the engine
  logic is **manual-playtest only** — the Alaska click-through is the check (escape1's lock is now its
  *primary* gate, so it still opens its door + finishes exactly as before).
- **To build a boss-with-lock later:** in the boss room add a `lock` hotspot + a second `door` whose
  **requires** = that lock's id (and, to force order, add the boss puzzle's id too). Solving the data
  puzzle → Canvas code + advance; the lock stays a separate, ungraded escape gate.

### OPEN DESIGN DECISION (RESOLVED 2026-07-18 → built option B) — a lock as a *second gate in the same room* (e.g. a boss room)
Lucas wants locks modular enough to sit **in a boss room**: solve the data puzzle (graded → Canvas
code) but still not "escape" until you crack the lock. The player currently tracks **one `solved` flag
per room**, and *any* puzzle- or lock-solve flips it + records the codec result — so two independent
gates in one room would collide (the lock's solve would overwrite the graded puzzle's codec answer, and
either solve would open both doors). Two ways forward:
- **(A) Separate rooms (works today).** Boss = analysis room (graded puzzle); a following escape room
  holds the lock. Functionally already delivers "solved the boss but didn't escape" — this is the
  current Alaska model.
- **(B) Per-gate solve state (engine change).** Track solved-ness per hotspot, and let a door/exit gate
  on a *specific* gate (e.g. `door.requires:"esc_lock"`), with locks never touching the codec. This is
  what enables a true two-objective **single** room. Small but core change to `solveRoom`/`handleDoor`.
Decision pending Lucas: is (A) enough, or do we build (B)?

### Bug fixed 2026-07-18 — cross-room false solves (duplicate hotspot ids)
**Symptom (Lucas):** on Alaska, replaying showed room3's puzzle already solved and the helicopter
escape door already open. **Cause:** hotspot ids are only unique *within* a room — the harness reuses
`obj_1`/`obj_2`/`obj_3`… across every room. The per-gate model (2026-07-18) keyed `solvedGates` by the
**bare hotspot id**, so solving room1's `obj_3` marked room3's `obj_3` solved, and solving room2's
`obj_2` satisfied the escape door's `requires:"obj_2"` (the escape lock is also `obj_2`). **Fix:** key
the solved-set and the attempt counter by **`gateKey(roomKey, hotspotId)`** (`"room|obj_3"`);
`door.requires` resolves its ids against the door's own room. In-code comment at `gateKey` in
`pano-player.js`. **Failure mode to remember:** any per-hotspot state (solved, attempts, and anything
future) MUST be room-namespaced — ids are not globally unique. No JS test runner on this box, so this is
the regression record; the Alaska replay is the manual check. (No cache bump needed — `play.html` was
already at `v=19`.)

### Next (not started)
- **Alaska: the `NWNL` initials lock is being REPLACED** (decided 2026-07-20) by the "Claire's filtered
  glass" *Secret of the Unicorn* overlay escape — three coloured 4×4 mask notes intersect to one cell,
  whose boss-room code = the keypad code. Still an escape-phase `lock` (out of the codec), so the engine
  work here stands; only the Alaska `escape1` answer + the puzzle-room clues change. Spec:
  `../rooms/data_vis/alaska/notes.md`. The fairness/field-notebook judgement below is largely mooted for
  Alaska by the overlay (the masks self-document in the notebook), but keep it for Hawai'i / future locks.
- Judge on click-through whether the instruction-free lock is fair as-is or needs an oblique clue /
  field notebook.
- Generate the real "step outside to the helicopter" **exterior scene** (harness) and swap out the
  boss stand-in art + place the real keypad/door boxes.
- Port the two-objective structure to **Hawai'i**: the wellroom door → the valve room, where the
  escape is the data-grounded "shut the intruding well (KEEI_B / aquifer_6), spare the clean ones."
