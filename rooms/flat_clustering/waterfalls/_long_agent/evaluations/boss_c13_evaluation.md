I checked the boss room's still and spec myself. The worker's call holds up. There's no clip yet, so this is the first render of this mover, not a re-author.

- **The still exists:** `boss/scene.png`, 3072×1024, committed from `l1_boss_2.png`. It shows one sluice left of centre pouring into its trough, with vapour on the floor. The fall is contained: the rest of the frame (bridge, font, wheel, warning-stone) stands still. It isn't a frame-filling mover.
- **The mover is fully specified:** the `sluice_wall` element has its own `motion.phrase`, `vigour` and `animate` block. The motion prompt gets built from the spec, and nobody is hand-writing an art prompt.
- **No settings change:** "3072 with end guide 0.70" is the pipeline's normal render. It doesn't touch seed, steps, cfg, length or resolution.
- **Nothing gets accepted or committed:** there's no zero-return reasoning, and nothing is written into scenario.json's art or hotspots.

One small note, not a blocker: a low spill runs over the front of the trough and is part of the same mover. The clip review should confirm it reads as a short spill, not a second fall.

VERDICT: PASS