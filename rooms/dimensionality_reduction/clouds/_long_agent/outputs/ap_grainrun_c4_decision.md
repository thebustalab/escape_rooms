Everything checks out on inspection — nothing here needs re-authoring.

**What I verified:**

- **The spec already carries a bounded mover with authored vigour.** `streamer` (at `dead ahead in the centre`) ends with *"tied to the strut between the nose and the left wing, a long pale ribbon of membrane streaming back in the wind, close to the viewer"*, with `motion: {moves: true, vigour: "brisk and snapping", phrase: "the long membrane streamer snapping and rippling hard in the wind"}`. Hanging cloth/pennant is the ledger's strongest confirmed mover category.
- **The still actually depicts it.** Cropping `ap_grainrun/scene.png` at x 300–1100 shows the ribbon plainly: a discrete pale membrane streamer anchored at the strut, streaming back left with a snapping twist in it. Bounded — roughly a quarter of the width in one narrow band — not a `hood`-style frame-filling field.
- **The art is not stale.** `scene_spec.render_prompt(sceneSpec)` reproduces the committed `scenePrompt` **byte-identically** (11396 chars, exact match), and the vigour phrase *"brisk and snapping"* is present in that committed prompt — so this panorama was generated from the spec as it stands now, including the mover's vigour.
- **The spec-derived motion prompt is well-formed.** `render_motion_prompt` gives 29 words in house form: *"locked-off static camera, zero camera movement. The long membrane streamer snapping and rippling hard in the wind. Only that moves; everything else stays perfectly still. Seamless natural loop."* One mover, purely oscillatory — snapping and rippling in place, no net path, so the no-travel rule holds. (The "Current motion prompt: NONE" in the brief is the absent `.txt` fallback, not an absent prompt; the spec is the source of truth.)
- **No clip exists.** Gate report `{}`, nothing under `_scratch/cine_cand/ap_grainrun`, and only cockpit's files in the render dir.

Nothing left to author, nothing to soften, and no evidence of a wrong thing moving — that judgement needs a clip first, and the prompt already carries its blanket clause. The sibling room `cockpit`, same glider, cleared every gate on one render at 0.70.

DECISION: RENDER
WHY: The spec carries one bounded mover with an authored vigour that the committed still visibly depicts, the committed art prompt is byte-identical to the current spec's `render_prompt` so the art cannot be stale, the spec-derived motion prompt is well-formed and travel-free, and no clip has been rendered yet — so the only remaining step is the single render at end guide 0.70.