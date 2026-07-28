---
authority: intent
---

# Open-world traversal + backtrack-safe environmental arc (cross-scenario design)

**Proposal / plan (2026-07-25, Lucas, session "squirrel").** Solves two **recurring limitations** across
every scenario so far — (A) linear corridor gating (closed doors force a single order but kill free
exploration) and (B) a temporal/season arc that fights backtracking (revisiting an earlier room ships the
player *backwards* in the day/season). Both are solvable on the current engine with **small, general
additions** — captured here as the standard model so future scenarios inherit it. Sibling of
`doors_plan.md` (which shipped forward/back nav). `squirrel` is the first intended consumer.

Kept **`authority: intent`** until agreed + the engine bits land; then graduate the settled parts into
`../AGENTS.md` and the design skill.

**GRADUATED 2026-07-26.** The settled model is now **canon** in `../AGENTS.md` → "Open-world layout +
backtrack-safe environmental arc" (+ the engine in the *Current architecture* open-maze bullet), and in the
`escape_room_design` skill (Rooms & doors checklist + the Scene-progressions backtrack-safety note). This
file remains the **full record + engine grounding + the squirrel worked example**; the canon is the concise
rule.

## Engine grounding (what EXISTS vs what's TO BUILD)

Verified in `shared/pano-player.js` / `authoring/` (2026-07-25):

**Exists / reusable:**
- `gameState` bag + `condOK(cond)` evaluator supporting `true` / `{solved:key}` / `{allSolved:[keys]}`;
  drives room `unlockedWhen` today. `set`/`inc` onSolve effects.
- Back-nav: a **`back` door is always-open, ungated, no entry, no codec**; **solved rooms re-enter** in
  solved state (open pano, puzzle short-circuits) without re-recording the codec.
- The **dial → mapview** pattern: a hotspot that **reads `gameState` and re-renders** (proto of #8
  `showWhen`). So "hotspot content conditioned on state" is already a shipped shape.
- **Ambient particles are a GLOBAL overlay** the engine draws over the pano (`scenario.ambient` ∈
  `fireflies|snow|embers|leaves|none`, spawned per screen), with a **per-room `r.ambient` override** —
  NOT baked into the scene art.

**To build (small, general — Lucas's `pano-player.js` work):**
1. **`availableWhen` + `lockedBody` on a `puzzle` hotspot** (Problem A). Reuses `condOK`. When
   `condOK(availableWhen)` is false, clicking the puzzle shows `lockedBody` (a diegetic "not yet" message,
   like a `clue`) instead of launching the WebR console; when true, it's the live puzzle.
   → **BUILT + browser-tested 2026-07-26** (for the `canyon` maze; Playwright headless Chromium, a synthetic
   maze scenario, 8/8 — open-door nav, availableWhen+lockedBody, onPickup→counter, {gte} gate; alaska+henges
   boot clean, no regression). In
   `pano-player.js`: `availableWhen`+`lockedBody` on **puzzle *and* lock** hotspots (`openLocked`), plus
   two siblings the open maze needs — door **`direction:"open"`** (always-walkable passage, entry on first
   visit) and clue **`onPickup`** effects; `condOK` gained the **`{gte:[stateKey,n]}`** counter gate (e.g.
   the escape panel's `availableWhen:{gte:["heights_read",7]}`). All optional + backward-compatible
   (absent ⇒ old behaviour). Puzzle-less junction rooms now track `visitedRooms` so their entry card
   doesn't re-show. Verify in `play.html` before relying on it.
2. **State-driven global ambient/tint** (Problem B). Drive the global ambient layer (and optionally a
   light colour-tint overlay) from `gameState` (e.g. `rooms_solved`) rather than a fixed string — so the
   *season/clock* lives in the overlay, advances with progress, and shows the SAME (current) value in
   every room including revisited ones.
Neither is a redesign; both extend machinery that already ships. No JS runtime on this box — these are
flagged for the harness, not built/tested here.

## Problem A — free exploration, puzzles still solved in order

**Model: decouple TRAVERSAL from PROGRESSION.** The whole world is physically explorable from the start;
the *ordering* is enforced on the **puzzle hotspot**, not the doors (exactly Lucas's instinct).

- **Doors all open.** Every connection is an always-open passage (the existing `back`-door behaviour in
  both directions), so the player can roam the entire map. Rooms are `unlockedWhen: true`. *(Entry cards:
  keep as one-time first-visit triggers — minor engine tweak, or accept they fire on first arrival
  regardless of order.)*
- **Puzzles gated by `availableWhen`.** Each later puzzle carries `availableWhen: {solved: <prev>}` (or
  `{allSolved:[…]}` for the boss). Until met, clicking it shows a **diegetic `lockedBody`** — never a
  video-game "LOCKED", always in-world (see squirrel below). This chains the order without a single wall.
- **Why it's better than corridor-gating:** free Myst-style exploration; the player can revisit anything;
  and for scenarios whose *escape* rewards roaming (squirrel's heights!), open-world traversal actively
  serves the pedagogy instead of fighting it.

## Problem B — a clock that survives backtracking

**Root cause:** a **temporal/season** arc is *irreversible* but is baked *per-room*, so revisiting either
contradicts the arc or yanks the player backwards in time. A **spatial/place** property is
*position-based* and is backtrack-consistent by construction (a place looks like itself).

**Model: split the environment into two layers.**
1. **Baked art = the PLACE's constant character (spatial, position-based).** Each location has its own
   *inherent, fixed* mood baked into its scene — dappled hollow, gloomy fen, bright clearing, exposed
   crown. **No time-of-day sequence in the art.** Revisiting is always consistent: a place looks like
   itself, forever. (Elevation/vantage may still differ per place — that's spatial, so it's fine.)
2. **The CLOCK = a single GLOBAL overlay driven by state.** The one irreversible element (winter closing
   / dusk falling) lives in the **global ambient/tint layer**, advancing with `rooms_solved` and rendered
   identically over **every** scene. Revisit the hollow after solving three rooms → you see the hollow's
   constant place-mood **+ the current (heavier) snow**, never "backward." The clock advances *everywhere
   at once*, which is also more truthful ("winter is coming to the whole wood").

**Two tiers of adoption:**
- **Tier 1 (zero engine work — do now):** place-constant art + carry the clock in the **narrative text**
  (entry cards, prompts) + a **single fixed global ambient** (e.g. `leaves` throughout, or `snow`). Fully
  backtrack-safe immediately; the season just doesn't visibly *advance* in the art (only in text).
- **Tier 2 (small engine work — the payoff):** the **state-driven global ambient/tint ramp** (build item
  #2) so the clock visibly advances (leaves → light snow → heavy snow) across all scenes, consistently.

**Reject:** multiple baked lighting variants per room (N× art cost). The overlay approach gets the same
feel for a fraction of the assets.

## Composed — the two fixes reinforce each other

Open-world traversal (A) + place-constant art with a global clock overlay (B) = the player can **freely
roam the whole world, revisit any location, and the world stays consistent** while a global clock still
advances with progress. For scenarios whose escape rewards exploration this is strictly better than the
linear corridor.

## Application to `squirrel` (Seedfall)

- **A:** the jay flies the **whole wood from the start** (all branch-passages open) — which directly
  serves the escape (roam to learn tree **heights** by eye). Each stand's **surveyor's lantern** is
  `availableWhen` its predecessor is solved; `lockedBody` is diegetic, e.g. *"You can't judge this stand
  yet — weigh the hollow and the fen first, then come back to it."* Boss lantern `availableWhen:
  {allSolved:[hollow,fen,kinds]}`.
- **B:** bake each place's **constant character** (dappled sunlit hollow / gloomy boggy fen / bright open
  clearing / exposed high crown / the warm oak-hollow roost) — **not** a morning→snow *sequence*. The
  **winter clock** rides the **global ambient**: Tier 1 = `leaves` (or a fixed light snow) throughout +
  the clock in the entry/prompt text; Tier 2 = ramp `leaves → snow` with `rooms_solved`. Revisiting the
  hollow to study heights then shows the hollow + the current season, never a backward jump. **This
  removes the earlier "light/season arc baked per room" design** (was in `notes.md` / the scene prompts);
  the height wandering the escape needs is now fully consistent.
- **Rework needed if adopted:** rewrite the 5 `scenePrompt`s to place-constant (strip the ordered
  morning→snow phrases), set doors to all-open, add `availableWhen` + `lockedBody` to the 4 graded puzzle
  hotspots, and set the ambient strategy (Tier 1 now / Tier 2 flagged). Update `AGENTS.md` +
  `scenario.json`.
- **REALISED 2026-07-26.** `squirrel/scenario.json` rebuilt to a **16-node open world** on this model
  (place-constant art + global `leaves` ambient; open passages; the 4 lanterns availableWhen-chained; 6
  transition rooms driving `heights_read`; the roost escape gated `{gte:['heights_read',6]}`). Model
  **expanded in that session** from Lucas's room-count design: **8 tree rooms (2 reps × 4 colours) + 6
  pairwise transition rooms** — the heights themselves are the escape's data, learned by flying. See
  `rooms/comparing_means/squirrel/{notes.md → Design record v2, AGENTS.md}`.

## Open decisions for Lucas

1. **Adopt this as the standard model** for new scenarios (and retrofit others over time), or squirrel-only?
2. **Build the two engine features** (`availableWhen`+`lockedBody`; state-driven ambient ramp)? #1 is
   needed for true open-world ordering; #2 is the visible-clock payoff (Tier 2). Both are small but they're
   harness/JS work only Lucas can build+test.
3. **Tier 1 vs Tier 2 for the clock** (text + fixed ambient now, or wait for the ramp).
4. **Entry cards in an open world** — keep as one-time first-visit triggers (needs a tweak) or drop them
   in favour of front-loaded goal + in-place signage?
