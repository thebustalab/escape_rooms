Checked the clip and spec myself rather than the worker's summary.

**What the frames show** (looped clip, 3072×1024, 61 frames at 24 fps):
- Camera is genuinely still — vault ribs, cast-iron spiral, traffic desk and platform edge sit pixel-stable across frames 0/40/56/60.
- The canvas dust-sheeting on the platform rail is the only thing moving, and it ripples and slumps gently between its ties. That is the authored mover, at the authored register.
- Everything else the spec pins (one tunnel mouth left, buffer stops and red lamp right, wheels on railheads, car floor level with the platform) holds steady frame to frame.

**On the glitch reading, which is the one thing worth a second look:** the raw render really does break at its tail — at frame 70 of 73 the whole left run of canvas has vanished, exposing bare ballast. That is what `at_pct: 93.1` is pointing at. But the report's `frames: 73` is the raw length, and the looped deliverable is 61 frames: the loop trims that tail off, and the canvas is present and intact through every frame of the clip actually under judgement. So the worker's *diagnosis* of the spike (a brightness-normalisation artefact, `whistlegate`-style) is not what is happening here — but the conclusion is right for a better reason than the one given, and the documented both-readings-≥0.70 rule doesn't fire on raw 0.167 either way.

The rest checks out: dead gate comfortably alive (20.5 / 19.36), `return` 0.23 is non-zero so no ambiguous-zero escalation, and the vigour ladder it cites is corroborated on disk — `ochre_hall_motion_vig_V1_slack / V2_gentle / V3_gale` were actually rendered for this room on Sep 12, so the gentle-rung comparison isn't invented.

Against the reject list: no settings lever, no frame-filling mover, no zero-return-as-dead, no acceptance and nothing written to committed art or hotspots, no hand-written art prompt, and no AUTHOR_MOVER on an unrendered mover. HOLD is the conservative action and the correct one — the clip goes to Lucas's eye, which is where a gate-surviving clip belongs.

One thing for that eye, outside the gate's scope: the committed still's sheeting runs most of the platform rather than the "couple of metres, one distinct bounded object" the spec authored. It animates fine, but it is a drift from the written intent and only a human can call whether it matters.

VERDICT: PASS