---
authority: intent
---

# Two new puzzle types — Deduction Ledger & Inference Board (build-ready drafts)

Full specs for catalogue entries #9 and #11 in `puzzle_inventory.md` — drafted 2026-07-18 for use in
future rooms (not built yet). Both teach a mode of reasoning the current MCQ / console-check / lock
vocabulary can't reach. Companion to `puzzle_types_design_notes.md` (the console-check puzzle types).

**The pair, in one line:** the **ledger** is for *classification* (assign many entities to groups —
clustering chapters); the **inference board** is for *confirmatory reasoning* (chain a few pieces of
evidence into one conclusion — multi-condition / diagnostic scenarios).

---

## Type 4 — Deduction Ledger (`type:"ledger"`)

**Root:** *Return of the Obra Dinn*'s crew book — assign a verdict to every entity in a grid.

**The soul of it — the confirmation rule.** The ledger never confirms a single row. It confirms a
**GROUP** only once every member of that group is simultaneously correct, and reveals *nothing*
per-row. So you can't fish one cell at a time for a green tick — you reason until you're confident a
whole *cluster* hangs together, and being right about the cluster is what unlocks it. That is the whole
pedagogical point: it mirrors how you actually gain confidence in a clustering (a cluster is "right"
when its members belong together), and it kills guess-and-check.

**Data-learning fit.** Classification / clustering. The student does the real analysis in the WebR
console (hclust, k-means, PCA), reads off which group each entity belongs to, and fills the ledger from
that. Pick a dataset where **eyeballing fails** so the console work is necessary.

**Worked example — Flat Clustering, `tequila_chemistry` ("is 1800 Añejo really aged?").** Ledger rows =
~10 bottles; the verdict dropdown = {aged, silver}. The student runs PCA + k-means, sees the two
clusters, and assigns each bottle. The **aged** group and the **silver** group each lock in as they
become fully correct — and 1800 Añejo is exposed by landing in the *silver* locked group. (Also fits
the forensic `wood_smoke`/`unknown_smoke` red-oak-vs-birch, and `chemical_blooms` species clusters.)

**Schema (draft).** Groups are *derived from the answers* — no separate group config; the group for
verdict `V` = all rows whose `answer` is `V`, and it confirms when the set of rows currently set to `V`
exactly equals that group (right members, no false-positives).
```json
{
  "id": "obj_ledger", "type": "ledger", "label": "The assay ledger",
  "box": [ ... ],
  "starterCode": "# solvents/tequila loaded as `tequila_chemistry` — cluster it, then fill the ledger.\ntequila_chemistry",
  "prompt": "Assign each bottle to its cluster. A group locks in only when every bottle in it is right.",
  "options": ["aged", "silver"],
  "rows": [
    { "id": "cazadores_anejo", "label": "Cazadores Añejo", "answer": "aged" },
    { "id": "1800_anejo",      "label": "1800 Añejo",      "answer": "silver" }
  ],
  "feedback": { "correct": "Every group confirmed — the fraud stands exposed.", "progress": "{n} of {m} groups confirmed" }
}
```

**Engine work.** New `ledger` puzzle type in `pano-player.js`: render a table (rows + a `<select>` per
row) beside the live console; a **"Check"** button evaluates each verdict-group by exact-match, **locks**
confirmed groups (rows go read-only + green), shows progress `"{n} of {m} groups confirmed"`, and calls
`solveRoom` when all groups lock. **Codec:** it's a graded gate → encode `answer = 1` (solved) +
attempts, exactly like a console-check room (the decoder key entry is `1`); no codec-scheme change.

**Design rules / open Qs.** Want **≥2 groups** so partial confirmation can guide (one group = degrades
to all-or-nothing, which loses the soul). Keep rows ~6–12 (more = tedious). Decide whether to offer an
"unassigned/?" option (Obra Dinn does). Verify against the dataset that the clusters are clean and that
eyeballing without the analysis won't crack it.

---

## Type 5 — Inference Board (`type:"inference"`)

**Root:** *Outer Wilds*' ship-log / rumour board — knowledge as a web of connected facts; progression
gated by understanding, not items.

**What it is.** Your **field notebook** already collects fragments (`pickup` clues + solved-puzzle
facts). The inference board turns that flat list into something you **connect**: the player links the
clues that support a conclusion, and making the **right set of connections** confirms it. It makes the
meta-puzzle (combining fragments) a *visible, manipulable act* instead of an in-your-head one — and it
teaches that a scientific conclusion is a **structure of linked evidence** (necessary conditions,
co-confirmation), not a single lookup.

**Build in two tiers — do Tier 1 first.**
- **Tier 1 — "support-select" (lighter).** State the conclusion; the player selects the subset of their
  collected clues that supports it (a multi-select of notebook fragments). Confirms when the selected
  set equals the required supporting set. No graph drawing; reuses the notebook clue pool. **Start here.**
- **Tier 2 — node graph (full).** Nodes = collected clues + candidate conclusions; the player draws
  links; a conclusion confirms when its required incoming links are present. Graph UI (click-to-link).
  More work; only if Tier 1 proves it's worth it.

**The confirmation rule.** A conclusion requires a specific SET of supporting clues — and it must be
the *right* set: requiring **both** chloride-high AND sodium-high (not either) teaches co-confirmation,
and including **distractor** clues that don't support it teaches *necessary vs irrelevant* evidence
(selecting a distractor fails the check).

**Data-learning fit.** Confirmatory / diagnostic reasoning — multi-condition scenarios. **Worked example
— Hawai'i "Saltwater Intrusion":** across the rooms the player collects nodes "KEEI_B chloride 280 (>250)",
"KEEI_B sodium 180 (>150)", "KEEI_B is a coastal Kona well", plus a distractor "aquifer_1 sulfate under
the line". The board's conclusion **"Seawater is intruding into KEEI_B"** confirms only when *both* the
chloride and sodium nodes are linked (the real two-key test) and the distractor is not — the student
literally draws the co-confirmation. Also fits the airship's three-property cure, and Comparing Means
("a difference exists" + "it's significant" → the claim).

**Schema (Tier 1 draft).** The option pool is the player's collected clues (by `pickup` id); `requires`
lists the ids that must be selected.
```json
{
  "id": "obj_board", "type": "inference", "label": "Your case board",
  "box": [ ... ],
  "conclusions": [
    {
      "id": "intrusion",
      "statement": "Seawater is intruding into KEEI_B.",
      "requires": ["clue_cl_over_250", "clue_na_over_150"],
      "feedback": { "correct": "Two markers, one well — intrusion confirmed.", "wrong": "One reading alone can be a fluke — what co-confirms it?" }
    }
  ]
}
```

**Engine work.** Tier 1: a modal listing the player's collected clues as checkboxes + the conclusion
statement + a **"Confirm"** button; passes when the checked set equals `requires`. Reads the existing
`caseFile`/`pickedClues` notebook state. Moderate. Tier 2 adds the graph canvas + link interaction
(higher). **Codec:** the board is most naturally the **escape/meta layer** (it replaces "type the
synthesised code into a lock" with "assemble the inference") → **ungraded, not in the codec**; but it
*could* be a graded analysis gate (encode `answer = 1`) if a scenario wants it on the graded path. Note
which per use.

**Open Qs.** Tier 1 vs Tier 2 (recommend Tier 1 first). Does it *replace* the escape lock or complement
it? How many clues/distractors before the multi-select gets noisy? Requires the notebook to expose
stable clue ids for `requires` — confirm `pickup` ids are addressable.

---

## Where these sit vs what exists

- **Graded analysis path:** MCQ (`question`) · console-check (`check`) · **Deduction Ledger** (new).
- **Escape / meta path:** the no-instructions **lock**, the **dial + mapview** world-state mechanic,
  and the **Inference Board** (new) — the board is the natural richer form of the scattered-fragment
  meta-puzzle (#2) once the field notebook is carrying the fragments.
