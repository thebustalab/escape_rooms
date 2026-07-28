---
authority: intent
---

# Reusable console puzzle types — design spec

Status: design (2026-07-15). **UPDATE 2026-07-16 — the shared `check` primitive below is
BUILT** in `shared/pano-player.js` (Phase 4 of `rooms_refactor_plan.md`): a puzzle carries
`check:{prompt,requires,expr,hint,maxAttempts,feedback}`, graded on the live R session via
`webR.evalRBoolean`. Hawai‘i room1 is the pilot (a Type-1 Compute-the-Key). Types 1–3 below are
now authoring patterns over that primitive; the codec `solved`-byte change is still pending (Phase 5).

Reusable puzzle "types" for the
Integrated Bioanalytics escape rooms, each tied to real coding skills from the
book and authored once, reused per chapter by swapping dataset + check. Grounded
in `teaching/CHEM5725/exercises.csv` (every existing exercise is a Type 1).
Types 1–3 grade on the shared `check` primitive (below); **Type 4 (Pick-the-Point,
added + feasibility-verified 2026-07-22)** grades on a click on a live ggiraph plot.

## The shared primitive — the console `check`

Today the engine grades a multiple-choice **index**: `makeQuestionCard` compares
`selected === q.correct`. The live WebR session (`WebRConsole.webR`) is never
inspected — the console is a scratchpad the student reads an answer *out of*,
then clicks a radio button.

Every type below leans on one new capability: **grade on the R session state.**
A node/step may carry a `check`:

```js
check: {
  requires: ["answer"],                    // vars that must exist first
  expr: "round(answer, 2) == 6.83",        // R expr → single logical, run in the student's session
  hint: "Assign your result to `answer`."  // shown if requires missing or expr errors
}
```

Engine support (one focused change, unlocks all three):

1. Expose the booted `webR` handle from the console to the question card.
2. Add a **Check my answer** button on a console-checked card. On click:
   - verify each `requires` var exists (`exists("answer")`); if not, show `hint`;
   - eval `expr` via `webR.evalRBoolean(expr)`; `TRUE` → solved, `FALSE` →
     wrong-attempt (same feedback ladder as MCQ).
3. **Codec:** a console-checked step encodes `answer = solved ? 1 : 0` plus
   `attempts` — fits the existing 5-bit/3-bit byte with no schema change. This
   also **retires the 32-option ceiling worry**: compound answers are checked by
   expression, not enumerated as options, so "class + count" tuples no longer
   need a 35-way option cross-product.

Everything else (`starterCode` per node, `maxAttempts`, two-dataset loading) is
already supported. MCQ grading stays available; a node picks `check` **or**
`correct`. Console-checked is the stronger, recommended default.

---

## Type 1 — Compute-the-Key (the backbone)

**Skill:** produce an analysis; its result *is* the answer. This is what all nine
existing quizzes already are (Q1/Q3). The craft is a dataset where the answer is
**un-eyeballable** — you must run the technique.

**Shape:** student writes a pipeline, assigns the result to a named variable,
hits Check; engine verifies the variable(s). Supports **compound** answers via a
conjunction in `expr` (the corpus's "class + count", "strain + significance").

**Worked example — wrangling (ch 6), `beer_components`** (real Q1):

```js
{
  key: "esters",
  technique: "group_by + summarise + arrange",
  prompt: "Rank the three most abundant Aliphatic_ester compounds in hops by " +
          "decreasing mean abundance. Assign their names, in order, to `top3`.",
  starterCode: "# hops esters → mean per compound → arrange desc → names → top3",
  check: {
    requires: ["top3"],
    expr: 'identical(top3[1:3], c("Methyl_6_methylheptanoate",' +
          '"Methylheptanoate","Methyl_2_methylheptanoate"))',
    hint: "top3 should be a character vector of compound names, highest mean first."
  }
}
```

**Reuse:** every chapter's Q1/Q3.
- PCA (ch 8): `which.max(abs(loadings[,"PC1"]))` name == biomarker.
- Comparing means (ch 10): a computed difference-in-means + significance flag.
- Data-vis (ch 3–5): the outlier only visible once faceted/log-transformed.

---

## Type 2 — Classify-the-Unknown

**Skill:** build a reference from labelled data, place a **mystery sample**
against it, return a verdict — often binary, often one-shot. Console-forced: the
verdict depends entirely on where the unknown lands. This is the dominant
structure in the back half of the corpus (guilty/innocent, poisonous/safe, which
patient) and *is* the escape-room narrative — there's always an unknown.

**Shape:** two datasets (reference + unknown); the student fits/clusters/embeds
the reference, projects the unknown, assigns a verdict variable. `oneShot: true`
→ `maxAttempts: 1`.

**Worked example — hierarchical clustering (ch 7), `wood_smoke` + `unknown_smoke`**
(real Q1):

```js
{
  key: "smoke",
  technique: "hierarchical clustering",
  oneShot: true,
  datasets: ["wood_smoke", "unknown_smoke"],
  prompt: "Cluster the reference smokes, place the jacket sample, and decide: " +
          "Red Oak or Paper Birch? Assign 'red_oak' or 'paper_birch' to `match`.",
  check: { requires: ["match"], expr: 'match == "red_oak"' }
}
```

**Reuse:** ch 7 dendrogram membership · ch 8 nearest in PCA space · ch 9 which
k-means/dbscan cluster · ch 11 model `predict()` class · embeddings nearest
neighbour by cosine. Same node shape; swap the technique that produces the
placement. Engine needs only the `check` primitive (two-dataset load already
works).

---

## Type 3 — Repair-the-Pipeline

**Skill:** read and debug real code — the one thing a conclusion-MCQ never tests
(a student can reach a conclusion with sloppy or AI-pasted code; they cannot fix
a broken pivot without understanding it). New to the corpus, deliberately.

**Shape:** `starterCode` pre-loads a nearly-right block that errors or returns a
telltale-wrong result. The student edits and reruns until the `check` on the
corrected output passes. The **error message itself teaches** — this is where the
live console earns its keep. (An MCQ "which edit fixes it" flavour exists but is
more guessable; console-checked is recommended.)

**Worked example — comparing means (ch 10), `algae_data`** (formula reversed):

```js
{
  key: "aov_fix",
  technique: "ANOVA",
  prompt: "This test should compare omega-3 abundance ACROSS harvesting regimes, " +
          "but the model is backwards and the p-value is nonsense. Fix it so " +
          "`fit` models abundance as a function of regime, then Check.",
  starterCode: "fit <- aov(harvest ~ omega_3_polyunsaturated_Fas, data = algae_data)\nsummary(fit)",
  check: {
    requires: ["fit"],
    expr: 'all.vars(formula(fit))[1] == "omega_3_polyunsaturated_Fas"',
    hint: "In aov(), the response goes on the LEFT of ~, the predictor on the right."
  }
}
```

**Reuse:** every technique has a canonical mistake — a ggplot missing its `aes()`,
a `pivot_longer` with the wrong `names_from`, a pipe with verbs out of order, a
`kmeans` with the wrong `centers`. Author the broken version + a check on the
corrected result.

---

## Type 4 — Pick-the-Point (make the plot, click the answer)

**Skill:** read a plot to find the extremum / outlier / right group, then **select it on the plot
itself** — the answer surface *is* the chart. This is the only type that genuinely forces
plot-reading: with the data too dense to eyeball as a table, the student must plot to see "which is
most", and the pick is registered by clicking the point (not typing a value or choosing a radio, both
of which a table-shortcut could satisfy). It's the live, data-generated evolution of the escape-only
**`h.map` pick-a-point** puzzle (`openMapPuzzle` in `pano-player.js`), which today uses a *pre-rendered
PNG + hand-placed clickable boxes* and is ungraded. Type 4 replaces the static image with a plot
generated live from the data, so the points and their hit-targets come for free.

**Feasibility — VERIFIED 2026-07-22** (this is the enabling finding, not a plan). `ggiraph` is in the
WebR wasm repo (R 4.4 `2.1.3`, R 4.5 `2.2.2`) with all deps (svglite, systemfonts, textshaping,
gdtools, uuid, xml2). A headless smoke test (`tests/ggiraph_smoke.mjs`, standalone — **not** in CI)
booted WebR in Chromium, installed ggiraph, and rendered
`geom_point_interactive(aes(data_id = lake, tooltip = lake))` to a `dsvg()` device. Every data point
came out as a clickable DOM node **tagged with its exact data identity**:

```
<circle id='svg_1_e1' cx='153.94' cy='16.92' r='4.27pt' … data-id='Lava_Lake' title='Lava_Lake'/>
```

So a click maps straight back to the row via `data-id` — **no coordinate inversion, no draw-order
guessing** (the fragile alternatives, since WebR's normal plot output is a flat raster canvas with no
geometry metadata). Timings in a fresh browser: WebR boot ~2.6s, ggiraph + deps install ~6.5s, render
round-trip ~8s → **~17s total**. Ran over WebR's **PostMessage** channel (no COOP/COEP headers), same
as the app's existing e2e. NB: the `dsvg` SVG single-quotes its attributes (`data-id='…'`) — match
either quote style when parsing.

**Shape:** the room runs a ggiraph plot → `dsvg(file = tempfile())` → `print(p)` → `dev.off()` →
read the SVG string back out of WebR's FS (`readLines`) → inject into the puzzle modal → a click
handler reads `evt.target.closest('[data-id]').getAttribute('data-id')` and compares to the answer,
with the same feedback ladder as the MCQ/`check` cards. The student still writes real plotting code in
the console to reason about the data; the picker is the graded "click the answer" surface.

**The picker now renders the STUDENT'S OWN plot (2026-07-28).** Two problems were fixed together:
(1) the picker **auto-drew** as soon as WebR was warm, so a student could open a pick room and click the
answer without plotting anything (Lucas caught this on alaska room3); (2) even after drawing, it rendered
the **authored** `pick.plotCode`, not the student's plot. Both gone. Now:

- The student builds their own ggplot in the console and **assigns it to `p`** (the schema gains
  `pick.idColumn` — the identity column, e.g. `"lake"` — and optional `pick.idNoun` for the error copy).
- "Draw the clickable chart" is gated on `p` being a fresh ggplot (`exists("p") && inherits(p,"ggplot")`;
  `p` is `rm()`-ed on modal open so each pick room needs its own plot — no stale carryover).
- The engine renders **that `p`** via `renderStudentPickSvg`: it swaps each layer's geom for its ggiraph
  interactive twin and splices `data_id = tooltip = !!sym(idColumn)`, so the marks on the student's chart
  become clickable + identity-tagged, then `dsvg` → SVG. `data_id` only needs the id column present in the
  layer data, so it's **robust to where `aes()` lives (ggplot() vs the geom), coord_flip, bars/points, and
  piped data** — validated end-to-end in a real browser+WebR by `tests/student_pick_smoke.mjs` (all four
  styles tag; both shipped answers clickable). If `p` isn't a taggable ggplot it throws → the card shows
  a distinct nudge ("assign your plot to `p`" vs "use a standard ggplot with one mark per <idNoun>").

`pick.plotCode` (the authored plot) is **retained as a reference/fallback but no longer rendered** in
normal play; `renderPickSvg` is kept for the old `pick_point_smoke.mjs`. Flow now: build your plot yourself
→ draw the clickable version → click your pick. (`buildPickCard`/`renderStudentPickSvg` in `pano-player.js`;
the e2e `solvePick` assigns `p` before drawing.)

**Engine — BUILT 2026-07-22** (`shared/pano-player.js`). `openPuzzle` dispatches `h.pick` →
`openPickPuzzle` (live console left + picker right). `renderPickSvg` runs the authored `pick.plotCode`
(leaves the ggplot in `p`) through ggiraph's `dsvg` device and returns the tagged SVG;
`buildPickCard` injects it, wires `[data-id]` clicks with the standard attempts/feedback ladder, and on
the correct pick reports `{ answer: 1, attempts }` — so it flows through `solveRoom → roomResults →
codec` **exactly like a `check`** (Lucas's decision (a): graded, in-codec; a pick room's decoder-key
slot is the solved byte `1`). `ensureGgiraph` installs ggiraph **lazily on first pick-room open**, so
only picker rooms pay the install. Validated in a real headless browser by `tests/pick_point_smoke.mjs`
(NOT in CI): boots WebR, loads the real alaska CSV, runs the R3 chloride plot → 20 unique `data-id`
bars, clicks `North_Killeak_Lake` → resolves correctly; ~16.6s total, ggiraph install ~2.6s.
Also fixed with it: `puzzleNoteText` now reads `pick.feedback.correct` (else a solved pick room logged
an empty note that `logToNotebook` dropped — no field-notebook entry).

**First consumer shipped (alaska, 2026-07-22):** R3 (chloride outlier → North_Killeak) and boss (warmest
→ Lava_Lake) are wired pick rooms; decoder key `c(3,2,1,1)`; `tests/e2e/alaska_full.spec.js` drives the
pick-solve (`solvePick` helper) and passes. So the full pipeline — engine, codec, wiring, e2e — is done
for the first Type 4 scenario; reuse it as the pattern for the next.

**Reuse:** any "which one is the extremum/outlier/odd-group" read across a set too large to tabulate —
data-vis outliers, the PCA biomarker point, the off-trend sample, a cluster's centroid. First intended
consumer: the **alaska** redesign (force a plot for the "most nitrogen / warmest lake" rooms; boss =
pick the warmest lake on the plot, subverting the primed high-chloride decoy).

---

## Build order (phased)

1. **Console-check primitive** + Check button + codec `solved` byte. Unlocks all
   three. Retrofit one existing `datavis1` MCQ to console-checked as the pilot.
2. **Type 1** — the backbone; convert the proven Q1/Q3 pattern.
3. **Type 2** — highest narrative payoff; the mystery-sample rooms.
4. **Type 3** — new pedagogy, smallest surface.

## Open decisions

- Keep MCQ as a fallback per node, or go console-check only once proven?
- Boss figure (Q2/Q4 image upload) stays hand-graded, or gets a lightweight
  `check` on the plot object's structure?
- Chapter 2 (data-vis II) room: which second dataset — reuse `solvents` (its real
  Q3) or pick one that hides a facet/scale reveal?
