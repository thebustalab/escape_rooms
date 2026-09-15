Checked it myself rather than taking the worker's word.

**Verified against the actual files:**

- **Bounded mover, confirmed two ways.** The Sep-7 judge in sisters/cine_base.judge.json localises `cloud_river` to `[0.44, 0.24, 0.64, 0.66]`, verdict `alive`, p95 11.55 — and cine_base.mask.json records coverage 0.0839, i.e. 8.4% of frame. I also opened the committed scene.png: the cloud is one discrete cascade pouring over the ridge just right of centre, with clear cobalt sky above and static rock either side. This is nothing like hood's valley-filling sea.
- **I computed the motion prompt rather than trusting the description.** Running `exp_art_prompt.motion_prompt('beacons','sisters')` returns: *"locked-off static camera, zero camera movement. The great bank of cloud spilling over the ridge saddle pours slowly down into the valley, its billowing front curling and re-forming as it comes. Only that moves; everything else stays perfectly still. Seamless natural loop."* Spec-derived from `col_cloud.motion.phrase`, one mover named, and — the point that mattered — **no rigid clause**. The bloated 7-item inventory lives in `motionSpec.rigid`, a different object; the `rigid=` gate at exp_art_prompt.py:98 reads `sceneSpec`, which has no `rigid` key. The worker's claim holds. (It said 38 words; it's 42. Immaterial.)
- **The still is real and eligible.** scene.png committed Sep 3, `accepted: true` by Lucas, `needsWork: false`, and sisters has no `needs_still` flag in state.json.

**Against the reject list:** no settings change (end guide stays the plan's pinned 0.70), mover is bounded not frame-filling, no zero-return-means-dead reasoning (gate report is empty — nothing to reason from), no clip accepted, nothing written to committed art or hotspots, no hand-written art prompt, and it isn't AUTHOR_MOVER. It also matches the precedent this loop already set on fenwatch c1 and spindle c4: first cycle on an authored room with no clip → one render.

The side-note about the cached scenePrompt predating the EQUIRECT clause is correctly flagged and correctly not acted on — regenerating would throw away human-accepted art for a reason unrelated to motion.

VERDICT: PASS