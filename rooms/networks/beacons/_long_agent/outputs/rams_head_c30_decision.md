Evidence checked. Here's what the state actually is:

- **The still is brand new** (`rams_head/scene.png`, committed 21:35 local from `l1_rams_head_3.png`, seam-staged) and it **depicts the authored mover plainly** — a near, high-contrast meltwater ribbon falling clear of the horn down the left third, braiding as it goes. Bounded, not frame-filling; falling water is on the ledger's confirmed-mover list, and ladder's waterfall was the single genuine mover in the whole flicker audit (3.35x over rigid).
- **The motion prompt in my brief is the stale `.txt` fallback, not what will render.** The live spec's `melt_ribbon.motion.phrase` resolves through `exp_art_prompt.motion_prompt` → `scene_spec.render_motion_prompt` and emits a 34-word prompt naming the ribbon and nothing else. `cirque_tarn`'s leftover legacy `animate` block is invisible to that path, so there is no two-movers conflict to fix.
- **No clip exists from this art.** The 00:02 UTC hold was the previous still with the tarn as declared mover; `state.json` for rams_head now carries only `art_generated: 1`, no gate and no clip.

Spec, still and prompt agree, and nothing is authored wrong — so this is the one render, not another authoring pass. Vigour is on the lively side ("falling fast and full"), but intensity language only works downward and that lever stays available after the clip exists; pre-softening art nobody has watched move would be searching settings backwards.

DECISION: RENDER
WHY: The freshly committed still depicts one near bounded mover — the meltwater ribbon falling past the shelf edge — the spec renders a 34-word motion prompt naming only that ribbon, and no clip has yet been rendered from this art.