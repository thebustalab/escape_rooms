I checked the worker's claims against the files rather than its summary.

**Verified:**

- **The mover is real in the art.** Looked at `rooms/networks/beacons/sisters/scene.png` (3072×1024, Sep 14 22:00): the marker-flag line on two iron stakes is there, left of centre, near and large — roughly x∈[0.08, 0.31], lower half of frame. **Bounded, not frame-filling.** No drift between spec and still.
- **The resolved motion prompt is the flags, not the cloud.** Ran `exp_art_prompt.motion_prompt()` on the live record: *"locked-off static camera, zero camera movement. The row of marker flags stirring gently along their cord, the nearest ones rippling slowly rather than snapping. Only that moves…"* — 33 words, house form, already in the soft register.
- **`col_cloud` carries only a legacy `animate` block, not `motion.{moves,vigour,phrase}`**, so `_has_authored_mover` cannot see it and it is correctly absent from the prompt. The frame-filling cloud river — hood's known 3072 failure — is not what gets driven.
- **The art prompt is generated, not hand-written:** `authoring.scenePrompt == scene_spec.render_prompt(sceneSpec)` is byte-identical and carries the EQUIRECTANGULAR clause.
- **No clip exists for this art:** `cine_base.mp4` is Sep 7, the still is Sep 14. Gate report empty.

**One thing I chased down that the worker didn't mention, and it holds anyway:** `authoring.motionSpec` is stale — its hero is `cloud_river` and its negatives ban *"flags, pennants, bunting"*. That block feeds `cine_stage.render_state`, and if the runner rendered through `cine_scenario`/`_iterate_render` it would suppress the very flags the spec wants moving. But the live loop is `cine_room.py`, which shells `exp_art_prompt.py --arms motion` (line 137) with the short camera/quality negative. The stale motionSpec is off the render path. Worth cleaning up later; not a blocker now.

No reject condition fires: no settings change, bounded mover, no zero-return argument, no clip acceptance or scenario.json write, no hand-written prompt, and RENDER is not AUTHOR_MOVER.

VERDICT: PASS