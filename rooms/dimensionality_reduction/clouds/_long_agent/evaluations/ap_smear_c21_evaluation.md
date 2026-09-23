Every load-bearing claim checks out against source, not the worker's description:

**Gate thresholds, read from the gate code itself:**
- `cine_glitch_check.py:22-25` — rejects only when **both** breadth readings exceed 0.70. This clip is 0.021 raw / 0.000 normalised. The same comment confirms `spike` "is reported and never gated," so the 3.23 is noise, correctly ignored.
- `cine_dead_check.py:32-33` — `DEAD_RATIO = 1.75`, `DEAD_PEAK = 0.45`. Clip is 10.54 and 7.64. Alive by a wide margin, and the gate's own `dead: false`.
- `cine_camera_check.py:89` — `still` is the fall-through after every conviction branch, below `BORDERLINE = 1.0`. Cleanest verdict available.

**The staleness check, re-run rather than trusted:** I re-rendered from `authoring.sceneSpec` — `render_prompt` is 10143 chars and byte-identical to the cached `scenePrompt` (`True`), EQUIRECT present. The art is genuinely not stale against the committed still. The motion prompt resolves from the spec in the house form, verbatim as the worker quoted it (29 words, not 28 — immaterial).

**The trap it didn't fall into:** `authoring.motionSpec` is `None` on this room. `room_iterate.yaml:25-38` records that "the production path reads motionSpec, so the decision is judging the wrong artefact" has been asserted by an evaluator twice and was wrong both times — the most expensive recurring error in this loop. The worker verified through `exp_art_prompt.motion_prompt` → `scene_spec.render_motion_prompt`, which is the right path, and the absent motionSpec is correctly irrelevant.

**The frames:** camera is locked — frame 0, mid-loop and last frame register identically. The ×8 difference map puts motion on the wing trailing edges and the storm curtain, while the dash, the sampler globe, the reading-pane and the whole left-side city sit black, i.e. still. That is a bounded mover, not a frame-filling one, and nothing suggests the wrong subject is animating.

**Against the reject list:** no settings change; no frame-filling mover; return is 0.13, treated as non-ambiguous and never used as proof of death; no clip accepted and nothing written to `scenario.json`; no hand-written prompt; not AUTHOR_MOVER. `HOLD` is a defined verb in this task — "survived the gates. This is NOT acceptance; it queues Lucas's eye" — so it respects the loop's one inviolable rule that metrics may auto-reject but never auto-approve.

Three reject-only gates all declined to reject, and no gate is permitted to approve. The only step left is the human eye, and HOLD is precisely the verb that routes there.

VERDICT: PASS