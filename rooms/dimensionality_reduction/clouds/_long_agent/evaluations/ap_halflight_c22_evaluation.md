Checked independently, not on the worker's word:

**Spec** — `ap_halflight`'s sceneSpec carries exactly one element with `motion`: `eyewall` (`at: "to the right"`), `vigour` "slow and immense, a steady turning", `phrase` "the vast funnel of cloud twisting slowly on itself as it reaches down". Every other element has `motion: null`. One mover, authored vigour.

**Bounded, not frame-filling** — this was the claim worth testing, since the element text also says "a sheer wall filling the whole right side". But the wall is the backdrop; the phrase names the funnel. In the committed 3072×1024 panorama the funnel is a discrete twisting column running from roughly x=0.72 to x=0.82 of the width, with its own silhouette against the wall behind it. That is a bounded object, not the frame-filling `hood` mode.

**Art not stale** — I re-derived it rather than trusting the number: `scene_spec.render_prompt(sceneSpec)` returns 10473 chars and compares `== authoring.scenePrompt` exactly. The committed still was generated from this spec.

**Motion prompt** — `scene_spec.render_motion_prompt` yields 30 words, house template, locked-off camera, one mover, rotation on its own axis. No net travel.

**State** — `state.json` has no `ap_halflight` entry at all, and `_scratch/cine_cand/ap_halflight` does not exist. Nothing rendered, nothing tried. The five siblings each went RENDER → HOLD on one render from this same spec shape.

Against the reject list: no settings change (0.70 is the recipe already in `instance.json`, not a proposed edit), mover is bounded, no zero-return reasoning (no clip exists), no acceptance and no write to committed art or hotspots, no hand-written art prompt, and not AUTHOR_MOVER on an unrendered mover.

One thing I noticed but is out of scope for this gate: the dash OVERRIDE is specified with "its six cells DARK", and in the still the six cells read as bright and lit. That is an art-fidelity question for Lucas's eye in the stills tab, not a motion defect, and it does not bear on the render.

VERDICT: PASS