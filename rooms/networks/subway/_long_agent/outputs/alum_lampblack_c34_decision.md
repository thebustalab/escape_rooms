I read the four authority docs, then checked this room's real state on disk rather than trusting the harness fields (which report an empty gate report and no history).

**What I found.** The spec already carries exactly one bounded mover — `soot_lamp`, with a full `motion` block — so `render_motion_prompt` resolves from the spec (no `.txt` fallback exists for this room, which also means the render could not have silently used a stale one):

> locked-off static camera, zero camera movement. The soot-lamp's tall yellow flame rolling and leaning in its open pan, its thick column of black smoke lifting steadily into the hood above it. Only that moves; everything else stays perfectly still. Seamless natural loop.

**A clip already exists from the current still.** `alum_lampblack_motion_ri49` was rendered today at 13:53 from the `scene.png` committed at 13:44, at the exact default settings (3072x1024, end guide 0.70, seed 4242, 8 steps, cfg 2.0, 73 frames). The round-3 job's `state.json` lost that record when round 2 was archived early, which is why the previous cycle proposed RENDER and was failed — a fourth run at the same seed, still and prompt reproduces ri49 and buys nothing.

**I re-ran the gates myself** (CPU only, no GPU) and reproduced the logged report byte for byte: camera still, glitch 0.062 raw / 0.042 normalised against a 0.70 both-readings threshold, dead gate explicitly negative at wander ratio 17.93 and peak 25.02, return 0.00.

**And the motion is the authored mover, not something else.** Per-column tile analysis of the raw render puts all the motion in one narrow column at x≈0.646 (4.52 against a 0.27–0.41 background band everywhere else), peaking low in the frame at y≈0.69. `scene_spec._POS` maps "just right of centre" — the soot-lamp's `at` — to exactly 0.64. The flame and its smoke column are what move; the train, stair, walls and floor are still. The 0.00 return is the documented cyclic-flow ambiguity, which is what flame and smoke always score.

Nothing to author, nothing to soften, nothing wrongly moving, and nothing to re-render.

DECISION: HOLD
WHY: The existing render `/home/bustalab/Documents/Tools/temp/cine/_art_prompt_exp/subway/alum_lampblack_motion_ri49_looped.mp4` was made from the current committed still with the spec's own motion prompt at the default settings, clears all four reject-only gates, and confines its motion to one narrow column at x≈0.65 exactly where the spec places the soot-lamp — so it goes to Lucas's eye, not back to the GPU.