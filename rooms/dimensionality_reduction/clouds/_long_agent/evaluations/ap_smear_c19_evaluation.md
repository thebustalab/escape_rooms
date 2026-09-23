I checked every claim against the files rather than the worker's description.

**Verified independently:**

- **One mover, correctly shaped.** Only `rain` carries a `motion` block, and it has all three fields `_has_authored_mover` (long_agent.py:3580) requires — `moves`, `vigour`, `phrase`. The RENDER refusal branch at line 4618 will not fire.
- **Not blocked on a stale still.** `ap_smear` has no entry in state.json at all — no prior attempts, no `needs_still` set. The line-4603 block doesn't fire either.
- **Art is genuinely current.** I re-rendered `SS.render_prompt(spec)` against the cached `scenePrompt`: byte-identical, 10143 chars both. EQUIRECTANGULAR clause present at offset 236, the vigour "heavy and continuous" present in the body.
- **The "motion prompt: NONE" is a display artefact, not a real absence.** There is no art_prompt_motion/clouds/ap_smear.txt, but I called the renderer's actual resolver — `exp_art_prompt.motion_prompt('clouds','ap_smear',rec)` — and it returns the spec-rendered prompt, because the spec declares a mover and spec wins. The clip will carry the right prompt.
- **The mover is drawn, and bounded.** I cropped the committed 3072x1024 scene.png at native resolution. Both wing trailing edges show a distinct curtain of falling water against the dark shell — the left one spans roughly 270px of 3072, well under 10% of frame width. Falling water, which loops trivially. This is not the implied-mover failure that sank logwood_verdigris.

**Against the rejection criteria:** no settings touched (end guide stays pinned at 0.70), the mover is bounded not frame-filling, no zero-return reasoning is invoked (no clip exists), nothing is accepted or written into committed art or hotspots, and no prompt is hand-written — the decision explicitly declines SOFTEN_PROMPT. The AUTHOR_MOVER criterion cuts in favour here: the mover has never been rendered, so rendering it is precisely the right next move rather than re-authoring it.

The one thing worth noting for later: rain is depicted on **both** wings while the phrase says "the wing" singular. Both are the same bounded falling-water category, so neither the frame-filling nor the loop risk changes — but if the clip comes back odd, that asymmetry between prompt and image is the first place to look.

VERDICT: PASS