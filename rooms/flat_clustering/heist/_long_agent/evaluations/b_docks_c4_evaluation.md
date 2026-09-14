I checked the claims against the live tree rather than the write-up.

**What holds up:**
- The diagnosis is correct. b_docks's tarp carries only a legacy `animate` block, no `motion`. `_has_authored_mover` (long_agent.py:3549) requires `moves` + `vigour` + `phrase`, so RENDER is refused unconditionally at long_agent.py:3847. Verified against the live scenario.json.
- The fragment is well-formed. It merges onto element index 0 (`tarp`) by `at`, preserves the authored desc, and I ran it through `scene_spec`: `render_motion_prompt` comes out **byte-identical** to the committed cinemagraph_tools/art_prompt_motion/heist/b_docks.txt. That half of the verification is true.
- The "never rendered" gate does **not** fire. There are 116 b_docks render artifacts in temp/cine/_art_prompt_exp/heist, including the full cal50/60/70/80 × 4-seed grid. The mover has genuinely been rendered.

**What does not hold up — and it's the load-bearing claim:**

`render_prompt` is **not** byte-identical. The committed scenePrompt is 1782 chars; the current renderer emits 3121. The committed prompt predates the current `scene_spec`, and the diff is ~1339 chars of added panorama-discipline boilerplate (EQUIRECTANGULAR projection block, the 24mm/f8 camera line, EDGE DISCIPLINE, GROUND IS ONE SURFACE). No authored content is lost, but applying the fragment silently overwrites the prompt that produced the triaged still — and this tree is **not under version control**, so that overwrite is unrecoverable.

That falsifies the cheap lever too. "The existing scene.png is exactly what a regeneration would produce" is wrong — a regeneration would run a materially longer, more constrained prompt. The `touch` may still be defensible on other grounds (the still provably depicts the tarp, and the motion prompt is unchanged), but Lucas would be clearing a guard on a stated reason that isn't true.

The a_vault analogy is precisely where it breaks: I checked, and a_vault's committed scenePrompt already equals `render_prompt(spec)` exactly. Its migration was lossless. b_docks is not the same shape.

Cost of refusing is one cycle — retries increments, the next cycle is queued, and the evaluator text is fed back as `last_eval`. The worker should re-propose the same fragment with the scenePrompt regeneration acknowledged and the current 1782-char prompt preserved somewhere first (it exists nowhere else), rather than certified as a no-op.

VERDICT: FAIL