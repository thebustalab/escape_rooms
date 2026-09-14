## Verification

I checked the worker's three load-bearing claims directly rather than trusting them.

**1. Cycle 65's pin applied.** `authoring.sceneSpec.rigid` on `a_opera` now reads *"the heavy velvet portière drapes hanging at the two doorways on the right, which never draw, sweep or swing across either opening…"* and `render_motion_prompt(spec, rigid=True)` emits it. Confirmed.

**2. The `needs_still` block is spurious.** `scene_spec.render_prompt()` (authoring_v2/scene_spec.py:136) reads `setting`, `seam`, `elements[].desc`, `atmosphere`, `negatives` — it never touches `spec["rigid"]`, and the sweep's `if e.get("desc")` filter skips cycle 64's inert element. I ran it: the art prompt is byte-identical with and without both, and the committed `scenePrompt` equals `render_prompt(spec)` exactly. So `scene.png` (Sep 13 22:24) *is* the current art. Meanwhile `spec_edited_at` = Sep 14 07:39 > png mtime, so the self-clear at long_agent.py:3784 will not fire, and the RENDER branch at :3945 would park the room with a message telling Lucas to regenerate a panorama that is already correct. `attempts` is 1 against `max_attempts_per_room: 2` — one render left, as stated.

**3. `to_hotspots` genuinely crashes.** `KeyError: 'id'` on the live spec, from `base = {"id": e["id"], …}` at scene_spec.py:240 hitting the inert `{"rigid": …}` element. Reproduced.

**4. The frames back the diagnosis.** Between frame 0 and frame 60 the two right-hand portière drapes at x≈0.72 and x≈0.84 swing inward and narrow both lit doorways, while the authored swag at x≈0.20 barely moves — the defect the pin targets. The still itself is sound: seam matches across the crimson flock, lighter and writing-slope both present, no text.

Against the reject list: no settings change, no frame-filling mover, no zero-return reasoning (return is 0.43), no clip accepted, nothing written to committed art or hotspots, no hand-written art prompt, not AUTHOR_MOVER. Since PARK itself sets `rs["parked"]`, the room-selection skip at :3756 will thereafter precede the self-clear — so the three-key deletion is the right remedy and `touch scene.png` alone would indeed stop working once this lands. The one slack detail is that `parked` isn't in the state file yet; deleting a key that isn't there is harmless.

The decision is correct and the handoff to Lucas is specific and actionable.

VERDICT: PASS