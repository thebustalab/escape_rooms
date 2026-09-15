I read the four evidence files, then checked the clip's provenance on disk rather than trusting the gate summary on the table.

**The gate report is stale.** The timeline is unambiguous:

| time (2026-09-14) | event |
|---|---|
| 23:08:22 | `scene.png` committed |
| 23:10:05 | cycle 50 decision: RENDER |
| 23:20:25 → 23:21:38 | `anvil_motion_ri50.mp4` rendered and baked |
| **23:29:11** | **cycle 52 decision: PIN_NON_MOVERS — the rigid clause lands** |
| 23:31:42 | evaluation PASS, state written |

The only anvil clip on disk is `ri50_looped.mp4`, rendered **eight minutes before the pin existed**, and `rooms.anvil.clip` still points at it with `attempts: 1`. The numbers on the table (return 0.0, breadth 0.625, peak 10.04) are the very numbers cycle 52's own decision quotes as the *evidence for* pinning — so holding on them would hold the pre-fix render and discard the fix.

**The pin is correctly in place and costs no art.** `scenario.json` carries `rigid: "the shattered rock pavement and the mountains behind it, every object standing on the rock"`, two items. `render_motion_prompt(rigid=True)` gives 64 words — under fenwatch's proven 66, far from a_opera's 176-word camera-drift regression — and matches the prompt on the table byte for byte, so the runner is already resolving rigid automatically. `rigid` appears nowhere in `render_prompt`, only in `render_motion_prompt` (`authoring_v2/scene_spec.py:406`), so the art prompt is untouched and the committed still stands.

**The spec is otherwise right.** One bounded mover with authored vigour (`fuel_tarp`, the flogging tarpaulin corner); `heat_shimmer` and `depot_smoke` carry legacy `animate` blocks only, invisible to `_has_authored_mover`, so the prompt names the tarpaulin and nothing else. Settings on ri50 were the pipeline default (3072x1024, eg 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242) — nothing to change. `max_attempts_per_room` is 2 and anvil has spent 1, which is exactly enough.

This is fenwatch's cycle 20 again, on the same run: *"the rigid pin landed in the spec at 20:51 but the only clip on disk is ri16 from 20:37."* That render produced fenwatch's held clip.

DECISION: RENDER
WHY: The two-item rigid pin landed at 23:29 but the only clip on disk is ri50 from 23:20, so the gate report on the table is the pre-fix render — the spec, the committed still and the 64-word pinned motion prompt are all correct and no clip has yet been rendered from them.