I checked the frames, the spec, and the code path rather than the worker's description. The core technical facts about `sceneSpec` check out — but the decision rests on a false premise about what the runner will actually render.

**What's true:** `sceneSpec` has exactly one mover, `day_cloth`; `name_crag` is legacy `animate` only; `scene_spec.render_motion_prompt` does emit the cloth sentence; `scene.png` is from today 21:09 and the clips are from Sep 7, so the art *is* newer than the clip.

**What's wrong:** the worker resolved the prompt through `cinemagraph_tools/exp_art_prompt.py` — a file whose own docstring says "EXPERIMENT… Renders only — nothing is masked, baked, judged or wired." The loop runner is `cine_iterate.py`, which imports `cine_scenario` → `cine_stage.py:40` → `motion_spec.render_prompt(spec)`, where `spec` is `authoring.motionSpec`. `sceneSpec` is consulted nowhere in that path.

`spindle`'s committed `motionSpec` names a different hero:

- hero subject `needle_spindrift`, box `[0.24, 0.03, 0.37, 0.32]`, phrase *"a fine banner of spindrift streaming off the needle's edge…"*
- no cloth subject at all, and the negatives list includes `flags, pennants, bunting` — which actively suppresses the signal cloth
- `cine_base.mask.json` masks to the `needle_spindrift` box at 3.77% coverage, so the cloth region is frozen in the bake regardless of what the model does there

So acting on this RENDER produces another spindrift clip, not a cloth clip. The worker would then judge the result against an object the pipeline never asked for.

Worse, that spindrift hero **has** already been rendered against this spec: `cine_base.judge.json` shows verdict `hold`, every check `ok`, `needle_spindrift` alive at p95 10.27. That is a survivor held for a human eye, not a dead clip.

The worker's closing note is also aimed at the wrong artifact. `art_prompt_motion/beacons/spindle.txt` is genuinely unreachable, but the live two-sources-of-truth drift is inside `scenario.json` itself: `sceneSpec` says cloth, `motionSpec` says spindrift. Retiring the `.txt` would tidy the inert copy and leave the real conflict in place.

A re-render against the new art is legitimately owed — the still changed today. But which object is spindle's hero is now an unresolved conflict between two committed authored blocks, and the still shows both are real (cloth prominent at the near left, spindrift a thin wisp off the needle). That is a human call, not one to fire blind on a false premise.

VERDICT: REVIEW