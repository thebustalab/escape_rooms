I read the four authority files, then verified the room's actual state on disk rather than trusting the handed gate report.

**The gate report is stale.** `state.json`'s `ap_backwind` block shows `attempts: 1`, `clip: …ap_backwind_motion_ri25_looped.mp4`, and a `last_gate` byte-for-byte identical to what I was handed (return 0.69, glitch breadth 0.125/0.125, dead ratio 8.5). The only renders on disk are `ri25*`, timestamped 00:52; cycle 29 ran at 05:09. So this report measures the **pre-pin** render — the very clip the pin exists to fix.

**Cycle 29's pin did land.** `sceneSpec.rigid` on disk now reads `"the viewer's own glider's two wide translucent membrane wings spread across the foreground"`. Running the renderer: `render_motion_prompt(rigid=True)` gives exactly the 57-word prompt I was handed, inside the 61-word register proven safe and far from the 176-word case that returned CAMERA MOVES; `render_prompt(spec)` is **byte-identical to the committed `scenePrompt`**, so `scene.png` is current and no art is at risk.

**I confirmed the defect from the frames myself.** Frame 0 is the clean panorama — the derelict glider is a small dark winged shape out at the right, and the viewer's own two pale translucent wings sit low left and low right. By frame 18 a gridded ochre sail spans the full 3072 px, visibly rooted in those two foreground wings and merged across the centre, burying the ring-current and the derelict. That is the frame-filling mover the pin names, and the gates are blind to it by construction: it arrives and departs, so the return reads healthy and the glitch breadth catches only the onset edge.

The spec carries one bounded mover with an authored vigour that the still depicts, the prompt is compliant and travel-free, the art is current, and `max_attempts_per_room: 2` against `attempts: 1` leaves exactly the one render this needs.

DECISION: RENDER
WHY: The cycle-29 rigid clause is on disk and renders a safe 57-word motion prompt against a byte-identical art prompt, but the only clip and gate report that exist are ri25's from before the pin — so the pin has never been tested and the single remaining step is the one render.