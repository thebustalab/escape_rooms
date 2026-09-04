# Canyon — audio credits

All sound effects below are **CC0 (public domain)**, sourced from freesound.org via the `sound_pull`
observer. CC0 only: these ship on the public GitHub Pages site (see `Utilities/sound_pull/AGENTS.md`
→ *Licensing*). Full source URLs are in `_scratch/audio/CREDITS.md`.

The **music** (`canyon_confluence_theme.mp3`) is NOT CC0 — it is a YouTube upload, credited in
`scenario.json` → `musicCredit` and shown to the player as a link on the music chip.

## Room ambience (all layers `loop`)

| file | freesound source | uploader | licence | used in |
|------|------------------|----------|---------|---------|
| `canyon_cave_hall.mp3`     | https://freesound.org/people/fonografico/sounds/636105/   | fonografico   | CC0 | undercroft, works, j_c7 — enclosed stone-hall tone |
| `canyon_waterfall.mp3`     | https://freesound.org/people/kwahmah_02/sounds/274259/    | kwahmah_02    | CC0 | j_c1 only — a thin bright spring fall, all spray and no bottom (0.1% of its energy below 200 Hz), which is right high in the canyon and wrong at the trunk |
| `canyon_deepfall.mp3`      | https://freesound.org/people/KevinT1001/sounds/379905/    | KevinT1001    | CC0 | j_c7 + works — the deep bed where every water has arrived. 71% of its energy below 200 Hz against the other fall's 0.1%; Lucas asked for "more low frequencies" and the two recordings differ by ~30 dB in that band |
| `canyon_stream_gentle.mp3` | https://freesound.org/people/BurghRecords/sounds/446019/  | BurghRecords  | CC0 | j_c2, j_c3, j_c4, j_c5, j_c6, j_c7 — running water bed |
| `canyon_slot_wind.mp3`     | https://freesound.org/people/dhallcomposer/sounds/697217/ | dhallcomposer | CC0 | j_c1–j_c4, j_c6 — thin wind down the open slot |
| `canyon_drip_cave.mp3`     | https://freesound.org/people/Sclolex/sounds/177958/       | Sclolex       | CC0 | undercroft, j_c5 — sparse drips over a bed |

## Levels

Each file was **gain-matched on materialisation** so the mixer's volume numbers are comparable across
rooms: the four continuous beds sit at about −26 dBFS mean, and the sparse drip recording is set by its
PEAK (−6 dBFS) because its mean is near-silence and means nothing. Raw `_scratch` levels spanned
−11 to −48 dBFS mean; a flat volume across them would have made the cave hall dominate and the wind
inaudible. Gains applied: cave_hall −14.6, waterfall −3.5, stream_gentle +5.4 (capped to avoid
clipping), slot_wind +8.1, drip_cave +2.7 dB.

## Shape decides role

`canyon_drip_cave.mp3` measures 38.9 dB between its quiet and loud windows — sparse transients in
near-silence, not a bed. It is therefore always layered **over** a continuous bed and never used alone:
a room whose only layer is a sparse recording has no room tone under it, which is the documented
shape/slot mismatch (`Utilities/sound_pull/AGENTS.md`). The other four measure 2–8 dB and are true beds.

It also loops rather than firing on an `interval`: the recording is 90 s, and an interval gap of 10–30 s
would overlap it with itself. `interval` is for a SHORT one-shot.

## Pending

- `canyon_bed_stream_deep_1.mp3` — a second, distinct CC0 stream
  (https://freesound.org/people/jackthemurray/sounds/433589/, CC0, 69 s, pure water, no birds or
  insects) pulled for **j_c7**, whose trunk channel is deep and smooth rather than babbling. Until it
  lands, j_c7 uses the shared `canyon_stream_gentle.mp3`.

## Solve stings (one per graded gate)

| file | freesound source | uploader | licence | fires on |
|------|------------------|----------|---------|----------|
| `solve_stone_slot.mp3`   | https://freesound.org/people/PostProdDog/sounds/578490/   | PostProdDog   | CC0 | j_c1, j_c2, j_c4 — the stone slot grinds open (same-type gates share a sting) |
| `solve_storm_breaks.mp3` | https://freesound.org/people/bastipictures/sounds/243782/ | bastipictures | CC0 | j_c7, the boss — solving it is what brings the storm |
| `solve_sluice.mp3`       | https://freesound.org/people/rivernile7/sounds/380363/    | rivernile7    | CC0 | works — the lock releases and the sluice runs |

Each was trimmed to its own event and loudness-normalised to **I=-18 LUFS / TP=-1.5 dBTP**, then capped
against the music by `auto_balance.py` (reduce-only). Two Attribution-licensed candidates were rejected
on the way — [FairSonicStudio 744947](https://freesound.org/people/FairSonicStudio/sounds/744947/) and
[jorickhoofd 160048](https://freesound.org/people/jorickhoofd/sounds/160048/) — because this ships on the
public site and the standing rule is CC0 only.

**Temple's stone solve stings were deliberately NOT reused** even though canyon is its sibling: two of
them are wired at `volume 0.0` (silent) and two run 9-28 s, which is a bed, not a sting. Worth fixing in
temple; not worth importing here.
