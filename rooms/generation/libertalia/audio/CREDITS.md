# Libertalia — audio credits

## Music (`libertalia_theme.mp3`)

**NOT CC0.** A YouTube upload, used under the standing licence stance for scenario music
(**non-commercial educational** course tool, **credited in-room** with a link back to the source —
Lucas's call, 2026-07-16, recorded in `data_vis/hawaii/AGENTS.md`). Credited to the player as a link
on the music chip via `scenario.json` → `musicCredit`; `pano-player.js` renders the chip and degrades
gracefully if the file is missing.

| field | value |
|---|---|
| source | https://www.youtube.com/watch?v=RDdH9f9SGDY |
| title | *The Movement Of Waves — 1 hour handpan music* |
| artist | Malte Marten |
| source length | 1:01:18 |
| `musicVolume` | `0.15` — the de facto corpus norm (9 of 14 scenarios with music) |

**Provenance: a human performance, not AI — CONFIRMED by Lucas, 2026-09-29.** An agent cannot verify
this from the page (YouTube renders in JavaScript); the agent's read was that the uploader's own
description refers to his September concert tour, an online course in progress and a team — the
signature of a working handpan musician, not a synthetic-audio channel. Lucas confirmed it directly.
No further check is owed before the site is pushed.

**Trimmed to the house shape on materialisation: the first 30:00, 128 kbps, 48 kHz stereo, 2 s fade in
and 5 s fade out** (`youtube_audio` observer row, 2026-09-29). The fades are load-bearing: the player
sets `music.loop = true` (`shared/pano-player.js`), so a bare cut running at full level at both ends
clicks audibly on every pass. `networks/beacons/audio/beacons_theme.mp3` is the reference shape.

**Never commit the raw source.** The untouched 1-hour original is kept at
`../_scratch/audio/libertalia_theme_full.mp3` — `_scratch/` is gitignored
(`escape_rooms/**/_scratch/`), so it stays on disk and on both machines via Syncthing without ever
reaching the public repo. A whole untrimmed 3-hour pull once went in at 259 MB and blocked the entire
`escape_rooms` push (see `dimensionality_reduction/clouds/audio/CREDITS.md`).

To take a DIFFERENT 30 minutes instead of the opening — which was the default choice, not a musical
judgement — re-cut from the original, not from the shipped clip:

    cd rooms/generation/libertalia
    ffmpeg -ss <START_SECONDS> -t 1800 -i _scratch/audio/libertalia_theme_full.mp3 \
      -af "afade=t=in:st=0:d=2,afade=t=out:st=1795:d=5" \
      -c:a libmp3lame -b:a 128k -ar 48000 -ac 2 audio/libertalia_theme.mp3

## Room sfx

None yet. Per-room layers are sourced CC0-only from freesound via the `sound_pull` observer
(`Utilities/sound_pull/AGENTS.md` → *Licensing*) — CC0 only, because `audio/` ships to the public
GitHub Pages site. Add them here as they land, one row per file.
