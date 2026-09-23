Verified each claim against the files rather than the worker's summary:

**Mover exists and is bounded.** `rooms[1].authoring.sceneSpec` carries exactly one element with `motion` set — `streamer`, with `vigour: "brisk and snapping"` and the phrase the worker quotes. All six other elements have `motion: null`. The still shows it plainly: a discrete pale membrane ribbon anchored at the strut by the sampler globe, streaming back left with a visible twist. It spans roughly x 77–1000 of 3072 (~30% of width, not the "quarter" the worker said) in one narrow diagonal band — a distinct object with its own edges, not a frame-filling field. Bounded.

**Art is not stale — confirmed two independent ways.** `scene_spec.render_prompt(sceneSpec)` reproduces the committed `scenePrompt` byte-identically (11396 chars), and `"brisk and snapping"` is in that committed prompt. Separately, the ap_grainrun `sceneSpec` and `scenePrompt` hash identically in `scenario.json.bak` (written at 23:26:22, the same second as `scene.png`) and in the current `scenario.json` — so the Sep 22 14:10 edit touched other rooms, not this one. The still was generated from this exact spec, mover included.

**Motion prompt is well-formed and travel-free.** 28 words (worker said 29 — immaterial), house form, one mover, purely oscillatory: snapping and rippling in place, no net path.

**No clip exists.** `_scratch/cine_cand/` holds only `cockpit`. Gate report empty.

**Against the reject list:** the 0.70 end guide comes from `_long_agent/plan.json` (`"end_guide": "0.70"`), not from the worker — no settings lever touched. Mover is bounded, not frame-filling. No zero-return reasoning anywhere, and none possible with no clip. No clip accepted, nothing written to committed art or hotspots. The art prompt is spec-derived, not hand-written. And it is not AUTHOR_MOVER on an unrendered mover — it is the opposite, and the correct call: this mover has never been rendered, so re-authoring now would be guessing ahead of evidence.

The only step left is the single render.

VERDICT: PASS