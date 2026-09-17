**Checked independently:**

- `ochre_hall/scene.png` — mtime today 14:08, `_long_agent/state.json` has `ochre_hall: {art_generated: 1}`, seam written at `2026-09-17T14:08:23` with `needsWork: false`. The still is fresh from the round-3 spec, as claimed.
- I looked at the frame. The round-3 fix held: exactly one brick-ringed tunnel mouth at the left end of a single road, buffer stops with a red lamp against the blind wall at the right, one train body sitting on the rails with its floor at platform level, spiral stair inboard on the left, traffic desk inboard on the right. The `dust_sheeting` mover is actually depicted — a short bounded run of pale canvas slung along the platform rail just right of centre, tied at intervals, read against the dark road behind it. Bounded, not frame-filling.
- On-disk spec: `dust_sheeting` is the only element with a `motion` block; `vault_shafts` carries only the legacy `animate` block. One authored mover, no competition.
- `scene_spec.render_motion_prompt` on the live spec yields the house-form prompt naming only the sheeting ("locked-off static camera… Only that moves… Seamless natural loop"). It's 49 words, not the 40 the worker stated — immaterial to the decision.
- `.cine_published.json` does carry an `ochre_hall` entry, but it points at `ochre_hall_motion_ri4_roll1_looped.mp4`, baked from the pre-regen art. There is no clip for the still now on disk, so there is nothing to judge and nothing being accepted.

No reject condition fires: no settings lever, bounded mover, no zero-return reasoning, no clip accepted, no hand-written art prompt, no AUTHOR_MOVER on an unrendered mover.

One thing for the runner to carry forward, not a blocker: `authoring.motionSpec.rigid` is still the legacy derivation and names the removed `LEFT-HAND END` / `RIGHT-HAND END` elements. Its clauses are all hold-still instructions, so they're harmless here, but that stored block is stale against the round-3 spec.

VERDICT: PASS