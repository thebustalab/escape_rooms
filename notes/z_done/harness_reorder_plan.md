---
authority: intent
---

# Art-last harness reorder + story-map authoring page + story skill

**Status:** intent / phased implementation plan. Agreed with Lucas 2026-07-21 ("room harness"
session). Discuss-and-document done here; **build is phased and about to start** — biggest wins first,
confirm each phase holds before the next (per root AGENTS.md phased-delivery rule).

## The problem this solves

Art generation is currently the *middle* of the authoring flow, not the end. In the 8-step harness
(`authoring/ui/harness_gpt.html`) scene art is generated at Step 4, **before** the puzzle/clue content
is wired (Step 5), and cover art (Step 3) and clue artworks (Step 5) are two further art moments. So
Lucas commits to imagery, then finalises content, and any content shift forces a scene regen — exactly
the "Hawai'i RGB cipher — awaiting art regen + wiring" situation (AGENTS.md Known follow-ups). The three
skills mirror this old shape: `escape_room_wiring` is defined as "the phase **after** the harness makes
art," so the skill boundary itself bakes art into the middle.

**Goal:** author *everything text* first, review it as a whole, generate all art **once, late**, then a
thin mechanical "place + validate" closeout. Art-once is a goal you approach, not a guarantee (a
generated scene occasionally just won't have a good spot for a needed door/object → regen regardless),
but the ordering removes the *content-driven* regens, which are the avoidable ones.

## Target shape (four phases, mirroring re-cut skills)

1. **Puzzles** — analog, ladder, dataset. (`escape_room_puzzles`, unchanged.)
2. **Story + design** — the spec **plus all text authored and locked**: room story, entry cards,
   puzzle + clue content, sounds chosen, landing + finish text — all reviewed on **one story-map page**
   before any art. (New `escape_room_story` skill + slimmed `escape_room_design`.)
3. **Art** — one pass, Lucas on the `:8751` harness: covers, scenes, clue artworks.
4. **Place + validate** — drop the hotspot boxes (they **auto-attach** the pre-written content by
   label), make the open doors, re-validate values against the dataset, decoder lockstep, run tests.
   (Slimmed `escape_room_wiring` — now defined by *what it produces*, not *when it runs*.)

## The technical crux

Today, puzzle/clue content attaches to a **real placed hotspot**, which only exists after art. To
author content *before* art, content must live on the **`plannedHotspots`** manifest (which exists from
the design phase) and be **copied onto the real hotspot at placement time by label-slug match**. This
decouples content (art-free) from box placement (art-bound). `plannedHotspots` + `designNote` +
click-to-place already do half of this — they carry a hotspot manifest and seed type/label on
placement. We extend the manifest to carry the **full payload**, and make placement inherit it.

The only thing that *must* stay after art is placing the boxes and generating open doors — you can't
click a scene that doesn't exist yet. Everything else moves forward.

---

## Phase 1 — Decouple content from placement (the enabler) — ✅ DONE 2026-07-21

The technical foundation everything else rests on. No UI reorg yet. **Shipped:** `plannedHotspots`
entries now carry the full puzzle/clue/lock content payload; the all-rooms puzzle editor
(`puzzle_edit.html`) lists pre-art rooms (*"planned — pre-art"*) and writes content onto their planned
entries; and the server's **`_attach_planned_content`** copies that content onto the placed box at
commit, matched by `(type, slug(label))` — the same slug the click-to-place checklist uses. Backward-
compatible (a bare manifest changes nothing). Regression tests
(`test_attach_planned_content_by_slug`, `test_commit_attaches_planned_content`) pass; the full harness
suite is green (26). Editor JS parses. **Not yet piloted end-to-end on a live scenario through real
art** — do that on Hawai'i before leaning on it. Original spec below.

- Extend the `plannedHotspots` schema so each entry can carry its **full content payload** — for a
  `puzzle`: `starterCode`, `question`/`options`/`correct`/`feedback` (or console-check fields); for a
  `clue`: body, `pickup`, optional artwork prompt; for a `door`: `direction`/`to`/`requires`. Design
  metadata (`note`, `direction`, `pickup`) already lives there; this widens it to the graded content.
- Make the puzzle/clue editor (`puzzle_edit.html`) able to **read and write planned hotspots** for a
  room that has no art yet — keyed by label-slug, not by a placed-hotspot id.
- At **placement/commit** (hotspots editor "Save room" / commit out of `_scratch`), copy the planned
  payload onto the newly-drawn real hotspot by **label-slug match**, so a placed box arrives already
  wired. Keep `plannedHotspots` as the source of truth until commit; commit is the one-way copy.
- Server: a patch path to write content onto `plannedHotspots` (mirrors `/api/room-patch`); keep the
  SAVE_LOCK serialisation.

**Deliverable:** a puzzle can be fully authored and verified before its room has art; placing the box
later inherits the content with zero re-typing. Prove it on one Hawai'i room end-to-end before Phase 2.

## Phase 2 — The story-map authoring page — ✅ DONE 2026-07-21 (2a story + 2b content both shipped)

**2b shipped:** the puzzle/clue/lock card renderers were extracted from `puzzle_edit.html` into a shared
**`authoring/ui/puzzle_cards.js`** (`EscapePuzzleCards.make(ctx) → {roomCardsInto}`), which BOTH the
standalone editor and the harness now use — single source of truth, no divergence. The harness renders a
**"Room content" section (step 2b) inline under the map**: every room's full cards on one page, a built
room editing its `hotspots` and a pre-art room its `plannedHotspots` (marked *planned — pre-art*), each
with a per-room Save. Map hotspot chips and the step-5 button now **scroll to** that inline section
instead of opening a popup. Card CSS is scoped to `#contentCols`. All three files parse; server suite
green (26). The one behavioural note: `buildContent()` rebuilds on `refreshAll` (after a commit/delete),
so save a room's content before triggering those — matches the standalone editor's explicit-save model.
Original 2a spec follows.

### 2a (story surface)

**Shipped (2a):** the Step-2 room map is now the story-authoring surface. Each graph node carries inline
editors — editable room **title**, the first node's **opening story** + **enter button**, every other
node's **entry card**, and the graph's **exit node**'s **finish screens** — all binding to the in-memory
doc on input and persisting on blur (`wireMapNode` in `harness_gpt.html`). Gradeable hotspot chips now
show **✓ set / ○ blank** (`hotspotHasContent`) and click through to the Phase-1 all-rooms puzzle editor.
Additive + low-risk: the standalone step-6 entry / step-8 finish editors stay and are kept in step by
one-way sync (removed in Phase 4). Inline script parses; validated against the real Alaska / Hawai'i /
`trees` scenario shapes (`trees` is fully pre-art — the ideal live test).

**Deferred to Phase 2b:** embedding the *full* puzzle/clue content cards inline in each node (extract
`puzzle_edit.html`'s card renderers into a shared `ui/puzzle_cards.js` module so both pages reuse them,
no divergence). Chips currently jump to the all-rooms editor instead. Do 2b once 2a is confirmed on the
big monitor. Original spec below.

Grow the Step-2 room map (`buildMap()` in `harness_gpt.html`) from a read-only diagram into the single
global text-authoring surface. Lucas reviews/edits on a **big monitor, all editors visible at once** —
a deliberate global view, not click-to-expand.

- Each **room node** gains inline editors: **entry-card text**, **room/story beat**, and (boss/finish
  rooms) **finish text** — plus its **per-hotspot content** (reusing the Phase-1 planned-aware
  puzzle/clue editors), laid out in the node.
- **Landing screen** (title/subtitle/story/enter-label) and both **finish screens**
  (`done`/`escapeDone`) surfaced on the same page, at the graph's entry and exit.
- All edits write `SCENARIO_DOC` in place and save through existing patch endpoints; the header
  **Save all** already writes every text field at once — extend it to cover the new fields.
- Repaints on `refreshAll` as before; nodes still show the door graph, depth columns, and hotspot
  chips (green existing / amber planned) so structure and story are read together.

**Deliverable:** one page that straightens the whole story + all content before any art — the review
gate. Keep node width/layout sane so the graph is still legible with editors open.

## Phase 3 — The `escape_room_story` skill + re-cut boundaries — ✅ DONE 2026-07-21

**Shipped:** new **`.claude/skills/escape_room_story/SKILL.md`** — a craft-forward protocol (the world IS
the technique, the escape IS its payoff; a compelling-story checklist; an anti-patterns catalogue; a
beat-per-rung protocol; worked shapes from Alaska + `trees`). It reads `escape_room_puzzles`' `notes.md`
and outputs a `## Narrative` spec (or revises a weak scenario's story-map fields directly). The pipeline
is re-cut to **puzzles → story → design → [art] → wiring** across all four `SKILL.md` frontmatters +
prose, the `.claude/skills/AGENTS.md` roster, and `escape_rooms/AGENTS.md` (step-1 card, the "building a
scenario is FOUR skills" block, the tuning-skill note). `escape_room_design`'s narrative-intake step now
*consumes* the story spec; `escape_room_wiring` is reframed as the post-art closeout (content authored
pre-art on `plannedHotspots`), keeping its still-authoritative MCQ conventions. The new skill is
discovered (appears in the session skill list). Original spec below.



Fix "the stories have been weak." Today `escape_room_design` treats narrative as *intake*, with no craft
rules; the real-life analog from `escape_room_puzzles` ("seeds the world") is never turned into a story.

- New skill `.claude/skills/escape_room_story/` — craft rules for a compelling escape premise: stakes,
  a world that literally embodies the technique, per-room beats, and **the escape as the thematic payoff
  of the boss analog**. Input = the analog + verified ladder from `escape_room_puzzles`; output
  populates the Phase-2 story-map fields. Slots **between puzzles and design**.
- Re-cut the three existing skills to the new pipeline: `escape_room_design` keeps **scene prompts +
  door graph + scaffolding**; `escape_room_wiring` shrinks to **post-art place + validate + tests +
  decoder** (defined by output, not timing). Update all three `description:` frontmatters, the harness
  step cards, and `escape_rooms/AGENTS.md` to read **puzzles → story → design → [art] → validate**.

**Deliverable:** the story phase has real quality rules and a home; the skills mirror the new order.

## Phase 4 — Reorder the harness steps + close out — ✅ DONE 2026-07-21

**Shipped:** the harness now reads **content-first, art-last**. New order: 0 analog → 1 spec (Claude) →
2 room map & story → 2b room content → **3 sounds → 4 cover & landing → 5 build rooms = the ART step,
last**. The transitional duplicates Phase 2 left in place are **removed** — the standalone step-6 entry
cards, step-8 finish screens, and the step-5 "check with Claude" card are gone; the story-map
(`wireMapNode`) is the sole owner of `story`/`entry`/`done`/`escapeDone`, and `saveAll` sources them from
the in-memory doc (the sync helpers + `saveEntry`/`saveDone`/`saveEscapeDone`/`updateEntryBadge`/
`buildStep3`/`buildStep5` were deleted). Verified: inline script parses, div/section/main tags balanced,
**zero dangling references** to the removed elements (`#dnTitle`/`#entryCols`/`.eText`/…). AGENTS.md
walkthrough rewritten to the new order + a failure-mode note; scattered "Step 6/5/4" refs corrected.
No scenario-data migration: the story-map/content editors act on fields that already exist in every
scenario.json (Alaska/Hawai'i/`trees`), so no consistency-audit sweep was needed for the reorder (it's a
harness-UI change, not a per-scenario invariant). Browser playtest still pending — flagged to Lucas.
Original spec below.



Land the visible reorder now that the mechanism (P1) and surface (P2) exist.

- Renumber/reorder the harness sections so it reads top-to-bottom as **content-first, art-once,
  place-last**: story-map (all text) → art (build rooms) → place + validate. Fold the now-empty
  Step-5 "check with Claude" content-fill into the story-map page; the late step is purely place +
  open-door + validate.
- Update `escape_rooms/AGENTS.md` (the "Authoring = N-step harness walkthrough" summary), the
  `consistency/consistency.yaml` spec if any settled invariant emerged, and run the consistency-audit
  over the back-catalogue (Alaska, Hawai'i) so the two live scenarios get flagged for the new shape.
- Regression note + failure mode after any bug fix, per root AGENTS.md close-out rule.

**Deliverable:** the harness, skills, and docs all tell one story: author → art once → place.

## Notes / open questions

- Hawai'i is mid-flight ("RGB cipher — awaiting art regen + wiring") — it's the natural pilot for Phase 1
  and the Phase-2 page, since it needs re-authoring anyway.
- Cover art and clue artworks are independent of scene art; they fold into the single Phase-3-era art
  pass but don't gate anything.
- Don't over-promise art-once: keep the scene prompt explicitly demanding needed affordances (a clear
  doorway here, a table bearing X) so the generated image cooperates with the pre-planned hotspots.
