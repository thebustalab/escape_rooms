# Henges — sound effect credits

All sourced from freesound.org, **Creative Commons 0** (public domain) — safe for the public
GitHub Pages site. Pulled via the `sound_pull` observer (see `Utilities/sound_pull/AGENTS.md`).
Music bed (`drowned_henges_theme.mp3`) is credited separately in `scenario.json` (`musicCredit`).

| file | freesound source | uploader | licence | role |
|------|------------------|----------|---------|------|
| `beach_waves_night.mp3`   | https://freesound.org/people/el_boss/sounds/587164/          | el_boss          | CC0 | beach — tidal waves bed |
| `wind_cold_loop.mp3`      | https://freesound.org/people/The_Isot_is_Back/sounds/638434/ | The_Isot_is_Back | CC0 | beach/mountain/boss — cold wind bed (loopable) |
| `plains_meadow.mp3`       | https://freesound.org/people/ali.g/sounds/855326/            | ali.g            | CC0 | plains — evening meadow (crickets/frogs) bed |
| `saltflat_wind_vast.mp3`  | https://freesound.org/people/IanStarGem/sounds/478812/       | IanStarGem       | CC0 | saltflat — vast eerie wind bed |
| `boss_dawn_birds.mp3`     | https://freesound.org/people/SamsterBirdies/sounds/578523/   | SamsterBirdies   | CC0 | boss — dawn chorus bed |
| `stone_drone.mp3`         | https://freesound.org/people/bassimat/sounds/854857/         | bassimat         | CC0 | shared — sacred stone drone (the henge hum, in every room) |
| `shimmer_crystal.mp3`     | https://freesound.org/people/newlocknew/sounds/772279/       | newlocknew       | CC0 | plains/saltflat — crystal shimmer (fireflies / glassy salt) |
| `solve_portal_awaken.mp3` | https://freesound.org/people/SkySpeira/sounds/848847/        | SkySpeira        | CC0 | solveSfx — scrying-basin solved, portal awakens (magical bell flourish) |
| `solve_portal_open.mp3`   | https://freesound.org/people/GammaGool/sounds/735062/        | GammaGool        | CC0 | solveSfx — mark-stone keyed, arch opens (fast warp-in) |
| `solve_way_home.mp3`      | https://freesound.org/people/Rvgerxini/sounds/554783/        | Rvgerxini        | CC0 | solveSfx — boss heart-stone, the way home (teleport) |

## Audition alternates (not pulled — swap in if a primary pick disappoints)
- cold wind: https://freesound.org/people/IanStarGem/sounds/478812/ (also a cave/wind synth)
- night crickets: https://freesound.org/people/BonnyOrbit/sounds/645863/
- dawn birds: https://freesound.org/people/richwise/sounds/466242/ (Hampshire dawn chorus)
- stone drone: https://freesound.org/people/xkeril/sounds/632682/ (deep rumbling drone)
- portal awaken sparkle: https://freesound.org/people/newlocknew/sounds/825544/
- stone grind: https://freesound.org/people/NahuelMartinez/sounds/844329/
- warm bell: https://freesound.org/people/manuelsound/sounds/829480/ ("Gling")

## Pull + post-processing (2026-08-29)

`beach_waves_night.mp3` and `plains_meadow.mp3` were credited above but **had never actually landed** —
`validate_assets.py` had been failing on both. Cause: `sound_pull.py`'s per-download timeout defaulted to
90 s while freesound throttles its preview mp3 to ~75 KiB/s, so any file over ~6.5 MB was unpullable by
construction and failed with no reason recorded. These two are 8 min and 21 min, so they never stood a
chance. Fixed in `Utilities/sound_pull/` (timeout 600 s + every failure now carries a reason); both pulled
clean on the retry. Same root cause as three temple ambiences — worth checking any other scenario whose
CREDITS lists a file that is not on disk.

Both were then **cut to 60 s seamless loops** (window chosen by scanning for the segment closest to the
file's overall level and steadiest within itself, then blended tail-into-head with
`youtube_audio.apply_crossfade_loop`, so the player's hard `audio.loop` has no seam). Full originals are in
`_scratch/audio/*_full.mp3` — re-cut from those, not from the shipped clip.

- `beach_waves_night.mp3` — 8:10 / 10.6 MB → 60 s / 939 KB
- `plains_meadow.mp3` — 20:41 / 28.4 MB → 60 s / 939 KB

**`beach`'s volume was 1.0** — the same signature as temple's `sun_altar_high_wind`, the other bed that was
missing from disk. Mixing against a file that is not there produces silence, so the slider gets pushed to
maximum. Set to 0.5 to match henges' other primary beds (0.51 / 0.52) — **a starting point, not a mix.**
If you find a bed pinned at 1.0, check the file exists before trusting the level.

**Also unreviewed:** three layers sit at volume 0.0 and are therefore silent — `plains/stone_drone`,
`saltflat/shimmer_crystal`, `boss/wind_cold_loop`. Deliberate mutes or leftovers, needs an ear.
