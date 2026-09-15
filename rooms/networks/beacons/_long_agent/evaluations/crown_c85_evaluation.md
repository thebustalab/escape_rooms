I checked the worker's claims against the files rather than its description.

**Verified true (load-bearing):**
- `scene.png` is 2026-09-15 02:30:59 — fresh; the ledger at `_long_agent/progress.md:418-420` records generation 13, commit from `l1_crown_2.png`, and seam-stage "clean, done" at 06:31 UTC (= 02:31 EDT). The 11s gap to `scenario.json` is the loop's own post-commit write, not a stale still.
- `_has_authored_mover` (`Utilities/long_agent/long_agent.py:3554`) requires `moves` + `vigour` + `phrase`. `dispatch_pennant` carries all three on disk; it is the only element with a `motion` block. RENDER will not hit the refusal branch at line 4256.
- `render_motion_prompt` on the on-disk spec returns exactly 33 words, one mover, house form. The spec wins over the `.txt` — `exp_art_prompt.motion_prompt:86-108` tries the spec first and only falls through when it yields nothing, and `test_motion_prompt_source.py` pins that precedence. The "guyed mast" text in `art_prompt_motion/beacons/crown.txt` is genuinely unreachable, so the worker is right that it's inert here.
- I looked at the panorama. It depicts what was authored: a rust-orange pennant on a varnished staff stepped into a drystone cairn at left, streaming out level and taut with the frayed free end curling over. Bounded — one discrete object against sky, not a frame-filling mover.
- Room state is `{"art_generated": 1}` — no `needs_still`, no attempts spent, not parked, so RENDER proceeds rather than tripping the safety-net park. `cine_base.mp4` is Sep 7, predating this art, consistent with the empty gate report.

**One claim I could not corroborate:** the ledger quote "Ochre and crown worked" does not appear in the loop's progress ledger. That's a decorative appeal to prior outcome, not a premise the decision rests on, so it doesn't change the call — but it shouldn't have been asserted.

**Against the rejection criteria:** no settings change (RENDER at the plan's existing end guide), mover is bounded, no zero-return reasoning involved, nothing accepted and nothing written to committed art or hotspots (`_launch_cine_room` writes only to `temp/cine/_art_prompt_exp/`), no hand-written art prompt, and it isn't AUTHOR_MOVER on an unrendered mover.

VERDICT: PASS