Verified independently on disk rather than from the write-up:

- **Live spec** — `rooms/flat_clustering/heist/scenario.json` → `rooms[6]` is indeed `b_casino`, and `scene_spec.movers()` returns exactly one element, `smoke`, with `motion.{moves,vigour,phrase}` all authored. Bounded to the near baize, not frame-filling.
- **Prompt source** — `exp_art_prompt.motion_prompt("heist","b_casino",rec)` resolves byte-identical to `scene_spec.render_motion_prompt(spec)`, *not* to `art_prompt_motion/heist/b_casino.txt` (which differs — it still says "bank of cigarette smoke coils and drifts"). Spec precedence for heist is pinned by `test_motion_prompt_source.py`. Nothing hand-written.
- **Still is new and owed nothing** — `b_casino/scene.png` is 2026-09-14 12:29, its hash differs from the 09-05 `cine360/b_casino_source_still.png`, and `authoring.scenePrompt == scene_spec.render_prompt(spec)` today. Seam `stage: blurred`, `needsWork: false`.
- **No clip against this art** — newest render `b_casino_motion_ri58` is 07:05 today, five hours older than the still; `_long_agent/state.json` `rooms` contains only `a_opera`, so the empty gate report is genuine.
- **Lucas's `review_note`** quoted accurately, including "Render each ONCE and gate. Neither room needs re-authoring."
- **Settings untouched** — ri14 and ri58 params are both seed 4242 / cfg 2 / 8 steps / 3072×1024 / 73 frames / end guide 0.7, and `cine_render.py` sets `END_GUIDE = 0.70` as the settled recipe. "Default 0.70" is leaving the levers alone, not pulling one.

None of the reject conditions fire: no settings lever, bounded mover, no zero-return-as-death inference (it explicitly names the cyclic-flow case), no acceptance or scenario.json write, no hand-written prompt, and not AUTHOR_MOVER. The one thing owed is a single render and a gate.

VERDICT: PASS