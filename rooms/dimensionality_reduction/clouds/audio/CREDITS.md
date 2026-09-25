# clouds — audio

## Sourced for this world

Both CC0 (public domain), verified on the source page before pulling, per the sound_pull rule that a
pull can fetch the wrong recording and the file's own measurements will not tell you.

| file | role | source | licence |
|---|---|---|---|
| `storm_bed_wind.mp3` | the storm bed, every ring room | freesound 405601, *Howling Wind Ambience*, DBlover (1:25) | Creative Commons 0 |
| `storm_bed_rumble_loop.mp3` | continuous rumble bed, every ring room | freesound 486558, *thunder.rumble.loop*, xUMR (0:04, a looping variant) | Creative Commons 0 |
| `storm_wind_drone.mp3` | spare layer, not wired | freesound 719251, *wind drone effect*, cbrews (1:01) | Creative Commons 0 |
| ~~`storm_bed_thunder_rain.mp3`~~ | RETIRED 2026-09-25 — Lucas: "instead of rain we just need thunder and wind. No rain." Kept on disk in case a rain state is ever wanted | freesound 376810, Alex_hears_things | Creative Commons 0 |
| `storm_thunder_distant.mp3` | interval layer — a distant roll every so often | freesound 581124, *Distant Thunder 3*, Fission9 (0:08) | Creative Commons 0 |

Lucas, 2026-09-25: "massive thunderstorms and rain and all the same in all rooms minus the eye" — so
every ring room carries the SAME bed, and only the volumes differ (the in-cloud rooms sit louder and
closer). The Eye is deliberately silent here; it is the centre of the storm and wants its own sound.

## The theme

| file | role | source | licence |
|---|---|---|---|
| `clouds_theme.mp3` | the scenario's looping music (`scenario.json` → `music`, volume 0.15) | Pierre's Generative Music, *3 Hours of Generative Ambient for Deep Focus · Modular Synth & Tape* | see `musicCredit` in `scenario.json` |

**TRIMMED 2026-09-25 to the house shape: the first 30:00, 128 kbps, 48 kHz stereo, 5-second fades in
and out — 28.8 MB.** The source is a THREE-HOUR video and it was pulled whole: 3:00:00 at 192 kbps,
**259 MB**, no fades. That is nine times every other theme in the corpus (they are all ~1800 s / 128 kbps
/ ~28-29 MB) and it is over GitHub's 100 MB hard limit, so `githooks/pre-push` blocked the entire
`escape_rooms` push — which is what surfaced it, not anything anyone noticed by ear.

The fades matter because the player sets `music.loop = true` (`shared/pano-player.js`): the source runs
at full level at both ends, so a bare 30-minute cut would click audibly on every loop. `beacons_theme.mp3`
is the reference — it fades both ends for the same reason.

**The untouched 3-hour original is kept at `../_scratch/audio/clouds_theme_full.mp3`** (`_scratch/` is
gitignored, so it stays on disk and on both machines via Syncthing without ever reaching the public
repo). To take a DIFFERENT 30 minutes instead of the opening — this was the default choice, not a
musical judgement — re-cut from it:

    cd rooms/dimensionality_reduction/clouds
    ffmpeg -ss <START_SECONDS> -t 1800 -i _scratch/audio/clouds_theme_full.mp3 \
      -af "afade=t=in:st=0:d=5,afade=t=out:st=1795:d=5" \
      -c:a libmp3lame -b:a 128k -ar 48000 -ac 2 audio/clouds_theme.mp3

## Stand-ins (to delete once the above are wired and checked)

`STANDIN_storm_wind_*.mp3` were borrowed from `networks/beacons` for the 2026-09-24 test play. They are
NOT authored for this world and beacons' own credits apply while they remain.
