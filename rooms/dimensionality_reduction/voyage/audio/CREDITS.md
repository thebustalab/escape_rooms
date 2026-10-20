# voyage — audio

## Music

`forestal_tape.mp3`: copied from `data_vis/hawaii/audio/` (Lucas, 2026-10-20: reuse Hawaii's music).
"Las Luces Primeras" by Forestal Tape, https://www.youtube.com/watch?v=OJUorlL1nIc (same credit as hawaii).

## Room sound (sourced 2026-10-20)

All CC0 (Creative Commons 0), licence checked on each sound's freesound page; title and tags read before
wiring. Pulled whole through the `sound_pull` observer into `_scratch/audio/<name>_full.mp3`
(spec: `_scratch/audio/pull_spec.json`), then cut with `ffmpeg -ss <start> -t <len> -i` (seek before
input), 128k. Beds: 1 s fade in, 2 s fade out. One-shots: no fade in, 0.15 s tail fade.

| file | room / role | source | uploader | cut from the full pull |
|---|---|---|---|---|
| `beach_bed_surf.mp3` | beach, bed: surf on the beach (tags: hawaii, maui, beach, shore) | [freesound 376872](https://freesound.org/people/deepseapro/sounds/376872/) *Ocean Waves on Beach* (12:20) | deepseapro | 530–550 s (steady mid-file stretch, near the median level) |
| `beach_bed_pennant.mp3` | beach, bed (HERO, the masthead pennant): a flag flapping in the wind | [freesound 154794](https://freesound.org/people/felix.blume/sounds/154794/) *A flag flapping in the wind, at the small village of Assem Souk, in the High Atlas* (1:00) | felix.blume | 26.5–41.5 s |
| `beach_shot_seabirds.mp3` | beach, interval: distant seabird calls over waves (quiet) | [freesound 587956](https://freesound.org/people/dankri2/sounds/587956/) *Seabirds* (0:51) | dankri2 | 20.5–26.5 s (two calls) |
| `well_bed_grove_wind.mp3` | well, bed: wind in trees with the beach beyond | [freesound 502774](https://freesound.org/people/bolkmar/sounds/502774/) *Windy landscape (beach + trees + wind)* (0:42) | bolkmar | 24–39 s |
| `well_shot_gourd_knock.mp3` | well, interval (HERO, the gourds on their cords): one hollow coconut-shell knock | [freesound 157541](https://freesound.org/people/husky70/sounds/157541/) *Coconut Pop* (0:06) | husky70 | 0.9–2.33 s (first knock) |
| `stream_bed_brook.mp3` | stream, bed: a gentle babbling stream | [freesound 446019](https://freesound.org/people/BurghRecords/sounds/446019/) *Gentle Stream Natural Stream Sound* (1:03) | BurghRecords | 37–52 s |
| `stream_bed_oven_crackle.mp3` | stream, low bed (HERO, the smoking earth oven): fire crackle (some crickets in the source) | [freesound 204348](https://freesound.org/people/Sauron974/sounds/204348/) *Crackling Fire* (1:35) | Sauron974 | 69.5–84.5 s |
| `spring_bed_falls_roar.mp3` | spring, bed (HERO, the waterfall): deep waterfall roar | [freesound 379905](https://freesound.org/people/KevinT1001/sounds/379905/) *NIAGARA WATERS ROARING* (0:27) | KevinT1001 | 1–16 s |
| `spring_bed_falls_splash.mp3` | spring, second bed: a mid-sized waterfall's splash | [freesound 352903](https://freesound.org/people/ProductionNow/sounds/352903/) *Mid-sized Waterfall* (0:11) | ProductionNow | 1–10.5 s (short source, so crossfade ≤ 4 s) |

Pulled but not wired (alternates, all CC0, full pulls kept in `_scratch/audio/`):
`beach_bed_surf_alt_full` ([450755](https://freesound.org/people/florianreichelt/sounds/450755/) *Waves of Hawaii*, florianreichelt),
`well_bed_leaves_alt_full` ([669113](https://freesound.org/people/kvgarlic/sounds/669113/) *LateSummer quiet woods and Leaves and Wind*, kvgarlic),
`well_shot_wood_knock_alt_full` ([578136](https://freesound.org/people/ATG65/sounds/578136/) *Knocking wood*, ATG65),
`stream_bed_brook_alt_full` ([415053](https://freesound.org/people/straget/sounds/415053/) *Brook 2*, straget).

No solve or deliver stings: the engine's `station` and `deliver` hotspots (`shared/pano-player.js`
`openStation` / `deliverLoad`) play no `solveSfx`.
