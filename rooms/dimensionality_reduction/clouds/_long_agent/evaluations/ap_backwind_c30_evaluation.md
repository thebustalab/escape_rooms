I verified this against disk and the frames rather than the worker's account.

**Timeline — the gate report is stale, as claimed.** `state.json` `last_cycle` is `2026-09-23T05:09:06Z` = 01:09 EDT; the only renders on disk are `ri25*`, written 00:52 EDT. The handed gate report is byte-for-byte the `last_gate` in `rooms.ap_backwind` (return 0.69, glitch 16.85/0.125/0.125, dead 8.5/12.17). So it measures the pre-pin clip. The worker's "05:09" is the UTC stamp, not a fabrication.

**The pin is on disk and renders clean.** `authoring.sceneSpec.rigid` is a string: `"the viewer's own glider's two wide translucent membrane wings spread across the foreground"`. Running the real renderer from `authoring_v2/scene_spec.py`: `render_motion_prompt(spec, rigid=True)` is 57 words, locked-off, travel-free, and matches the quoted prompt verbatim; `render_prompt(spec)` is byte-identical to the committed `scenePrompt` (10237 chars, equal), so the still is not stale and no art is at risk.

**The defect is real and the remedy is aimed at it.** I pulled frames 0/18/36 myself and compared against `ap_backwind/scene.png`. The committed still is clean: the viewer's two pale membrane wings sit low-left and low-right, and the derelict glider is a small dark winged shape at roughly x≈0.78, y≈0.23 — a genuinely bounded mover that the still depicts. By frame 18 a gridded ochre sail spans the full 3072 px, rooted in those two foreground wings and merged across the centre, burying the ring-current and the derelict; it is still there at frame 36. That is exactly the frame-filling intruder the rigid clause names, and it explains the healthy-looking gates.

**Budget.** `max_attempts_per_room: 2` against `attempts: 1` leaves one render (`budget_left` at long_agent.py:4240 reads `attempts`, not `retries`); `retries: 2` is far below the cap of 8, so nothing is near parking.

No rejection criterion fires: no settings change, the mover stays the small derelict wing rather than a frame-filling one, no zero-return misreading, no clip accepted, nothing written into committed art or hotspots, the art prompt is rendered from the spec rather than hand-written, and this is not AUTHOR_MOVER. The pin has never been tested, and one render is exactly what tests it.

VERDICT: PASS