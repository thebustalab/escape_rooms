---
authority: intent
---

# Egypt scenario (draft) — Data Wrangling

Chapter `wrangling`, scenario `egypt`. **Idea captured 2026-07-22 (Lucas, session Egypt).**
**Phase status (2026-07-22):** PUZZLE+DATA ✅ · STORY ✅ · DESIGN ⬜ (next) · art ⬜ · WIRING ⬜. Not yet
scaffolded (`rooms_built: 0`, no `scenario.json`). Codec id: take `next_free_id` from
`rooms/scenario_inventory.json` when scaffolded (11 at capture time; whichever of egypt / temple is
scaffolded first takes it — regenerate the inventory after).

## Role: the pre/post PAIR to `trees`

This is the **second `wrangling` scenario** — the pre/post partner to `trees`
("The Collector's Vault"). Per the chapter design principle (`../../../notes/puzzle_inventory.md`;
and `../trees/notes.md`), the pair asks the **same `group_by` + `summarise` question style** on a
**different dataset and story**. So Egypt inherits the *shape* of trees deliberately — three graded
group/summarise puzzles, a regroup boss, an ungraded "recognise the grouping" escape — but re-skins the
world (Egyptian port/market/library) and the data (`wine_quality`). Design it as a genuine twin, not a
clone: same skill exercised, different surface.

## Dataset — `wine_quality` (the class's own wrangling dataset)

`phylochemistry/sample_data/wine_quality.csv`. Chosen deliberately: the CHEM5725 Data Wrangling
exercise **already uses `wine_quality`** (e.g. *"which wine type has higher mean sulphate"*), so this
scenario mirrors the class exercise directly — the perfect partner dataset.

**Profile (raw):** ~6,497 wines. Categorical columns: `type` (red / white) and `quality_category`
(high / low). Score: `quality_score`. Then **11 physicochemical measurements** (fixed/volatile acidity,
citric acid, residual sugar, chlorides, free/total sulfur dioxide, density, pH, sulphates, alcohol).

**Data-engineering — RESOLVED 2026-07-22 (session Egypt): engineered `data/wine_cargo.csv`.** Profiling
confirmed raw `wine_quality` is **thin on categorical axes** — only `type` genuinely moves the chemistry
(red sulphates 0.66 ≫ white 0.49 — the real class-exercise answer); `quality_category` is just a
binarised `quality_score`, not an independent axis. So, exactly like the forest twin, a bespoke dataset
was engineered (keep a realistic wine skeleton, add cargo axes **region / varietal / vintage**, drive
each graded axis with an additive effect model, and build a **Simpson's-paradox flip** on
`quality_score`). See the **Verified puzzle slate** section below.

## The world — Egyptian port / market / library

Real-world anchor: **Alexandria** — the one place where a great **PORT**, a bustling **MARKET**, and
the **LIBRARY** genuinely coexist. Wine arrives **by ship as cargo**; the player comes in on that ship.
The three venues give a natural three-beat journey (**dock → market → library**) that parallels the
forest's three ascending stations.

- **Aesthetic — DECIDED 2026-07-22: Hellenistic Alexandria** (Ptolemaic port, the Pharos lighthouse,
  Greek-Egyptian market, the Great Library) — the honest anchor for the port+market+library trio.
  (Rejected an overtly pharaonic skin.) House teal-and-amber holds (torchlit stone, warm dusk, sea-blue
  harbour).
- **Tone — DECIDED 2026-07-22: not sad, mysterious is fine.** No burning-Library / loss beat. The mood
  is warm and intriguing, not tragic — matches the Glass Beams ambience.

## Analog grounding (Step 0 — the real-world act the code performs)

`group_by` + `summarise` = **sorting things into piles by a shared trait, then reading one number off
each pile.** In this world that is **cataloguing** — and cataloguing is exactly what a port, a market,
and a library *do* by hand:

- the **customs officer** at the dock tallies the cargo manifest — group the amphorae by origin, count /
  average per group;
- the **market steward** sorts goods into stalls by kind;
- the **librarian** shelves scrolls by subject.

All three *are* `group_by`/`summarise`. And — the recognition-not-computation move the escape needs
(per trees) — each collection has **already been organised** by someone; the player's job at the escape
is to **recognise which organising principle catalogued it**, not to compute it.

## Storyline sketch (TO DISCUSS)

The player arrives at Alexandria on a wine ship and must make their way **dock → market → library**.
Escape payoff — **DEFERRED 2026-07-22: settle the dataset + puzzles first, let them suggest the
stakes.** No burning / loss beat (tone decided: not sad, mysterious is fine). Surviving candidates,
both warm/mysterious:

1. **Clear customs.** The harbour won't release the ship (or you) until the **manifest is reconciled** —
   the cargo correctly grouped and tallied. Tightest fit to "wine as cargo."
2. **Earn your place.** A merchant-scholar must **deposit their cargo's record into the Library** to be
   admitted — organisation as the price of entry; a mysterious librarian gatekeeper.

(Rejected: the burning-Library payoff — too sad.)

**STORY FORK RESOLVED 2026-07-22 (Lucas): candidate 1 — CLEAR CUSTOMS.** Lean-story mandate
("minimum story needed to carry the scenario, so the player focuses on puzzle + data"). Full narrative
in the `## Narrative` section below.

## Narrative (STORY phase — clear customs; written 2026-07-22, session Egypt) — ✅ PHASE COMPLETE

Deliberately **minimal** per Lucas: the story exists only to give a reason you're grouping and tallying
cargo by hand, and a clock. No subplot, no cast to track — the port's law, one task, one gate.

### Logline / stakes / clock
- **Logline.** You've sailed into Alexandria on a wine ship; the harbour won't release you — or the ship —
  until the cargo manifest is reconciled: every amphora grouped by origin and correctly tallied.
- **Stakes.** Concrete and low-key (tone = mysterious/warm, not tragic): you're stuck at the customs gate
  until the numbers are true. A loud merchant's inflated claim about his cargo threatens to falsify the
  manifest — settle it and you clear customs.
- **Clock.** The **tide turns at dusk**; the ship must ride it out. The clock rides the scene light-arc
  the design phase will set: **dawn at the ship → midday glare in the market → gold dusk climbing to the
  Library → night and firelight atop the Pharos**, with elevation rising alongside (harbour level → up
  into the city → up the tower).

### World & cast (one place, one throughline)
Hellenistic Alexandria, the working harbour. **Fuller route approved 2026-07-22 (Lucas) — grow the
world:** the player walks **ship's deck → ship's hold → the quay warehouses (emporion) → market
(S2 · price) → market (S3 · the famous name) → the Canopic Way → the Great Library → back to the quay → a
skiff across the Great Harbour → up the Pharos lighthouse**, one continuous journey (~8–9 scenes). **Cast
kept minimal (Lucas, 2026-07-22 — fewer people = a simpler, more memorable story):** there is **no customs
officer and no beacon-keeper**. The two-part goal — **register the cargo** with the city, then **turn the
Pharos light onto the ship** — is **front-loaded in the opening**, so the player already knows what each
room and the finale are for. Where a character would only *explain* a mechanic, an obvious story set up
front does the job (the lighthouse is a **locked door** the player already knows to open, not a keeper who
grants entry). **The one kept character is the S3 merchant** — text-only flavour whose boast makes Chios
the tempting wrong answer; the officer, keeper and archivist are gone, and the three sigils are taught by
objects (count-board / price-board / reject-slate).

**Landmarks (the beautiful places, each earning its visit):** the ship (deck + lamplit hold), the
**emporion** warehouses, the **Canopic Way** colonnade, the **Great Library / Mouseion** (boss venue),
and the **Pharos lighthouse** (escape). **Signature travel mechanic:** a **harbour skiff** across the
Great Harbour to the lighthouse island, then the **climb** up the tower — the crossing + ascent are the
route to the finale, not a corridor (as the forest had its canopy rail-cars). The atmosphere / pickup-only
rooms (deck, hold, warehouses, Canopic Way) carry **no graded analysis** — they're where the 9 amphora
seals are gathered and the verb-workers appear; the four graded puzzles are unchanged. The escape's **sigil legend** (the three summarise verbs) is taught **without characters** — each station
carries a **register / board** that visibly performs one operation, tagged with its sigil, so the player
meets all three before the lantern:
- **SHIP'S DECK — the count-board / tally-stick**: a running notch-count of the amphorae → **`n()` /
  count** (tally sigil).
- **MARKET — the price-board**: the dearest lot marked highest → **`max()` / greatest** (up-chevron sigil).
- **MARKET — the reject-slate**: the poorest lots struck to the bottom → **`min()` / least** (down-chevron
  sigil).

(Per the fewer-people principle: the sigil meaning must read off the **object**, so no character is needed
to teach it. A light text-only touch at a station is fine, but never one the player must track.)

**The collectible:** through the day the player gathers **9 amphora seals** (image-card pickups — clay
tokens each stamped with a colour / shape / size + a merchant's tally numeral). These are in-world props
with **no tie to the wine data**; they are the material the escape reconciles. (Pickups must be reliable —
mandatory/auto — see the pickup-reliability flag in the escape section.)

### Per-room beats (why THIS analysis, right now — bends to the verified ladder, never the reverse)
- **S1 · SHIP'S DECK — open the manifest (Type 1 Compute-the-Key).** The first crates stand open on the
  deck at dawn, the count-board notching up beside them. Reds and whites are taxed apart, so the register's
  first, easy line is which the ship carries more heavily cured for the voyage. *Analysis:*
  `group_by(type) |> mean(sulphates)` → **red**. *Unlocks:* the manifest's first line is signed; you may
  go below to the hold and then ashore.
- **S2 · MARKET — price the cargo (Type 4 Pick-the-Point).** The market prices wine by the grape and the
  strongest pressings fetch most, so the cargo's value hangs on which varietal pours the most potent wine
  — too many grapes to eyeball, so you read it off the price-board's plot and click the winner. *Analysis:*
  `group_by(varietal) |> mean(alcohol)` → **Argitis**. *Unlocks:* the cargo is valued; its record sends
  you on to settle the loudest claim in the market.
- **S3 · MARKET — the merchant's boast, the SHORTCUT (Type 1 Compute-the-Key).** A **merchant** is loud
  over his stall, swearing his **Chian** amphorae are the finest cargo in the harbour and the tally will
  bear him out; the reject-slate nearby (the `min` board) strikes the poorest lots to the bottom. Take his
  boast at face value *for now*: group by island and read which region scores highest **as it stands**.
  *Analysis:* `group_by(region) |> mean(quality_score)` → **Chios** (count-weighted). *Unlocks:* you have
  the naive answer the boss will overturn — the trap is set in code, not sprung on you.
- **BOSS · LIBRARY — the true record, the REGROUP (Type 3 Repair-the-Pipeline).** The dispute climbs to
  the Great Library, whose ledgers keep the true record of every vintage. The catch is written there for
  anyone who reads it: **Chios ships mostly its noble grapes and Thasos its common ones**, so a plain
  average flatters the famous name. Repair the naive pipeline into the varietal-balanced regroup — give
  every grape an equal say. *Analysis:* `group_by(region, varietal) |> mean` → ungroup → `group_by(region)
  |> mean` → **Thasos** (Chios falls to last). **Misdirection:** the obvious/tempting answer is Chios (just
  computed at S3, and the merchant's boast); the careful answer is Thasos. *Unlocks:* mints the
  Canvas code; the manifest can now be reconciled honestly.

### Escape payoff (DATA-FREE meta-echo — the recognition move as climax)
**RELOCATED 2026-07-22 (Lucas): the escape is atop the Pharos lighthouse**, reached by the skiff across
the harbour after the Library boss — so the lighthouse's beauty *earns* its place in the story instead of
being walked through. **No keeper — a locked door** (fewer-people principle): the opening already told the
player the second half of the goal (turn the Pharos light onto your ship to leave), so the lantern needs
no character to explain it. At the top: a **locked door**, and beyond it the great lamp on its dial.
**The lock IS the escape puzzle** — lay out the **9 amphora seals** gathered all day (*not* the wine data;
no CSV, no console), read the **queue of three tally-marks** (verb sigil + target value, in order), group
the seals by a visual trait, apply the queued verb, and select on the 3×3 `grid-select` the trait whose
result hits each target. **Payoff — a player-performed ceremonial gesture (NEW 2026-07-22, Lucas):**
solving the lock opens the door and lights the **lamp dial** (reuse the airship's game-state dial widget);
the **player themself turns the beam onto their ship** in the harbour below — cleared to sail on the
turning tide. Keep it a single gesture — **one dial, one target (your ship), one motion** — *not* a second
puzzle (no derived angle). **Why it lands:** the whole day's move — sort into piles, read one number off
each — performed by *you*, unaided; then your own hand swings the light that frees you, at the most
beautiful place in the world. (Verified key `[size, shape, colour]`; full spec + the 9 seals + the result
table are in the escape section above.)

### Voice notes
Earnest, concrete, sensory — sun and dust and sea-glint, clay and stylus and tally-stick; never jokey.
Keep every card **short** (the lean-story mandate): a beat and a reason, not a paragraph. **Cast kept to
one** (fewer-people principle): the port's law, the registers and boards, and the front-loaded goal carry
the story — no officer, keeper or archivist to remember, and only the **S3 merchant** as a single
text-only voice (his boast primes the boss). Keep any human touch text-only and incidental; never a
character the player must track to progress.

### Draft story-map text (paste into the harness story-map, then tighten)
- **title:** `The Manifest`
- **subtitle:** `A wine ship at Alexandria, and a harbour that won't let you leave.`
- **story (landing screen):**
  > The wine ship makes Alexandria at first light, the Pharos still burning gold above the harbour. You
  > came in with the cargo — a hold of amphorae from the Aegean islands — and by the law of the port no
  > ship may leave until two things are done: the cargo **registered** with the city, every amphora grouped
  > by origin and honestly tallied; and the great **Pharos light turned upon it** to clear it for the open
  > sea. The tide turns at dusk. Reconcile the manifest room by room, climb to the lantern, and swing the
  > light onto your ship before the water pulls her out.
- **entry — S1 (ship's deck):**
  > On deck at first light, the first crates stand open beside the count-board, a fresh notch for each
  > amphora tallied. Reds and whites are taxed apart, and the register's first line is the plain one —
  > which does the ship carry more heavily cured for the long voyage across?
- **entry — S2 (market):**
  > Past the dock the wharf opens into the market, all dust and haggling under the midday sun. Here cargo
  > is priced by the grape, the price-board marking the dearest lot highest — so the manifest's value hangs
  > on which varietal pours the most potent wine. Read it off and mark your figure.
- **entry — S3 (market):**
  > Two stalls on, a merchant is loud over his amphorae, swearing his Chian wine is the finest cargo afloat
  > and the tally will bear him out; nearby, a reject-slate strikes the poorest lots to the bottom. Take his
  > boast at face value for now — group the cargo by its island and read which region scores highest as it
  > stands.
- **entry — BOSS (Library):**
  > The dispute climbs the steps to the Great Library, whose ledgers keep the true record of every vintage.
  > The trouble is set down plainly there: Chios ships mostly its noble grapes and Thasos its common ones,
  > so a plain average flatters the famous name. Weigh every grape alike, and see which island truly makes
  > the better wine.
- **entry — ESCAPE (the Pharos lantern):**
  > The skiff sets you at the foot of the lighthouse and you climb — flight after flight — to a locked door
  > at the top, and beyond it the great lamp on its dial, throwing its beam far out to sea. You already know
  > what to do here: reconcile the manifest, and the light is yours to turn. Lay out the seals you gathered
  > all day and sort them by the three tallies, in the order the board demands, before the tide pulls your
  > ship from the harbour.
- **done (analysis complete — Canvas code minted):**
  > The manifest is reconciled. Weigh every grape alike and it is Thasos, not Chios, that gives the truest
  > wine — the correction goes down in the register and the tally is stamped true. Copy the code sealed into
  > the manifest; it is your proof the cargo was judged fairly.
- **escapeDone (escaped):**
  > The last seals fall into their piles, the three tallies match, and the door gives. You set both hands to
  > the dial and turn the great beam down across the water until it finds your ship at her mooring —
  > cleared. The tide has turned and she rides high on it; sails fill, and the Pharos light holds you all
  > the way out of the harbour, the manifest true behind you.

### Judgement calls (flagged)
- **Clock = the tide at dusk**, riding the dock→market→Library light-arc; chosen as the lightest possible
  time pressure that needs no exposition. Design phase owns the actual weather/time progression.
- **Escape relocated to the Pharos lighthouse** (Lucas, 2026-07-22), reached by a skiff across the
  harbour after the boss — so the lighthouse earns its visit and the beacon-clearance becomes the payoff.
  (Supersedes the earlier customs-house bookend.)
- **Verb legend taught by objects, not people** (fewer-people principle): the count-board (`n`)/deck, the
  price-board (`max`)/market, the reject-slate (`min`)/market — all three sigils met across rooms 1–3,
  before the boss, so the escape needs no legend and no character to teach it.
- **Cast reduced to one + a player-performed finale** (Lucas, 2026-07-22): dropped the customs officer,
  beacon-keeper and Library archivist, and taught the three sigils by objects (count-board / price-board /
  reject-slate); front-loaded the two-part goal (register the cargo, then turn the Pharos light onto the
  ship) in the opening so each mechanic reads as an obvious story. **One character kept — the S3 merchant**
  (Lucas, 2026-07-22), reinstated as text-only flavour because his boast makes Chios the *tempting* wrong
  answer for the boss. The lighthouse escape ends in a **ceremonial dial the player turns** (reuse the
  airship game-state dial): the recognition puzzle unlocks the door and the lamp, but the dial is payoff —
  one dial, one target, one motion — never a second puzzle.
- **Kept the ladder exactly** — Chios (shortcut) and Thasos (regroup) preserved; the merchant's boast is
  written to make Chios the *tempting* wrong answer, per the boss-misdirection rule. No pedagogy bent.
- **Placeholder names kept** (Chios/Thasos/Argitis etc. from the data phase) — they're already period-apt,
  so I left them; rename here later if desired, but nothing in the story depends on the exact strings.

## Structure sketch (mirrors trees — 3 stations + regroup boss + organisation escape)

- **Three graded wrangling stations** — one `group_by |> summarise` + plot + answer each, on the wine
  **cargo manifest**. Single-grouping warm-ups on three categorical axes (e.g. `type`, then two
  engineered axes such as region / varietal), echoing the class exercise.
- **Regroup boss** — the **Simpson's-paradox flip** capstone (same shape as forest's zone regroup):
  a naive count-weighted "which region's wine scores highest as shipped?" (the shortcut a prior station
  hands the player) vs the varietal-balanced "which region genuinely makes the best wine, giving every
  varietal an equal say?" — lands on a **different** region. Fairness via precise phrasing + an explicit
  clue flagging the varietal-mix confound (not a hidden gotcha), per trees.
- **Ungraded escape — a DATA-FREE meta-echo of cataloguing (REFRAMED 2026-07-22).** Per the sharpened
  escape principle (`escape_room_puzzles` step 4 / `escape_room_story` beat 4): the escape is a **meta
  version of the technique enacted in the world, with NO connection to the wine dataset** — no CSV, no
  console, none of the data's region/varietal/type/quality. Alexandria is *made* for this: a port, a
  market and a library are all **cataloguing** — literally `group_by`/`summarise` done by hand (sort into
  piles by a shared trait, read one number off each pile). So the escape is the player acting as the
  **cataloguer**, on **in-world props**, not on the cargo data.
  - **Reconciles Lucas's three-collection idea** (wine cargo / market goods / library books): those props
    can still appear — but each is sorted by an **obvious visual trait** (colour / size / shape /
    material), **never by the wine data's variables**. Exactly the forest pattern, where the escape
    collectibles (beetles/cones/shells by colour/size/shape) were decoupled from the tree variables the
    stations analysed. So amphorae may feature — sorted by *amphora shape* or *seal colour*, not by region
    or varietal.
  - **Mechanic — DECIDED 2026-07-22: the ACTIVE sort-and-summarise via the image inventory** (rejected the
    forest-style recognition grid — Lucas doesn't want the escape to repeat a prior scenario's puzzle).
    The player **collects image tiles through the story** (pickup `clue` hotspots carrying an `image`; see
    `AGENTS.md` → *Pick-up (clues)* + *Collected items board*), then at the escape **groups and summarises
    them in various ways** to solve it.
    - **Reuses the existing "Collected items" board** (`#nbBoard` in `pano-player.js`) — a draggable
      snap-grid where tiles drag into cells and stack. That board *is* the grouping surface: the player
      drags the collected images into **piles by a shared visual trait**, exactly `group_by` by hand.
    - **The tiles are in-world props with several visible traits, NONE tied to the wine data** — e.g.
      amphorae / market wares / scrolls each varying in **colour, shape, size** (each a **3-level**
      grouping axis) **plus a stamped NUMERAL** (a merchant's tally mark — an in-world number, so
      `max()`/`min()` have something to act on; still nothing from the wine dataset). **9 tiles** to start.
    - **Legend taught in the stations (REFINED 2026-07-22; RESOLVED in Narrative — objects, not people).**
      Each puzzle room stages one summarise verb via a **register / board** tagged with a **sigil**: the
      deck's **count-board** (`n()`, tally sigil), the market **price-board** marking the **dearest**
      (`max()`, up-chevron), the market **reject-slate** marking the **least** (`min()`, down-chevron). By
      the escape the player has met all three sigil→verb pairings diegetically — no R legend at the door,
      and (per the `## Narrative` fewer-people decision) no character to teach it.
    - **The escape — a symbol QUEUE + a 3×3 selector (REFINED 2026-07-22, supersedes the 3-digit lock).**
      The escape shows a **queue of the three sigils in a set order** (e.g. max, min, n). The player must
      **perform those actions, in that order, on their 9 collected cards** — group the cards, apply the
      queued verb at each step — and enter the three results on a **3×3 grid-select** (the forest's
      `grid-select` widget, reused as the *input*): **3 columns = the 3 queued steps in order; 3 rows =
      candidate result-values**; one selection per column; the correct vector fires `solveRoom`. **No
      lock** — Lucas wants to lean on the selector and cut lock usage. *This is NOT a repeat of the forest
      puzzle:* the forest asked the player to **recognise** which grouping made a display; Egypt asks them
      to **actively perform** queued summarise verbs on cards they collected — only the input widget is
      shared.
    - **Grid layout — RESOLVED 2026-07-22 (Lucas): the grouping variable is the grid's OTHER axis,
      symbol-encoded.** Grid = **columns = the 3 queued steps** (each headed by a **verb sigil** from the
      queue) × **rows = the 3 grouping traits** (colour / shape / size, each a **sigil**). For each step
      the player groups the cards by each trait, applies the step's verb, and **selects the trait whose
      result equals the step's target** shown on the door. One cell per column → the trait-vector is the
      grid-select key. Both axes are symbols; no lock.

    **FULLY PINNED + VERIFIED 2026-07-22** — generator `_scratch/build_escape_cards.py` (asserts a unique
    solution). **Verb semantics** (each = `group_by(trait) |> summarise(...) |> reduce`, so every result is
    grouping-dependent): **`n`** = COUNT of the largest pile; **`max`** = greatest pile TOTAL (sum of the
    stamped numerals); **`min`** = least pile TOTAL.

    - **The 9 cards** (id · colour · shape · size · numeral): 1·Red·Round·Small·1, 2·Red·Round·Medium·2,
      3·Red·Tall·Large·3, 4·Red·Squat·Small·4, 5·Blue·Round·Medium·5, 6·Blue·Round·Large·6,
      7·Blue·Tall·Small·7, 8·Amber·Round·Large·8, 9·Amber·Tall·Medium·9. Marginals: **colour** Red4/Blue3/
      Amber2, **shape** Round5/Tall3/Squat1, **size** Small3/Medium3/Large3.
    - **The 3×3 result table** (rows verb × cols trait) — every verb row has 3 **distinct** values, so a
      target singles out one trait:

      | verb | colour | shape | size |
      |------|:---:|:---:|:---:|
      | `n`   | 4  | 5  | 3  |
      | `max` | 18 | 22 | 17 |
      | `min` | 10 | 4  | 12 |

    - **The queue** (door shows verb sigil + target, in order) → **grid-select key**:
      1. **`max` → 17** ⟹ group by **size** (largest pile total).
      2. **`n` → 5** ⟹ group by **shape** (largest pile of 5).
      3. **`min` → 10** ⟹ group by **colour** (smallest pile total).
      Key = **[size, shape, colour]** — unique; fires `solveRoom`. All three traits and all three verbs
      exercised once.
    - **Engine cost: low.** The collected-items board already does the grouping (drag tiles into piles);
      the **`grid-select`** type is **specced for the forest** (build once, share — both scenarios are
      `rooms_built: 0`, so it may still need standing up). New work is mostly **content**: the 9 tile
      images + the three station **board + sigil** beats + the door queue.
    - **Pickup requirement:** all 9 cards must be collected before the escape — make them mandatory / auto
      (see pickup-reliability flag above).
  - **Pickup reliability (flag).** Image pickups are **opt-in** ("Add to notebook"), so the escape is only
    solvable if the needed tiles were collected. Forest sidestepped this by making collections non-pickup;
    here pickups are the point — so ensure the required tiles are **reliably collected** (mandatory/auto
    pickup, or strong cueing + backtracking). Resolve before build.
  - **Open — echo the boss's regroup?** The baseline echoes general `group_by/summarise`. Whether the
    escape should also echo the *boss's* specific move (don't trust the raw count-weighted pile; give each
    subgroup equal weight) is a stretch goal — likely too subtle for a wordless meta puzzle; note and
    defer.

## Verified puzzle slate + dataset (BUILT + VERIFIED 2026-07-22, session Egypt)

Generator: `_scratch/build_wine_cargo.py` (deterministic, seed 20260722; script-relative output path, so
re-runnable from any CWD) → **`data/wine_cargo.csv`** (4,000 rows, 13 cols). Realistic wine skeleton
(red/white chemistry as distractor columns) + engineered cargo axes and effect model. **Public URL once
the site is pushed from the Mac:** `https://thebustalab.github.io/escape_rooms/rooms/wrangling/egypt/data/wine_cargo.csv`
(alt: move to `phylochemistry/sample_data/`, as with other scenario datasets). **Student-facing columns:** `amphora_id, type, region, varietal, vintage,
fixed_acidity, volatile_acidity, residual_sugar, chlorides, pH, sulphates, alcohol, quality_score`.

**Category re-skin (Alexandria cargo).** `region` = four famous ancient Aegean wine islands
**Chios / Rhodes / Kos / Thasos** (~1,000 amphorae each). `varietal` = six ancient-style grape names
**Aminean / Apian / Eugenia / Argitis / Duracina / Helvola** (premium = Aminean/Apian/Eugenia).
`vintage` = three Ptolemaic-era years (a pure **distractor** axis — grouping by it moves nothing).
`type` = red/white (~40/60). All names are placeholders the `escape_room_story` phase can rename.

**Effect model (what drives what):**
- `sulphates` ← **type** only (red 0.66 / white 0.49 + noise). → S1 winner **red**.
- `alcohol` ← **varietal** only. → S2 winner **Argitis**.
- `quality_score` ← **region "true ground" lift + varietal premium lift**, with an engineered **per-region
  varietal MIX SKEW** (Chios packed ~90% premium grapes; Thasos packed ~90% common) → the flip.
- other chemistry columns (`fixed/volatile_acidity, residual_sugar, chlorides, pH`) are realistic
  type-driven **distractors** — `str()` shows more than any puzzle needs, so the student must pick the
  right column (mirrors the forest `crown_height_m` decoy).

**The engineered flip (the teaching point).** `Thasos` is genuinely the best ground *per varietal* (wins
the balanced regroup), but `Chios` is packed with the premium grapes, so its **raw count-weighted** mean
is inflated and it wins the naive shortcut. Shortcut → **Chios**, regroup → **Thasos** — a real two-way
flip. Nice narrative echo: the prestige-name cargo (Chios) only *looks* best; the humble Thasian is the
truly better wine.

**VERIFIED answers (re-run the generator to reconfirm; deterministic):**
- **S1 — single grouping (type).** `group_by(type) |> summarise(mean(sulphates))` → **red** (0.661 vs
  0.489, **+35.1%**). *Which wine type is more heavily sulphured?* — literally the class exercise. + plot.
- **S2 — single grouping (varietal).** `group_by(varietal) |> summarise(mean(alcohol))` → **Argitis**
  (13.79, **+12.1%** over Aminean). *Which grape yields the strongest wine?* — 6 levels, harder read.
  + plot.
- **S3 (SHORTCUT) — single grouping (region).** `group_by(region) |> summarise(mean(quality_score))`,
  phrased *"which region's cargo is finest as it stands?"* → **Chios** (7.28, **+7.4%** over Kos). Hands
  the player the naive count-weighted answer. + plot.
- **BOSS (REGROUP).** `group_by(region, varietal) |> summarise(m = mean(quality_score))`, **ungroup**,
  `group_by(region) |> summarise(mean(m))`, phrased *"which region makes the best wine giving every grape
  an equal say?"* → **Thasos** (7.43, **+8.7%** over Kos; Chios falls to last, 6.27). **Different region
  than S3** — the flip fires. Mints the Canvas code; the varietal-balanced bar chart is the codec-
  watermarked deliverable.

**Escalation (strictly monotonic):** 2-level warm-up (type) → 6-level read (varietal) → the count-
weighted region shortcut → the two-stage region×varietal regroup. Each rung adds one move; no plateau.

**Fairness (per the pair principle):** the boss wording explicitly asks the equal-weighting question and
the boss clue calls out the varietal-mix confound (regions differ wildly in which grapes they ship, so a
raw average misleads). A student who reuses S3's method gets Chios and is *meant* to notice it can't be
right — that recognition is the lesson, not a hidden trap.

**Distractor availability (for the wiring phase):** region/type groupings have <6 levels, so MCQ
distractors come from **wrong-method** answers (global mean, wrong grouping column, count-instead-of-mean,
grouped-by-vintage → no difference, the shortcut answer at the boss) + the other regions. Varietal has
exactly 6. Recompute exact distractor values in `escape_room_wiring`.

**Judgement calls flagged for Lucas:**
- **Fully engineered, not real rows.** Like `forest_census`, `wine_cargo.csv` is generated from an
  effect model — it is *not* the real UCI `wine_quality` rows. It keeps the real red/white sulphates
  relationship (the class exercise) but region/varietal/vintage and the quality flip are constructed.
- **Names are placeholders** — the ancient island/grape names are first-draft; `escape_room_story` owns
  final naming and the prestige-Chios-vs-humble-Thasos story beat.

## Puzzle-type variety across the rooms (DECIDED 2026-07-22 — boss = Repair confirmed by Lucas)

The verified ladder above pins the *analyses*; this pins the *format* each room uses, drawing on the
console puzzle **types** (`../../../notes/puzzle_types_design_notes.md`) so the four graded rooms aren't
four identical Compute-the-Key cards. Slate — **four distinct mechanics across the scenario**:

- **S1 (type → sulphates → red) — Type 1 Compute-the-Key.** The backbone warm-up: write the
  `group_by |> summarise`, assign, Check. Simplest rung, simplest format.
- **S2 (varietal → alcohol → Argitis) — Type 4 Pick-the-Point** *(the new type)*. Plot mean alcohol per
  varietal and **click the winning grape on the live `ggiraph` plot** — forces plot-reading (6 grapes is
  too many to eyeball as a table), and the click maps back to the row via `data-id`.
- **S3 (region → quality → Chios, the SHORTCUT) — Type 1 Compute-the-Key.** Keep it a console compute so
  the count-weighted shortcut is *felt in code* (sets the trap the boss springs). Straightforward rung.
- **BOSS (regroup → Thasos) — Type 3 Repair-the-Pipeline.** The regroup's **canonical mistake IS the
  shortcut**, so this type fits perfectly: hand the student the naive `group_by(region) |> summarise(mean)`
  (which returns **Chios**, the wrong-here answer they just computed at S3) and make them **fix it into the
  varietal-balanced regroup** (group by region×varietal, summarise, ungroup, regroup by region) → **Thasos**.
  Repairing the broken pipeline *is* the lesson; the error teaches. Mints the Canvas code.
- **ESCAPE — the symbol-queue + 3×3 `grid-select`** (data-free, above). A fifth, distinct mechanic.

So the scenario spans **Compute-the-Key · Pick-the-Point · Compute-the-Key · Repair-the-Pipeline ·
grid-select** — three graded types + the escape (only the two plain computes repeat, at different rungs).

**Dependency / coordination:** **Type 4 Pick-the-Point is being built now (another agent, 2026-07-22)** —
its `ggiraph`-in-WebR feasibility is verified but the engine wiring (pull the SVG into the modal,
`data-id` click + feedback ladder, codec decision) is **NOT yet built**. So S2 as Pick-the-Point is
**gated on that landing**; fall back to Type 1 (compute, or an MCQ on the winning grape) if it isn't ready
at build time. Likewise `grid-select` (escape) is still to be stood up. Neither blocks the story phase.

**Alternatives considered:** boss as **Type 4 Pick-the-Point** (show the balanced bar chart, pick Thasos,
subverting the primed Chios decoy — the exact alaska-boss pattern) is also strong; chose **Repair** so the
boss adds a *third* graded type and because fixing the naive→balanced pipeline is the sharpest possible
framing of the Simpson lesson. Type 2 Classify-the-Unknown was left out — wrangling has no natural
mystery-sample without contrivance.

## Ambience & music

**Music: Glass Beams — "Mahal EP" (full live performance)** — `https://youtu.be/hGQu4_fan8Q`. Hypnotic,
masked-psychedelia groove; warm, hypnotic, faintly Eastern — a lovely fit for a torchlit market /
harbour bazaar. On build: fire a `youtube_audio` observer row (clip + fade into
`mobile_assistant/hold_music/…` or scenario-local), then set `music` / `musicVolume` / `musicCredit`.
Candidate `ambient` / `fx`: dust motes and heat-shimmer in the market, harbour glints and gull cries at
the dock, torch-flicker and drifting dust in the library; per-room SFX = harbour bustle → market
crowd/haggling → hushed library.

## Open design questions

- ~~**Story payoff** (customs-clear vs Library-burns vs admission).~~ RESOLVED 2026-07-22: **clear
  customs** (Lucas). Full narrative in the `## Narrative` section.
- **Aesthetic** — pharaonic Egypt vs Hellenistic Alexandria (see world section). Affects art + which
  venues are honest.
- **Escape mechanic** — reuse `grid-select`, or build the diegetic shelving/sorting puzzle.
- ~~**Dataset engineering.**~~ RESOLVED 2026-07-22: engineered `data/wine_cargo.csv` built + all four
  answers verified single-winner + the flip asserted (see Verified puzzle slate). `type`→sulphates kept
  as the class-exercise warm-up.
- **Three distinct grouping axes** — like forest, the three station axes (and the three catalogued
  collections) must be visually + conceptually separable so each grouping is unmistakable.
- **Pair integrity** — keep it a genuine twin of `trees`, not a re-skin: same `group_by`/`summarise`
  skill + regroup boss, different world + data + escape flavour.

## How it maps to established vocabulary

- **Pre/post pair** (`../../../notes/puzzle_inventory.md` chapter principle): the second `wrangling`
  scenario, same question style as `trees` on `wine_quality` + an Egyptian story.
- **Two-objective structure** (`../../../notes/two_phase_escape_design_notes.md`): stations + regroup
  boss = graded, codec-minted `group_by`/`summarise` in the console; the organisation puzzle = the
  ungraded, no-instructions escape.
- **Escape = a DATA-FREE meta-echo** (`escape_room_puzzles` step 4): stations group-and-summarise *with*
  labels + code on the cargo data; the escape re-poses that *cognitive move* on **in-world props with no
  link to the dataset** — cataloguing by a shared visual trait. Transfer by analogy, not repetition
  (exactly the forest grid's move, re-themed as Alexandrian cataloguing).
- **Mechanic:** reuse the `grid-select` type (relatives: pattern-match lock #6, inference board #11,
  deduction ledger #9) or a new shelving/sorting variant.
