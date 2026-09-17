I checked the room's state on disk and the frames myself rather than taking the worker's summary on trust.

**What the record shows**

- `_long_agent/state.json`: `ochre_woad: {"art_generated": 1}` — no `clip`, no `staged`, no `last_gate`, no history. No `cine_cand/ochre_woad` directory exists. Nothing has ever been rendered against this art.
- `progress.md`, 18:30 UTC: new art committed from `l1_ochre_woad_3.png` and seam-staged clean (mid band, run 0.018), boxes re-placed (`boxesFrom.art bb6d7527ae21`, 14:30:53). `scene.png` is 3072×1024, written 14:30 today. So the still postdates the round-3 spec fix — the plan's third done-criterion (no clip animating a stale still) is satisfied.
- The spec carries exactly one mover: `lamp_on_flex`, `motion.moves: true`, authored vigour and phrase, plus an `animate` block. Every other element is inert.
- `authoring.motionSpec` exists and is derived from the spec (`derivedFrom: sceneSpec.animate`), with a **measured** subject box of `[0.658, 0.2743, 0.6788, 0.3353]` — roughly 2% of frame width by 6% of height. That is a bounded mover by measurement, not by assertion.

**What the frames show**

The still depicts the mover plainly: a single caged work-lamp on a long yellow flex hanging free from the barrel vault just right of centre, small and isolated against the tile, nothing near it that could be dragged along. The round-3 fault is genuinely gone — one tunnel mouth only, at the left-hand end of the single road; the right-hand end is timber buffer stops, a red lamp and blind brick. Both spiral stairs stand inboard of the frame edges, the track bed is one unbroken pair of rails with the blue car's wheels on the railheads and its floor level with the platform edge, and the wrap edges are plain tiled wall.

**Against the reject list**: no settings proposed — 0.70 is `plan.json`'s configured `end_guide` and 3072×1024 is the still's own size, so neither is a change. The mover is bounded, not frame-filling. No zero-return reasoning is in play because no clip exists. Nothing is accepted and nothing is written to committed art or hotspots. The art prompt was rendered from the spec by the runner, not hand-written. And it is not AUTHOR_MOVER on an unrendered mover — it is precisely the render that mover has never had.

Two small corrections to the worker's account, neither load-bearing: the prompt it quoted uses the element's `motion.phrase`, while `motionSpec.subjects[0].phrase` carries the `animate` wording instead — both gentle and bounded, so either register is fine. And `motionSpec.rigid` is stale: it still names "the LEFT-HAND END of the station" and "the RIGHT-HAND END of the station" (elements deleted in the round-3 fix) and says "tunnel mouths" plural. That list only enumerates things to hold still, so naming departed elements costs nothing and introduces no second mover — worth cleaning up on a later authoring pass, not worth withholding the render for.

The spec, the committed still and the motion prompt all agree on one small swinging lamp, and the only thing missing is the render itself.

VERDICT: PASS