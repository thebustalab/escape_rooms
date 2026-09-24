I've read the four authority documents and verified the room's actual state.

**What I checked**

- **The clip exists and is complete**: `cockpit_motion_ri3_looped.mp4`, rendered 07:14 today from the `scene.png` committed at 07:01 — so it is a clip of the *current* spec, not a stale generation. Params sidecar confirms the pinned recipe exactly: 3072x1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4711, no LoRA, no speed clause.
- **Camera gate — pass.** `camera: "still"`, `frame0_corr` 0.982, `landmark_drift_px` 0, `loop_jump` 4.8.
- **Glitch gate — pass.** Raw `breadth` **0.50**, normalised 0.708. The rule is reject only when **both** readings exceed 0.70; the raw reading is well under. This is precisely the case the two-reading rule was built for — the city mover *is* a light that brightens and dims globally, which is what inflates the normalised reading (the `whistlegate` false-positive pattern). Not a rejection, and no re-roll is warranted.
- **Return gate — pass.** 0.48, inside the 0.13–0.51 band the shipped Egypt clips occupy. Not the ambiguous zero.
- **Dead check — pass.** `dead: false`, ratio 8.03, peak 9.45.
- **The filmstrip agrees with the numbers.** The `|mid − frame 0|` difference panel is near-black across the whole dash, sampler globe, reading-pane and override cells — the foreground is pixel-stable and stays sharp, as the guidance requires. The energy sits in the storm on the right (lightning) and, more softly, in the lit city on the left. Both authored movers are doing what their phrases asked, nothing else is. Last frame closely matches frame 0, so the loop closes.

Nothing here calls for re-authoring, and the guidance forbids it regardless — the two light movers are the approved recipe, already blessed by Lucas on this room at this seed. The clip is not too lively, nothing that should be still is moving, and it is not dead.

DECISION: HOLD
WHY: The clip renders from the current spec at the pinned seed 4711 / end guide 0.70 and clears every gate — camera still, raw glitch breadth 0.50 against a both-readings-≥0.70 rule, return 0.48, not dead — with the filmstrip showing motion confined to the city and the storm while the dash stays sharp, so it belongs in front of Lucas's eye rather than back in the loop.