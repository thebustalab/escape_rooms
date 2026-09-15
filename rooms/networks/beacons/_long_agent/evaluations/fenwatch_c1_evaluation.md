I checked the spec, the still, the prompt resolution code, and the room's committed state rather than taking the write-up on trust.

**What holds up.** The committed spec at rooms/networks/beacons/scenario.json declares exactly two movers — river_mist and chimney_smoke — each with a full motion.{moves,vigour,phrase} block. I resolved the prompt through the real code path and it comes out verbatim as the worker quoted it: two distinct phrases joined with "; ", no duplicate-sentence bug. The spec-beats-.txt precedence is real and deliberate — cinemagraph_tools/test_motion_prompt_source.py records Lucas overruling the old .txt precedence for heist/subway/beacons on 2026-09-13 — so the legacy "white woodsmoke rises" text genuinely is dead weight here.

I looked at the still myself. Both movers are bounded: the mist is a low strip lying along the river bed at left, well under the peaks, and the smoke is a plume over the slate roof just right of centre. Neither is frame-filling — the judge's own boxes put them at roughly 8% and 7% of frame area. The worker also correctly refuses to treat the 1536 probe cluster as proof of death.

**One thing it got wrong.** "No clip exists at deployment resolution yet" is false — there's a committed 3072x1024 cine_base.mp4 from Sep 9, and a night clip too. The gate brief said "Clip: none yet", so the worker inherited that error rather than inventing it.

It doesn't flip the verdict, and the true state actually strengthens the case. The provenance sidecar cine_base.cand.json records that committed clip as tag menu_s1234 — a menu-template seed-menu pick. The ledger says the menu prompt is precisely what "turned a reliable clip into a coin flip" on fenwatch, while the living template is credited with this room's two accepted clips. The spec-derived prompt is living-shaped. Separately, the existing judge file is stale — its clip_mtime is Sep 5, four days older than the clip sitting next to it — so its "alive/alive" subject verdicts don't describe what's currently committed.

So the render isn't the first clip, but it is the first spec-derived one, and it swaps a known-bad-template clip for the template that has actually worked here. None of the six rejection criteria are hit: no settings change, bounded movers, no zero-return death call, no acceptance or scenario.json write, no hand-written prompt, no premature AUTHOR_MOVER.

The runner should expect this to overwrite an existing clip rather than fill an empty slot — that's normal for this pipeline, which keeps .pre_ backups, but it's worth knowing the render isn't free of a prior artefact.

VERDICT: PASS