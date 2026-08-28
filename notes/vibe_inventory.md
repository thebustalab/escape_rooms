---
authority: intent
---

# Escape-room vibe inventory — light, palette, mood

A living catalogue of **what each scenario LOOKS AND FEELS LIKE** — key, palette, light sources,
weather band, signature material, and what a cinemagraph has to work with. Fifth sibling of
`puzzle_inventory.md` (what you solve), `candidate_locations.md` (where you are),
`scenario_theme_ideas.md` (the premise) and `travel_mechanic_inventory.md` (how you move).
Started **2026-08-12** (Lucas, session "Subway"), because vibe had been decided per-scenario and
never compared across them — and a comparison turns out to matter (see the finding below).

**Where the axes came from.** Not invented: each one is something that has actually cost time or
broken a mechanic. *Key* decides whether an unlit thing reads as significant. *Reserved colours*
is the one that bit `networks/subway`. *Motion budget* is why `trees` needed 114 clips and a
clinical scenario would need almost none.

**How the built rows were filled, and their limits.** By harvesting `scenario.json`: the `music`,
`musicVolume`, `ambient` and overlay flags are **read directly and are exact**; the palette and
light columns are derived from a **keyword scan of the `authoring.scenePrompt` text**, which is a
proxy, not a reading. Treat those two columns as a **first pass to be corrected by eye**, and fix
a row when you next work in that scenario rather than trusting it blind.

---

## ⚠️ The finding: the corpus has converged on ONE palette

Across 12 scenarios' scene prompts:

- **amber** appears in **10 of 12**
- **brass** in **10 of 12**
- **teal** in **8 of 12**
- the light band is **dusk / night / dawn in 10 of 12** — only `hospital` and `clouds` are daylight

That is the house reference (dusk, teal-and-amber, painterly) applied faithfully — and the result
is that scenarios are drifting towards looking like each other. `candidate_locations.md` guards
against two scenarios sharing a *place*; nothing has been guarding against them sharing a *look*.

**So the useful question for a new scenario is not "what would look nice", it is "what register is
still free".** See *Registers not yet used* at the foot.

---

## Built and drafted scenarios

| Scenario | Key | Time / weather band | Palette (proxy — verify) | Signature material | Ambient | Music (vol) | Motion budget |
|---|---|---|---|---|---|---|---|
| `data_vis/alaska` — *Signal in the Cold* | low | night, evening, haze, snow | cold blues + cobalt + emerald, amber lamps, brass | snow, field-station metal | `snow` | `arnalds_hafursey` (0.10) | high — falling snow, haze |
| `data_vis/hawaii` — *Saltwater Intrusion* | low | dusk, night, mist, gloom | green + teal, amber, brass, black | wet jungle, volcanic rock | `fireflies` | `forestal_tape` (0.25) | high — mist, insects, water |
| `data_vis2/hospital` — *Vital Signs* | **high** | **afternoon, sunlight, daylight** | blue/green/grey, warm gold | clean interior surfaces | `leaves` | `milk_tea` (0.10) | **low** — the outlier, and the only bright scenario |
| `data_vis2/airship` — *The Alembic* | low | night, starlight, haze, gloom | brass + copper + verdigris, amber, red | brass and canvas | `embers` | `kora_passage` (0.18) | high — embers, roll (`heel`), `sickness` vignette |
| `wrangling/trees` — *The Collector's Vault* | mid | midday→sunset, mist, haze | amber + gold + teal + rose, brass | alien canopy, monorail steel | `fireflies` | `in_the_sun` (0.15) | **very high** — 114 clips; the expensive end |
| `wrangling/egypt` — *The Manifest* | mid | **the widest band in the corpus** — dawn, midday, dusk, night, moonlight | gold + bronze + brass, violet, rose, slate | stone, sea, papyrus | `embers` | `glass_beams_mahal` (0.15) | high |
| `comparing_means/spa` — *First Guest* | low | pre-dawn → sunrise, snow | verdigris + copper + brass, rose, teal | thermal water, tile, brass | `snow` | — | high — steam, water, snow |
| `comparing_means/squirrel` — *Seedfall* | mid | late autumn → first snow | amber + gold + red + orange | real deciduous wood | `leaves` | — | high — falling leaves |
| `dimensionality_reduction/henges` — *The Portal Henges* | low | pre-dawn, night, starlight, mist | black + blue + white, gold, cold | standing stone | `fireflies` | `drowned_henges_theme` (0.19) | mid — starfield, mist |
| `dimensionality_reduction/clouds` — *Where the City Opens* | mid | afternoon, haze | gold + slate + blue, amber, brass | cloud, city stone | custom sun-motes | — | mid |
| `flat_clustering/waterfalls` — *Where the Waters Divide* | low | dusk, mist, gloom | teal + verdigris + rust, amber, brass | falling water, wet rock | `none` | — | high — water |
| `hierarchical_clustering/canyon` — *The Confluence* | mid | (haze; band not yet set) | ochre + red + slate + amber, teal | red rock | `none` | — | high — flood, dust |
| **`hierarchical_clustering/temple` — *The Register of the Gods*** | **high** | **harsh overhead NOON**; the shafts going from slanted to vertical **are the clock**. Exactly ONE dark room (the sealed cell), deliberately | **near-monochrome green-grey**: wet stone, dark foliage, pale root, bleached white sun. **The only saturated colour in frame is the nine banners** | root-cracked jungle masonry, carved votive figures | `rays` (**first claim**) | tbd | mid — spore in shafts, hanging roots, water |
| **`networks/beacons`** *(design notes only)* | **high — deliberately** | **daylight + moving weather**; storm, cloud, fog. **At most ONE night scene** | **grey-white, high-key**: rock, cloud, smoke. Fire demoted to a rare pinprick, not the ambient wash | mountain rock, timber posts, iron braziers, ledgers | weather — **one state change** via the edit endpoint (base + 1 edit; capped at one) | tbd | high — smoke, cloud, rain, moving weather |
| **`networks/subway` — *The Faintest Line*** | **low** | underground; no sky, no weather — a **tide** clock in text | **neutral ground, deliberately**: sooted brick, wet black tile, charcoal; cold blue-green damp vs warm lamp amber | Victorian tile + brass **shell**, contemporary works kit inside it (plastic, gaffer tape, work lamps) | (tbd — dust → damp haze) | **five tracks, one per rail line** — diegetic, the driver's own; genres deliberately unlike each other (metal / jazz / dub / …). Needs `room.music` (spec'd, not built) | high — steam, drips, lamp flicker, tunnel motion |

## Reserved colours — the axis nothing else records

Colours a scenario's **data, signage or answer-carrying artwork** has already spent, which the
world therefore must not compete with. This is a legibility constraint, not taste: get it wrong
and a mechanic quietly stops working.

| Scenario | Reserved | Why |
|---|---|---|
| `networks/subway` | **`#c1443f` madder, `#3f63b8` woad, `#d8b23c` weld, `#35a08a` verdigris, `#9aa0a6` lampblack** | The five line colours. The player learns them in the tunnels and plots them on the carried map — the world's red and the map's red must be one red. **This is why subway cannot use the house teal-and-amber: teal ≈ verdigris, amber ≈ weld.** |
| `data_vis2/hospital` | the facet-collage postcards + the pH×Ca map-pick plot | not audited — check before re-lighting |
| `dimensionality_reduction/henges` | the PCA pick plot | not audited |
| **`modeling/canal`** | **the gauge-board face, the bridge-plate numerals, and the hull's draught line** | The escape is read entirely off these three marks, and the scenario is deliberately **wordless** — so they are the only high-contrast objects allowed in frame. Same functional pattern as `temple`'s nine banners: desaturate everything else so the answer-carrying marks read at a glance. The draught line in particular must be the one crisp horizontal in a world of wet, soft, muddy edges. |
| **`hierarchical_clustering/temple`** | **crimson, white, orange, deep blue, black, magenta, yellow, violet, turquoise** — the nine banners | They are the **ledger escape's row identifiers**, and the art cannot write names, so the banner colour is the only way a player maps a niche they saw to a row they fill. The world is deliberately desaturated so all nine read at a glance. `sea-green` and `silver` were dropped in the re-skin: one vanishes into green stone, the other has too little chroma to carry a row. **Nothing in this world may compete with a saturated hue.** |
| others | — | **not yet audited.** Worth filling in as each is next touched. |

## Registers not yet used

Free ground, given the concentration above:

- ~~**High-key daylight.**~~ **CLAIMED by `networks/beacons`** (2026-08-12). Only `hospital` was
  bright; beacons takes daylight deliberately, as the answer to the amber-at-night trap.
- ~~**Clinical / white / scrubbed.**~~ **CLAIMED by the period-city heist** → `flat_clustering`
  scenario 2 (2026-08-27, Lucas, session "Canal boat"). Nothing else in the corpus is clean — and
  nothing else is **urban** or **modern** either, which the heist claims at the same time. A gallery
  or a vault interior is exactly this register. (Original note: considered and rejected for subway —
  a high-key world makes an unlit ghost platform a black hole that gives itself away. That objection
  is specific to a hidden-in-the-dark escape and does not apply to the heist.) Theme-stage
  designation, no build yet — draft in `scenario_theme_ideas.md`.
- ~~**Flat overcast daylight — low cloud, no sun at all.**~~ **CLAIMED by `modeling/canal`**
  (2026-08-27). The corpus light band is **dusk/night/dawn in 10 of 12**; the daylight exceptions are
  `hospital` (bright interior), `clouds` (hazy gold), `beacons` (high-key + storm) and `temple` (harsh
  overhead noon). **Nobody has plain low flat cloud** — even, sunless, shadowless, the light of an
  English afternoon that never quite commits. It is the correct light for a canal in decline, and it is
  functionally useful too: **no sun means no shadow clock**, which matters because this scenario has
  spent its one per-scene edit on lock-full/lock-empty and therefore **cannot carry a time arc**.
- ~~**A palette with no amber, no brass and no teal.**~~ **CLAIMED by `modeling/canal`** (2026-08-27) —
  and it is the first scenario to refuse all three of the house colours at once (amber appears in 10 of
  12, brass in 10 of 12, teal in 8 of 12). Instead: **wet grey stone, black-tarred lock beams, rust,
  sodden green meadow, elder and cow parsley, red brick gone brown.** The register is *working country*,
  not wilderness — hedges, gates, a field that someone still cuts.
- **NOT Victorian industrial** — `networks/subway` holds that (brick, glazed tile, underground). The
  canal is **outdoor, rural and pre-industrial in build**; see the period note in
  `rooms/modeling/canal/notes.md`. Two scenarios can share a century without sharing a look, but the
  separation has to be stated: subway is a **works interior**, canal is **weather and field**.

- **Check this file before settling a new scenario's look**, the same way you check
  `candidate_locations.md` before settling its place.
