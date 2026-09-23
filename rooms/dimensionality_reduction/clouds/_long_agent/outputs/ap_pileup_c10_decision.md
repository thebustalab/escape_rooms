I read the four authority files, then verified this room's actual state rather than trusting cycle 7's forecast.

**What I checked**

- **The art is fresh, not stale.** `render_prompt(current sceneSpec)` is byte-identical to the committed `scenePrompt` (10,635 chars both), and `scene.png` was regenerated at 22:57 alongside the spec edit (`art_generated: 1`). This still *is* what the post-AUTHOR_MOVER spec produced.
- **The mover is depicted, and it is bounded.** I cropped `_POS["just left of centre"]` → x=0.36 and looked. The glass sampler globe is there, large and sharp, with a pale luminous bloom glowing inside it — enclosed in hard glass, so it physically cannot travel. It occupies a small fraction of frame width: bounded, not frame-filling, and not a diffuse sea like `hood`'s cloud.
- **The doubling risk the cycle-7 evaluator flagged did not materialise.** `nose` also names the globe, and the worker's "ONE and only… drawn exactly once" guard held: across the full panorama there is exactly one globe, with the reading-pane at centre and the override cells to its right. Nothing to disambiguate.
- **One mover, not several.** `sampler` is the only element carrying `motion`, so the prompt is a single clause: *"locked-off static camera, zero camera movement. The captured cloud-garden bloom drifting, turning and pulsing slowly inside its glass sampler globe. Only that moves; everything else stays perfectly still. Seamless natural loop."* — 33 words, house form, no re-description of the scene.
- **Travel-free.** "drifting, turning and pulsing" inside a sealed globe names only oscillatory phenomena; the forbidden torn-cloud "streaming past… parting around" is gone from `motion`, `animate` and the desc alike.
- **No clip exists and the gate report is empty**, so there is no defect to act on — no vigour to adjust, no prompt to soften, nothing to pin. The scenario's own `cockpit` room held first render on this same element at this same `at` (return 0.28, glitch 0.146, camera still), and `ap_grainrun` held too, so the precedent for the settled recipe here is direct.

Everything that controls how much this room moves is already set before the GPU is touched. The only remaining step is the single render at the settled recipe.

DECISION: RENDER
WHY: The regenerated still now visibly depicts the spec's one bounded mover — a glass-enclosed bloom at x=0.36, singular despite the `nose` doubling risk — the committed art prompt is byte-identical to the current spec so the art cannot be stale, the spec-derived motion prompt is well-formed and travel-free, and no clip has been rendered yet.