The runner should act on this RENDER decision. I checked the files myself instead of relying on the worker's description.

- **The mover is in the spec.** In `scenario.json`, `still_flood` now has cycle 3's `motion` block (with `moves: true` and a short motion phrase). The old `animate` block is still there beside it.
- **The still shows it.** `scene.png` is 3072×1024 and was written at 2026-09-17 22:48, after cycle 3. The black pool on the left has clear concentric ripple rings, and the amber lamplight on it breaks into long wavering streaks. The pool stays inside the sunken left half of the floor, below the flood-door steps. The door, steps, piers, panel, ladder and arch all look fixed, which matches the spec's list of things that should stay still. Both far edges are plain dark wall, so the seam should hold.
- **Nothing has been rendered from this still yet.** Every clip file on disk (`cine_base*.mp4`) is from 2026-09-01, and the gate report is empty. Rendering now is the right next step; authoring another mover would not be.
- **It breaks none of the rejection rules.** It changes no settings. The mover is a bounded pool, not something that fills the frame. It doesn't use a zero return as evidence, accepts no clip, writes nothing into the committed art or hotspots, and doesn't hand-write a prompt.

One thing for the runner to know: the old patch box in `cine_base.patches.json` (x 0.03–0.22) covers only part of the new pool, which reaches about x 0.36. If the render reuses that box instead of making a new one, the right-hand part of the ripples won't animate. This doesn't block the render.

VERDICT: PASS