I've read the four evidence files and verified the state on disk rather than trusting the table.

**The gate report is empty and the motion prompt on the table is stale.** `cinemagraph_tools/art_prompt_motion/beacons/anvil.txt` is stamped 2026-09-14 23:31 and still carries the pre-soften phrase — that file is what the brief displayed. It is not what the renderer will use: `exp_art_prompt.motion_prompt` resolves from `authoring.sceneSpec` first and falls back to the `.txt` only when the spec declares no mover (`cinemagraph_tools/exp_art_prompt.py:87-107`). anvil's spec declares one, so the live prompt is:

> locked-off static camera, zero camera movement. The loose corner of the canvas tarpaulin **lifting and settling slowly, breathing rather than flogging**. The shattered rock pavement and the mountains behind it, every object standing on the rock are rigid and fixed — … Only that moves; everything else stays perfectly still. Seamless natural loop.

62 words, with the two-item rigid pin auto-on via `spec["rigid"]` — the same shape as the 64-word prompt that produced the held ri53 render.

**The softening has already landed and it is phrase-only.** Diffing the live spec against `scenario.json.bak_20260915_075430_soften_three`, the single change in anvil is `fuel_tarp.motion.phrase`; `vigour`, `desc` and every other field are untouched, and `render_prompt(spec)` is byte-identical to the committed `authoring.scenePrompt` (7056 chars, equal). So the committed panorama is correct, `needs_still` cannot fire, and this is the cheap lever the pipeline prescribes for "too lively" — intensity language works downward, and Lucas's note was *"moving quite aggressively… should probably move more gently"*, not a complaint about the art.

**So there is nothing left to author.** The only anvil clip on disk is `ri53`, rendered from the aggressive phrase at 03:36 UTC; no clip exists for the current prompt. Room state is `{}` — attempts 0 of 1, nothing in flight. This is exactly the position sisters was in at cycle 94, which drew RENDER under the same review note. Seed stays 4242 per the note: softening and rolling in one render would confound the two.

DECISION: RENDER
WHY: The phrase-only softening is already in the spec, the art prompt is byte-identical to the committed still, and the spec-derived 62-word pinned motion prompt has never been rendered — the clip on disk predates it.