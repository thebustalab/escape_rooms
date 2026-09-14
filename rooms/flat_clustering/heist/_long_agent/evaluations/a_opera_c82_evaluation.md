I verified the worker's claims against disk rather than its summary.

**Spec / prompt state — confirmed.** The live `a_opera` spec carries the c81 phrase (*"…stirring slowly in a draught, its folds shifting a little and settling"*). `SS.render_prompt(sceneSpec)` returns 3129 chars, **byte-identical** to the stored `scenePrompt` — so no still is owed and Lucas's reviewed art (lighter sizing included) is untouched. `render_motion_prompt(sceneSpec)` reproduces `art_prompt_motion/heist/a_opera.txt` exactly, so the motion prompt is spec-derived, not hand-written.

**Timing — confirmed.** The txt was written `12:57:48` local, which is exactly `last_cycle: 2026-09-14T16:57:48Z` (c81). The newest clip `ri78` is `12:43–12:45`. The new wording has never been rendered; there is no ri81 artefact.

**Budget — confirmed.** `plan.json: max_attempts_per_room: 2`, room `attempts: 1`. One render left.

**Deadness — I measured it myself, and it is not resting on the zero return.** Independent per-pixel temporal std at my own scale:

| clip | frame-median col std | swag band (x .15–.33) | peak |
|---|---|---|---|
| ri75 | 1.17 | **5.23** | 10.51 **at x=0.26 (the swag)** |
| ri78 | 0.86 | **0.83** | 1.49 at x=0.40 (not the swag) |

ri78's swag band sits *below* the frame median and the global peak has migrated off the curtain; mean abs difference from frame 0 rises to ~1.4/255 by frame 18 and flatlines — a global settle, not cyclic flow. The same measure lights up ri75 at 4.5× median with the peak pinned on the swag, so it discriminates. The dead call is spatial, which is exactly what the gate note's warning asks for.

**No reject clause fires:** no settings change (ri78 params are the frozen seed-4242 set and the decision leaves them alone), the mover is one bounded curtain, the deadness is not inferred from the zero return, nothing is accepted or written into committed art/hotspots, the prompt is authored through the spec, and this is not AUTHOR_MOVER.

One flag for the record, not a reason to block: this spends the last budgeted render, so if the third measured point also misses, the room parks for Lucas's eye — which is the correct terminal state anyway.

VERDICT: PASS