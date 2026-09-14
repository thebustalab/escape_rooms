Checked the tree rather than the write-up. Everything the worker claims holds:

- **One bounded mover.** The a_gallery spec has exactly one element with motion.moves/vigour/phrase — the dust sheet. In the full 3072×1024 panorama it occupies roughly 8% of the width. Bounded, not frame-filling.
- **The still derives from the current spec.** I re-ran scene_spec.render_prompt on the live sceneSpec: 3389 chars, byte-identical to the committed scenePrompt (same md5). scene.png was rewritten 22:23 from candidate l1_a_gallery_2.png, and the seam was re-screened at 22:24 — needsWork false, ratio 2.43. The backup chain shows the softening landed before the regen, not after.
- **The art actually depicts it.** I cropped left-of-centre and looked: a canvas sheet draped over a plinth, pooling on the marble, beside the opened vitrine, with the conservator's trolley dead ahead. It's there.
- **The spec, not the stale text file, feeds the render.** exp_art_prompt.motion_prompt tries the spec first and only falls back to art_prompt_motion/heist/a_gallery.txt if the spec yields nothing. The softened phrase is what will render.
- **No clip for this still.** No mp4 anywhere under the scenario, gate report empty, and state.json's rooms map is reset, so the attempts budget is untouched. The cycle-13 HOLD belongs to the previous art.

Against the reject list: no settings change (0.70 is the plan's standing end guide, not a proposed lever), no frame-filling mover, no zero-return reasoning, no acceptance and no writes to committed art or hotspots, no hand-written prompt, and it isn't AUTHOR_MOVER. The runner's own RENDER guards — needs_still and _has_authored_mover — both pass.

VERDICT: PASS