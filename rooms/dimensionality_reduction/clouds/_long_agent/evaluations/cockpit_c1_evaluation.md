I checked the worker's claims against the files rather than its description.

**Verified independently:**
- `scenario.json` → `rooms[0]` (`key: cockpit`), `authoring.sceneSpec`: exactly one element (`sampler`) carries `motion` with `moves: true`, a vigour and a phrase — so `_has_authored_mover()` (long_agent.py:3580) returns True and the RENDER branch's guard (long_agent.py:4618) will not refuse.
- `scene_spec.render_prompt(spec)` recomputed = committed `authoring.scenePrompt`, byte-identical, 10352 chars both. The still is not stale against its own spec.
- `scene_spec.render_motion_prompt(spec)` resolves from the spec: *"locked-off static camera, zero camera movement. The captured cloud-garden bloom drifting, turning and pulsing slowly inside its glass sampler globe. Only that moves; everything else stays perfectly still. Seamless natural loop."* — 31 words (worker said 32; immaterial), one mover, oscillatory, no travel.
- `_x_from_at` (scene_spec.py:356) resolves all seven `at` values, 0.08→0.92, none falling through to the order-based default.
- **The art**: I opened `cockpit/scene.png` at native 3072×1024 and cropped the sampler box. The glass globe is there on the dash just left of centre with a distinct glowing white-gold bloom inside it — roughly 240×200 px, ~1.5% of frame. Bounded, well clear of frame-filling, and unambiguously the thing the motion phrase names.
- `cockpit/` contains only `scene.png` — no clip exists, `state.rooms` is `{}`, so `needs_still` is unset.

**Against the reject list:** no settings change (the 0.70 end guide comes from `plan.json`, not from the worker); the mover is bounded; no zero-return reasoning anywhere (there is no clip to measure); no clip accepted and nothing written into committed art or hotspots; no hand-written art prompt — the motion prompt is spec-derived; and it is not AUTHOR_MOVER on an unrendered mover.

The one thing worth naming: the worker's phrasing "`scene_spec.render_prompt` on the current sceneSpec is byte-identical" describes a recomputation, not a stored field — there is no `render_prompt` key in the sceneSpec. I re-ran the builder myself and the equality holds, so the conclusion stands.

VERDICT: PASS