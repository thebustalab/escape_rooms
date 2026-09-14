Evidence read; state verified on disk. Findings:

- **Live spec** (`rooms/flat_clustering/heist/scenario.json` → `rooms[6].authoring.sceneSpec`) declares exactly one bounded mover, `smoke` over the near baize, with `motion.{moves,vigour,phrase}` all authored — so `scene_spec.movers` sees it and `render_motion_prompt` resolves from the spec, not the stale `art_prompt_motion/heist/b_casino.txt` (whose text is what the cycle brief quoted).
- **The committed still is new and owed nothing**: `b_casino/scene.png` is 2026-09-14 12:29, and `authoring.scenePrompt` is byte-identical to `scene_spec.render_prompt(spec)` today — the art was generated from this exact spec. Seam staged `blurred`, `needsWork: false`.
- **No clip exists for this art**: the newest render, `b_casino_motion_ri58`, is 07:05 today, five hours older than the still. `state.json` has no `b_casino` entry, matching the empty gate report.
- Lucas's `review_note` for this round is explicit: *"b_casino — NEW committed art… Render each ONCE and gate. Neither room needs re-authoring."*
- Historically b_casino's smoke is alive across 0.50–0.80 and all four calibration seeds; its 0.00 return is the documented cyclic-flow case, not death. Nothing here justifies touching vigour or the phrase before a clip exists.

DECISION: RENDER
WHY: The spec carries one bounded, vigour-authored mover whose motion prompt resolves from the spec, the committed still is freshly regenerated from that same spec and seam-clean, and no clip has ever been rendered against it — so the one thing owed is a single render at the default 0.70 and a gate.