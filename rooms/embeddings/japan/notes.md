---
authority: intent
---

# Embeddings scenario — "Wind Shrine" (dir `japan`) — PHASES 1–2 (puzzles + data, story)

Chapter: **embeddings** (book ch. 13, protein language models). **Scenario title: "Wind Shrine"**
(Lucas 2026-07-22 — "if a person understands the wind shrine, they can solve this world"). **Dir slug:
`japan`** (renamed from the phase-1 working name `rice` on 2026-07-22). Session "Japan", started 2026-07-22.

Status: **phase 1 (puzzles + data) complete; story phase essentially complete** (see the `## Narrative`
section below). Next pipeline phase: `escape_room_design` (scenes / door graph / scenario.json).

## Analog grounding

Embedding similarity = **finding the closest match by *kind*** when the matching has already been reduced
to numbers. Everyday act: a matchmaker / librarian handed a pile already arranged so that things of the
same kind sit near each other, and asked "what's nearest to *this* one?" — **retrieval**. The technique's
trap (and the boss): a **false friend** — an item sitting right next to your target that *looks* like it
belongs but is actually a different kind. That recognition move (spot the near-neighbour that doesn't
truly match) is the seed the story phase will build the data-free escape from.

## Book alignment + the lesson we must ADD

Read book ch. 12 (language models / text) and ch. 13 (protein language models). **Both teach the same
pipeline: embed → PCA to 2D → plot → eyeball the clusters.** Neither teaches **distance measurement
(cosine similarity), a distance matrix, or programmatic retrieval / nearest-neighbour** — the original
`rice_proteins` text exercise did its "closest match" by reading a dendrogram tip.

Our ladder is built on *retrieval*, so it teaches something the book doesn't yet carry. Two consequences:

- **>> FOLLOW-UP (chapter 13): add a distance/retrieval + cosine-similarity lesson to
  `integrated_bioanalytics/chapters/13_protein_language_models.Rmd`**, so the room tracks the book.
  Cosine is basic (dot product over magnitudes); Lucas will provide a **helper function** students use
  throughout. Also mention euclidean via base R `dist()` (WebR-fine).
- **Do NOT grade off a 2D PCA plot or a dendrogram.** Our clean single-winner answers live in the full
  960-D cosine space; a PCA/tree projection can reshuffle who looks nearest and quietly break the key.
  Compute distance directly. Bonus: retrieval-not-tree **sidesteps the ggtree-in-WebR blocker** entirely.

## Dataset

- **File:** `websites/thebustalab.github.io/phylochemistry/sample_data/rice_proteins_embeddings_merged.csv`
  Public URL: `https://thebustalab.github.io/phylochemistry/sample_data/rice_proteins_embeddings_merged.csv`
- **Provenance (NOT engineered — real data merged):** Lucas generated `rice_proteins_embeddings.csv`
  (57 rice proteins × **960-D protein-LM sequence embeddings**, ESM-C hidden size; keyed by
  `fasta_header` = UniProt entry name). This agent left-joined the original
  `rice_proteins.csv` (`ID_number` / `Protein_name` / `Protein_function`) onto it by protein id
  (all 57 matched, no misses) → merged file has `ID_number, Protein_name, Protein_function, dim_0…dim_959`.
- **Sequence embeddings, not text-of-function** (deliberate — Lucas's call; more interesting + no live API,
  and it's his research area). This **flips the answer** from the old text exercise: text version's nearest
  to beta-glucosidase-12 was BGL07; **sequence version's nearest is BGL06.**
- **Clustering is mushy** — mean-pooled PLM vectors of these full-length multi-domain proteins do NOT
  split into tidy families (BGL12 sits in a 30-of-57 blob even at k=8). So **no "which family / how many
  in the cluster" room** — those have no clean answer. Nearest-neighbour / retrieval is crisp; the ladder
  uses that.

## Verified ladder (3 rooms + boss) — reverse-engineered from the boss

Hero protein throughout: **BGL12_ORYSJ** (Beta-glucosidase 12). All values cosine similarity, verified
against the merged CSV.

BGL12 nearest neighbours (for reference): BGL06 **0.954** · BGL07 0.923 · **AGAL 0.921 (false friend)** ·
BGL18 0.903 · HXK6 0.895 · then a clear drop.

- **Room 1 — pairwise (learn cosine).** Compute cosine of BGL12 to two candidates and say which is nearer:
  a beta-glucosidase (**BGL07 ~0.92**) vs an unrelated enzyme (e.g. UGT79 ~0.70 or HXK6 ~0.90). Answer =
  **the glucosidase**, big margin. Deliberately does **not** use BGL06 (that's room 2's answer).
  *Puzzle type: **Type 1 Compute-the-Key** (console-`check` on the helper's output).* Plants "proximity = similarity".
- **Room 2 — nearest in the whole library (retrieval) + PLOTTING.** Cosine of BGL12 to all 56 others,
  rank, take the top. Answer = **BGL06** (0.954; runner-up BGL07 0.923, ~0.031 clear / ~30% further in
  euclidean — clean single winner). *Puzzle type: **Type 4 Pick-the-Point** — student writes plotting code
  to make a similarity-to-BGL12 ranked bar/point plot, then **clicks the top bar (BGL06)** on a live
  ggiraph plot. This is the "plot picker" + forces plotting.* Distractors present (BGL07/AGAL/BGL18/HXK6 near; GLGB far-but-name-plausible).
- **Room 3 — retrieve AND verify (the move the boss hinges on).** New move: don't just trust proximity —
  pull the neighbour's `Protein_function` and confirm it does the same job, on a case where it **holds up**:
  target **P2C06_ORYSJ**, nearest = **P2C50_ORYSJ** (0.958, gap 0.059 — both Protein phosphatase 2C, a
  genuine functional match). *Puzzle type: **Type 3 Repair-the-Pipeline** — a colleague's broken retrieval
  snippet (e.g. sorted ascending / forgot to drop self / wrong column); fix it so it returns P2C50, then
  read the function to confirm.* This is the "fix the colleague's bad code" room.
- **Boss — top-k retrieve + spot the FALSE FRIEND (the taught trap / misdirection).** Retrieve BGL12's
  **three** closest neighbours — BGL06, BGL07, **AGAL** — read the three functions, and name the impostor:
  **AGAL_ORYSJ (alpha-galactosidase, EC 3.2.1.22)**, which the model parked among the beta-glucosidases
  (EC 3.2.1.21) because it shares the fold but runs the *opposite anomeric* reaction. **Single non-glucosidase
  in the top-3 → clean single winner.** Misdirection: tempting to say "all three sit next to BGL12, so all
  three are matches." *Puzzle type: **Type 2 Classify-the-Unknown / verdict** (MCQ or console-`check`
  `impostor <- "AGAL_ORYSJ"`; consider one-shot).* Teaches the core embeddings caveat: embeddings capture
  sequence/fold, which **usually but not always** tracks function.

**Escalation is strictly monotonic:** compare one pair → rank the whole library → rank + verify function
(confirms) → rank + verify function (subverts, with misdirection). **Puzzle-type variety: Type 1 → 4 → 3 →
2 (four different types).** All four engines are already BUILT (check primitive, ggiraph Pick-the-Point,
Repair-the-Pipeline, verdict). Plotting lands in room 2; debugging in room 3.

## Escape (SEED ONLY — designed in the story phase)

Boss's core cognitive move to hand to `escape_room_story`: **spot the member of a near-group whose *kind*
actually differs — the false friend.** A data-free, in-world recognition of that move. Do not design here.

## Judgement calls / open decisions (for Lucas)

1. **Sequence vs text embeddings** — went with **sequence (PLM)** per Lucas; answer moves BGL07→BGL06.
2. **False-friend boss** — the AGAL alpha-galactosidase impostor is the pedagogical centrepiece; makes the
   scenario "about" the sequence≠function caveat, not plain retrieval. Lucas endorsed the spine.
3. **Add cosine/retrieval lesson to book ch. 13** (see follow-up above). Lucas will supply the helper fn.
4. **Pairing (pre/post twin) — TBD.** Chapter convention: two scenarios, different data/target, same
   question style. A twin embeddings scenario (different hero protein / organism, same retrieve-and-spot-
   the-false-friend shape) is not yet designed. Flag for later.

## Housekeeping

- **Codec id:** `scenario_inventory.json` `next_free_id = **11**` (reserve when scenario.json is scaffolded).
- **No git on this box** — site is a Mac-only repo; Syncthing carries edits.
- Merged dataset written this session; original `rice_proteins_embeddings.csv` + `rice_proteins.csv` left intact.

---

## Narrative (STORY PHASE — WORK IN PROGRESS, brainstorm 2026-07-22, session "Japan")

**Status:** actively brainstorming with Lucas. World essentially built; escape mechanic conceived;
several geography/opening details still open (see *Open decisions*). Captured so nothing is lost —
**NOT yet the final locked spec**, and phase-exit story-map cards are not drafted. Do not treat as
phase-complete.

### Logline / stakes / clock
- **World:** an isolated archipelago of tall rocky sea-stacks, terraced rice paddies on their ledges —
  an **agricultural research station** breeding rice to stand tall and strong against the region's typhoons.
- **Protagonist:** a lone worker at the station whose hobby is **photography** (replaces the original
  exercise's "Aria Tobihara" placeholder — name TBD).
- **Stakes:** a **typhoon is coming**. The station must certify the *true* defence enzyme before it commits
  this season's seed — and the trap is a **false friend**, an enzyme sitting right beside the target that
  runs the *opposite* reaction; graft it by mistake and the crop is ruined, not saved. (This is the AGAL
  alpha-galactosidase impostor from the verified ladder, given real-world consequence.)
- **Clock:** the incoming typhoon, made visible by a **wind-and-tide gauge / storm post**. Escape = float
  the beached boat out to sea ahead of the storm, rice saved behind you.

### The one grammar of this world: playable lanterns
- Lanterns hang **everywhere** — they read as ambient set-dressing, but they are the **data**. Each lantern
  is a **hotspot; click it and it plays its tone.** (Simplified 2026-07-22: lanterns do NOT light up or
  toggle art — "you can just play them" is the whole mechanic; the earlier ignite/quench art-toggle was
  dropped as too hard to build.)
- **Cosine similarity, made sensory:** a lantern's **brightness = magnitude** (ignored, misleading), its
  **pitch = direction = kind**. Two lanterns of very different brightness can ring the *same* note = same
  kind. So the false friend can be the **brightest** lantern in a row (obvious visual match) yet ring an
  **inverted/odd tone** — obvious-but-wrong vs careful-and-right, split across eye and ear. Boss
  misdirection made physical.
- **The repeated move:** in each room you **play the lanterns and find the odd one out** (the play *order*
  doesn't matter — the odd tone is what counts). This rehearses the false-friend recognition before the
  boss, and the odd-toned lantern becomes that room's **escape token**.

### Geography + walkthrough (RESOLVED 2026-07-22)
Hub-and-spoke: **one tall central island + three outer puzzle islands**. Concrete route:
1. **Quarters** (base of central island, door already open) — you learn you're a **photographer**; the
   scenario + the **incoming typhoon** are explained.
2. Step outside to the **outdoor rice-paddy** by the quarters — the hub, with **two paths**:
   - **Down** to the **marooned boat + the water source / waterworks** (sea-cave level). Visited **early so
     the player sees them** (Chekhov's gun for the finale) — *still need a diegetic reason to go down early; TBD.*
   - **Up** to the **wind shrine** at the summit — the **instrument** there plays the lanterns and **teaches
     the lantern grammar**.
3. Over the summit and **down the far side** to a **landing platform** looking out on the **three outer
   islands**, each bearing a **solid**: **sphere / pyramid / cube** (Lucas slipped and named four shapes —
   "triangle" = the pyramid; there are **three** rooms), each with a little landing porch + entryway.
4. On the platform's cliff side, a **dial** spins to swing the **rope bridge** to whichever outer island —
   the spoke system. **All open — any order.**
5. **Three outer islands = the three graded puzzle rooms** (ladder rooms 1–3). See *escape* for how a solved
   room yields its photo-token.
6. Back over the summit, **descend past the rice paddy to the lower sea-cave level** — the **boss lives in
   the sea-cave** by the boat. Beat the boss → last photo → four digits → keypad → drain → float boat → **escape**.

**Env arc rides the route:** low storm-light at the boat → climb to the wind shrine → out across bridges to
the solid-islands → descend to the sea-cave as the typhoon lands. Rise then descend, as wanted.

**Travel mechanic settled:** the **bridge-dial** (hub/spoke) is the signature; the **paddy-drain** is
reserved for the **escape** (drain routes water to float the boat), not a general travel mechanic. Confirm
harness support (dial-driven bridge, sea-cave keypad, camera-gated photo tokens) in the design phase.

### Per-room story beats — OUTSTANDING (write next)
Walkthrough + token logic are set, but each room still needs a **plot reason its analysis matters** (the
skill's core "every room is a BEAT, not a reskin"). To write, for rooms 1–3 (learn-cosine pairwise →
nearest-in-library → repair the colleague's broken retrieval code) and the boss (spot the false friend):
*why does the photographer run this exact analysis now, and what does its answer unlock in the plot?*
Currently the honest answer is close to "so the player does the puzzle" — that's the gap to close before
phase exit.

### The "solid" rooms (AMBITIOUS — art-phase to attempt)
- Lucas wants each outer puzzle room to be **inside a giant platonic solid — a sphere, a pyramid, a cube** —
  lanterns hung within. Rationale: unforgettable, AND it **hearkens to the high-dimensional nature of
  embeddings**. He wants to **push the AI image generator** to realise it despite the difficulty.
- The solid doubles as the room's **identity/symbol** for the escape's inventory-slot correspondence (below).
- **Flag:** "convincingly inside a giant sphere" is a hard 360° scene to generate — a **design/art-phase
  risk**, not a story lock. **Fallback if the art won't hold:** Japanese architectural forms as the
  room-symbols (moon-gate circle, torii gate, pagoda tiers, stone-lantern silhouette) — iconic,
  unmistakable, cheaper. Decide in design.

### The escape (data-free, synthesised across rooms → ceremonial release)
- **Not** "pick the one odd lantern" (too guessable). Instead a **collection → arranged code**:
  - Lanterns in each room are **always playable**; the **gate is the camera/notebook**, not the lanterns.
    Solving that room's **graded WebR puzzle unlocks the photo**, and you **photograph the odd-toned
    lantern** — the recognition move captured in-world. The photo (a **lantern-card with a little number**)
    lands in your **notebook/image inventory**. (Resolves the "condition the lantern info on solving"
    tension: the world stays open, but the *token* only lands on a correct WebR answer.)
  - **Four photos total** — the three outer rooms + the **boss** (the last photo). Each room's **symbol**
    (its solid) tells you **which slot** its card goes in.
  - At the finale you **arrange the four cards in order** by their room-symbols and **read the numbers off**
    → a **four-digit code**. (Borrows the proven **hospital postcard** mechanic.)
- **Ceremonial release:** the code opens a **modern digital waterworks lock** (the island has modern paddy
  drainage). Draining the paddy **routes water to float the beached boat**, and you **sail out ahead of the
  typhoon** — rice saved, you escaped. **One control, one motion**; the boat-float is a bespoke finale
  state-change, not a reused travel mechanic (a nice distinction).
- On-spec: recognition (not computation), **no CSV/console/dataset values**, answer synthesised from the
  earlier rooms, single ceremonial gesture. ✓

### Environmental arc (DRAFT — for design)
Start low at the boat (storm-light gathering) → **climb** the central island to the wind shrine (wind,
height) → **dial out** across bridges to the outer solid-islands (mist, sea-spray) → typhoon building
throughout (the clock) → **descend** to the boat / waterworks / sea-cave for the finale as the storm makes
landfall. **Rising then descending** — Lucas wanted an earned descent for contrast.

### Recurring motif: the mirror
Flooded terraced paddies are **mirrors** — the landscape reflects the sky from the first frame. The anomeric
flip (alpha vs beta = mirror-image) is **foreshadowed visually** throughout; only late does "a mirror can
mean same-shape-opposite-kind" pay off. Mirror is a **motif**, deliberately **not** the whole escape.

### Cast
- **One colleague** — justified by ladder **room 3 (Repair-the-Pipeline: fix the colleague's broken
  retrieval code)**. Present mostly through what they left behind (ledger/notes). Keep the cast this small.

### Open decisions (updated 2026-07-22)
**Resolved this session:** opening route (quarters → paddy hub → down-to-boat / up-to-shrine → landing
platform → three solid islands via the bridge-dial → back → **sea-cave boss** → escape); **four photo-tokens**
(3 rooms + boss) → four-digit keypad code; lantern-gating = **camera unlocked by solving the WebR puzzle**;
signature travel = the **bridge-dial**, paddy-drain reserved for the escape.

**Still open:**
1. **A diegetic reason to visit the boat / water source early** (so the player sees them before the finale). TBD.
2. **Per-room story beats — the biggest remaining gap** (see the *Per-room story beats* section above):
   *why* the protagonist runs each exact analysis now and what it unlocks in the plot — not "solve to open the door."
3. **Solid-rooms vs Japanese-form symbols** — pending the art phase's read on whether "inside a giant solid"
   renders (fallback: moon-gate / torii / pagoda-tier / stone-lantern).
4. **Protagonist name** (replace "Aria Tobihara").
5. **Harness confirmation** (design phase): dial-driven bridge, sea-cave keypad, camera-gated photo tokens.

### Story-map card text (DRAFT 2026-07-22 — Voice A, ready to paste into the harness story-map)
Protagonist kept **second-person / unnamed**; colleague **unnamed** (both easy to name later).
**Title:** **Wind Shrine** — chosen by Lucas 2026-07-22 ("if a person understands the wind shrine, they can
solve this world"). *(Superseded working options: Windfast / Tall Rice / The Odd Bell / Windward Terraces.)*

**title:** Wind Shrine

**subtitle:** The storm is a day out, and the season rides on one true match.

**story (opening / landing screen):**
> For three seasons you have coaxed a rice that stands where the typhoons flatten everything else — tall,
> deep-rooted, unbroken. The trials are scattered across the terraced isles, each plot testing a candidate for
> the one protein that lets the stalk hold. Today the last data is due, and the glass is falling. The
> wind-gauge in the sea-cave reads a day, no more, before the storm closes the bridges and floods the paddies.
> Gather every trial's answer, choose the true match, and be gone before the water rises. Your camera is
> charged. The bells are strung. Go.

**entry — sea-cave:**
> The path drops through wet stone to the cave mouth, where your boat lies canted on the rocks, hull dry,
> going nowhere. Beside it a modern panel blinks — the drain-lock, four digits, sealed. The wind-gauge needle
> trembles: less time than you'd hoped. Everything you decide up on the terraces comes back down here.

**entry — wind shrine:**
> The climb ends in wind and open sky. Lanterns crowd the old shrine, hundreds of them, and when you brush one
> it answers with a clear note. Here the keepers left their teaching: among any cluster of near-kin, one voice
> never quite matches the rest — and it is that odd note, not the brightest lamp, you are to mark. Learn the
> ear now. The terraces will test it.

**entry — island 1 (trial 1, calibrate):**
> A single plank bridge waits, already strung to the first plot. This is where you began, seasons ago — the
> calibration trial: a known cousin and a known stranger set beside your candidate so the instrument could
> learn true kin from false. Read it once more, and trust nothing downstream until it rings right.

**entry — island 2 (trial 2, retrieve nearest):**
> The basket unlatches; the rope-bridge swings out and settles across the gap. On this plot the question
> widens: of every protein in the library, which stands closest to your candidate? Not near — nearest. Find
> the one, and photograph its bell.

**entry — island 3 (trial 3, the colleague's plot, verify):**
> This plot was your colleague's, and their retrieval ledger is a mess — a line transposed, the self-match
> left in, the sort run backwards. Set it right. Then do the thing they were careful about: don't take the
> nearest on faith — pull its function and confirm it does the same work. Here, it holds.

**entry — boss island (the decision trial):**
> The last bridge lands you on the boss plot as the light goes bruised and low. This is the choice the whole
> season rode on: your candidate's three closest kin, laid out together, and one to breed into the line. Two
> are true. One sits among them wearing the same shape and running the opposite reaction — and if it goes into
> the seed, the crop dies standing. Trust the ear you trained. Name the false one.

**done (analysis complete):**
> Four trials, four honest photographs. The false match named and set aside, the true partner marked for the
> seed. The season is saved on paper — now you have to make it off the isles.

**escapeDone (you escaped):**
> The code takes. Deep under the terraces the sluices open, and the paddy you tended for years pours out
> beneath the rocks — lifting your boat, inch by inch, until the hull floats free. You pull for open water as
> the first rain hits the sails. Behind you the tall rice bends and does not break. The storm has the isles;
> the harvest is yours.

**Voice notes:** earnest, concrete, salt-and-cedar sensory; mood rises (wind, open sky at the shrine) then
darkens (bruised low light, rain at the boss/escape); cards kept short; the "tall rice bends and does not
break" payoff closes the loop on why the whole season mattered.

### Wind-shrine teaching — OPEN (discuss next)
Lucas's flag: the entry card *states* the rule, but it's not yet clear **how interacting with the shrine
teaches "the odd-ringing bell (not the brightest) is the one to photograph."** Needs a concrete interaction
design (candidate: a no-stakes practice cluster + first-photo tutorial + the brightness decoy planted here).
Resolve before phase exit.

### Music — READY (wire when scenario.json is assembled)
Lucas chose the looping ambience (2026-07-22): the **first 33:20** of https://youtu.be/l4vkouAwuec,
**looping with a 20s crossfade** (seamless — tail blended into head, so the player's hard loop has no seam).
Pulled via a `youtube_audio` observer row (`--section 0:00-33:20 --crossfade-loop 20 --bitrate 128K`) to
**`audio/wind_shrine.mp3`** (in this scenario dir). When the `scenario.json` is built, set:
`"music": "audio/wind_shrine.mp3"`, `"musicVolume": 0.12` (tune to taste), and
`"musicCredit": {"text": "DJ KRUSH — live at 大中寺 (Daichuji), MUSO Culture Festival 2021", "url": "https://youtu.be/l4vkouAwuec"}`.
(Credit confirmed by Lucas 2026-07-22 — a temple DJ set, which fits the Wind Shrine world nicely.)
