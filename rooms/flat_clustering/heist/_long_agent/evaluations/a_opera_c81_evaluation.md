Verified every load-bearing claim myself rather than trusting the write-up.

**The dead-vs-cyclic call is independently measured, not inferred from the zero return.** I extracted all 73 frames of both clips and computed per-band temporal variance:

- ri75 (the "too aggressive" endpoint): bands at x 0.12–0.38 — exactly where the swag is authored, "to the left" — measure 4.8–5.0 against a frame median of 1.13. A strong, localised mover.
- ri78 (the clip under gate): no band anywhere exceeds 1.5, and the swag's own band measures 0.77 against a frame median of 0.895 — *below* the median. There is no localised variance in the frame at all.

Cyclic flow would still light up that band; nothing does. So the death call rests on direct measurement at the authored position, which is what the gate's zero-return caution demands. That clears the sharpest rejection criterion.

**The rest checks out exactly:**
- Render params for ri75 and ri78 are byte-identical (seed 4242, 8 steps, cfg 2.0, end guide 0.7, 73 frames) — the two wordings are a clean controlled comparison, and the proposal changes no setting.
- Applying the fragment under the runner's own deep-merge semantics leaves the art prompt byte-identical at 3129 chars, and that matches the stored scenePrompt. The runner gates needs_still on comparing rendered art prompts, so no still is regenerated and Lucas's lighter sizing is untouched.
- The rigid clause does survive: the renderer turns rigid on from spec["rigid"] itself, which is non-empty here. Current prompt is 57 words, proposed is 62, both carrying the walls-and-parapet pin. The "wall weirdly breathing" fix stays answered.
- The 104-word file at cinemagraph_tools/art_prompt_motion/heist/a_opera.txt does exist but is only a fallback — the spec path wins for heist, so the worker's aside about the brief quoting an unreachable prompt is correct and worth fixing in the brief assembler.

The proposed wording is genuinely intermediate between the two measured endpoints and lands on the vigour the still depicts, without touching the vigour field (which would cost a still). Not a settings change, not frame-filling, not AUTHOR_MOVER, hand-writes no art prompt, accepts no clip, writes nothing into committed art or hotspots.

VERDICT: PASS