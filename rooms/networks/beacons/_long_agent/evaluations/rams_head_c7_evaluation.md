I checked the frames, the spec, the room's own judge file, and the runner's merge code rather than the worker's summary.

**What's true:** the live spec really does carry a stale lantern phrase on `cirque_tarn` (migration artefact — vigour says cat's-paws, phrase says swinging lantern). That mismatch is real and would poison a render. The merge mechanic the worker relies on is also real: `long_agent.py:4160` matches by `at`, so `"to the left of centre"` merges into `cirque_tarn` and deep-merges `motion`.

**What's false — and decisive:** "The still depicts no mover at all." The committed `scene.png` puts a large, ice-rimmed black tarn front and centre-left, and this room's own `cine_base.judge.json` scores `tarn_surface` **alive, p95 15.63**, alongside `horn_meltwater` and `gap_grass` alive, on a clip whose only flag was a background-swing warn for a human eye. The depicted mover is not hypothetical; it has rendered and it animates.

That makes this an AUTHOR_MOVER against a mover that has never been rendered *in this loop* (`Clip: none yet`, gate `{}`) and that, on the wider record, renders alive. The sibling rooms in this same run — `fenwatch`, `spindle` — correctly chose RENDER in exactly that position.

**Cost the worker doesn't account for:** the art prompt changes, so `needs_still` fires and the runner spends a paid generation to replace a panorama Lucas accepted on 2026-09-03 (`seam.accepted: true, acceptedBy: "lucas 2026-09-03"`). The merge also overwrites the tarn's `desc`, demoting "filling the whole floor of the cirque" to a trailing clause, and discards its authored cat's-paws vigour. The cited 3-of-3 experiment (`notes/reauthor/beacons__rams_head.spec.json`) put the lantern at *"just left of centre"* as its own element and lit; this is not that configuration, so the proof doesn't transfer.

The identified bug has a free fix the worker passed over: an `ADJUST_VIGOUR` fragment rewriting only `motion.phrase` on `cirque_tarn` to name the tarn leaves `render_prompt` byte-identical, sets no `needs_still`, keeps the accepted still, and clears the drift — then render.

VERDICT: FAIL