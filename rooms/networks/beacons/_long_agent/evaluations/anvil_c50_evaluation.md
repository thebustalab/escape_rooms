I checked the frames, the spec and the code path rather than the worker's summary.

**What I verified**

- The still is real and it depicts the mover. I cropped the left near field of scene.png (3072×1024, written 23:08:22) and the torn tarpaulin corner is plainly there — flown free of its rope, standing out off the fuel stack, bounded at roughly x 500–640, y 540–700. Near field, large, and nothing like frame-filling.
- The spec carries exactly one element with `motion.moves` — `fuel_tarp` — and it has both a vigour and a phrase, so the runner's own `_has_authored_mover` check passes. `heat_shimmer` and `depot_smoke` are legacy `animate` only and are not movers under the live schema.
- The stored `scenePrompt` is byte-identical to `render_prompt(spec)` (7056 chars both), so the committed art came from *this* spec. The room's runner state is just `{"art_generated": 1}` — no `needs_still`, so RENDER will not be blocked.
- I ran `render_motion_prompt` myself against the live scenario.json. It returns exactly the 34-word form the worker quoted, naming only the tarpaulin.

**The one claim worth pressure-testing** was the stale .txt. The worker waved it away, so I read the resolver rather than trusting that. exp_art_prompt.py lines 86–105: if the sceneSpec declares movers, the spec-derived prompt is returned and the .txt is never reached — it is the fallback, not the override. The 2026-09-08 anvil.txt naming heat shimmer and depot smoke is genuinely dead text here. The worker is right, and right for the right reason.

I also checked the trap that caught the previous cycle: the last evaluation faulted a worker for resolving through a path the runner doesn't use. That concern was about `cine_iterate` reading `motionSpec`. This job is `task_type: room_iterate`, which goes long_agent → cine_room.py → exp_art_prompt.py → sceneSpec. The legacy `motionSpec` on this room (hero `far_smoke`) is inert on this path, and cine_room passes `--no-stage`, so the stale mask never applies either. And there is no `ri`-tagged anvil output on disk, so the "silently re-gate yesterday's clip" skip won't fire.

Against the reject list: no settings change, bounded mover not frame-filling, no zero-return reasoning, no clip accepted, no committed art or hotspots touched, no hand-written prompt, and it isn't AUTHOR_MOVER on an unrendered mover — it's the render that mover has never had.

VERDICT: PASS