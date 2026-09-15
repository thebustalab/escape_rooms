I checked the room myself rather than relying on the worker's summary.

**Spec (live, `scenario.json` → `rooms[key=b_casino].authoring.sceneSpec`):** matches what was quoted. The duplicate `id: "smoke"` is real — the compact plume (`moves: true`, with `vigour` + `phrase`) and a stale bank (`moves: false`). Note the room's `scene_specs_heist.json` entry is the *old* pre-reauthor spec; the live one is in `scenario.json`, which is what the pipeline reads.

**Motion prompt** — rendered from the on-disk spec via `scene_spec.render_motion_prompt`, not hand-written:

> locked-off static camera, zero camera movement. The compact plume of cigar smoke rising from the ashtray on the near baize, its coils curling and rolling over as they climb. Only that moves; everything else stays perfectly still. Seamless natural loop.

40 words, and the `moves: false` bank is correctly excluded — the duplicate element leaks into the *art* prompt only, not the motion prompt. So the contradiction the worker flagged cannot affect this render.

**The still** — `scene.png`, 16:26 today, `seam.stage: "occluded"`, `needsWork: false`. At native resolution the left baize carries exactly one mover: a single cigar-smoke ribbon off a crystal ashtray at x≈0.19, three legible coils, thinning out in a narrow column, with clear air over the far tables and no haze layer anywhere. Bounded and non-frame-filling. No bank was rendered, so the prompt contradiction resolved the right way in the art.

**"No clip yet"** — worth being precise, because there *are* b_casino clips on disk. The newest, `ri104`, is 15:29; the committed still was rewritten at 16:26 (occluder composited over the 15:04 image, backed up as `scene_undo3.png`). Every existing clip predates the current still, so none of them is a render of this image. The framing holds.

Against the rejection list: no settings change proposed; mover is bounded, not frame-filling; no zero-return reasoning anywhere (gate report is empty); no clip acceptance and no write to committed art or hotspots; the prompt is spec-derived; and it isn't AUTHOR_MOVER on an unrendered mover — it's the first render of that mover, which is the correct move. The flagged duplicate-smoke cleanup is left for a later regeneration rather than acted on, which is the cheap call given the art is demonstrably correct.

One thing for your eye, not a blocker: a plain RENDER calls `render_motion_prompt` with `rigid=False`, so the `rigid` clause pinning the pasted-in pilaster only enters on a `PIN_NON_MOVERS` pass. If the composited pilaster warps in this clip, that's the lever to reach for next, not a re-author.

VERDICT: PASS