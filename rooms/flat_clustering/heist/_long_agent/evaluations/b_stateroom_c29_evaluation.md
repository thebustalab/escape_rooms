I checked every load-bearing claim against the tree rather than the write-up.

**Verified:**
- **Authored mover is real.** `porthole` carries `moves: true` + `vigour` + `phrase` in the live `scenario.json`, so `_has_authored_mover` (long_agent.py:3549, which requires all three) returns True and the RENDER branch at long_agent.py:3963 will not refuse.
- **Motion prompt resolves from the spec, not a file.** `exp_art_prompt.motion_prompt` tries `scene_spec.render_motion_prompt` first; I ran it and it emits *byte-identical* to the worker's quote — one mover named, "Only that moves". No `art_prompt_motion/heist/` directory exists, so there is no fallback file to override anything.
- **The still depicts it, and it is bounded.** I opened `b_stateroom/scene.png` at native 3072×1024 and cropped the left region: the porthole shows genuine open sea with wave crests and a horizon, roughly 5–6% of the frame. Not a dark disc, not frame-filling — the "water in one channel" archetype.
- **Not stale against its own motion intent.** The committed `scenePrompt` contains the exact vigour clause "the slow swell rising and falling close beyond the glass", so the still was generated from art that already knew about the swell. `needs_still` is unset, so the RENDER guard against animating an old panorama does not fire.
- **No attempt spent.** `b_stateroom` has no key in `state.json["rooms"]`, no files in `_long_agent/outputs` or `evaluations`, and no artifacts matching `stateroom` among the 388 files in `temp/cine/_art_prompt_exp/heist`. Budget is 2; this is render 1.

**Against the reject list:** no settings proposed (end guide 0.70 comes from `plan.json`, seed left default); the mover is bounded, not frame-filling; no zero-return reasoning is used at all (there is no clip to measure); nothing is accepted and no write to `scenario.json` art or hotspots is proposed; no hand-written art prompt; and it is RENDER, not AUTHOR_MOVER on an unrendered mover. The two things the worker deliberately declined — the pre-equirect stale `scenePrompt` and pre-emptive pinning of the desk charts — are correct to leave alone; the first would discard a human-triaged still over a seam concern the motion loop was not asked about, and the fix order pins non-movers only after a clip shows them moving.

The decision line also parses: `parse_room_decision` reads `DECISION: RENDER` cleanly, and no line in the body begins with `SPEC:` to contaminate the fragment.

VERDICT: PASS