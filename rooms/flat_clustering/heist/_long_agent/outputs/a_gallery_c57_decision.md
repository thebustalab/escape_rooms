I verified every load-bearing fact on disk rather than trusting the handed-in context, which was empty (`gate report: {}`, `tried: []`) and is wrong.

**What's actually on disk:**

- The spec's dust sheet is a bounded mover with **both** down-levers already pulled — `motion.vigour` = "barely stirring… very gently in a slight draught", `motion.phrase` = "breathing very gently, barely lifting at one corner". Both answer Lucas's "too aggressive" note; `other_cases` answers his "cases all empty" note.
- `render_prompt(sceneSpec)` is **byte-identical** to the committed `authoring.scenePrompt`, and `scene.png` (22:23:56) postdates it — the still came from this exact spec.
- The motion prompt I was shown is the stale `art_prompt_motion/heist/a_gallery.txt` fallback. The spec declares a mover, so per step 2 the spec wins; `render_motion_prompt` returns the softened phrase.
- **A render from this exact state already exists**: `a_gallery_motion_ri35_looped.mp4`, baked 22:37:48 (after the still), seed 4242, end guide 0.70, 3072x1024, 73 frames, 8 steps, cfg 2.0 — the pipeline default, verified in its `params.json`.
- Its gate line: `camera: "still"`, breadth 0.0 **and** breadth_normalised 0.0 (nowhere near the 0.70/both-readings glitch bar), return 0.00 → the documented dead-or-cyclic ambiguity. Verdict recorded: *"survived gates — needs Lucas's eye."*

**And it has already been adjudicated three times.** c37 ADJUST_VIGOUR → REVIEW (premise confounded: ri11 and ri35 are different stills). c38 ADJUST_VIGOUR → FAIL, on direct frame measurement showing the sheet band arcing 0 → 5.31 → 3.97, the most active region throughout — the mover is alive, and the 0.00 return is a local arc swamped by ~3.5 grey levels of whole-frame creep, the third instance of that metric's known false-dead. c39 → PARK, PASSed. c56 proposed RENDER and was FAILed for missing ri35.

The room stands at 1 of 2 renders. Spending the last one would reproduce a clip that already exists, and `state.json`'s own restart note names this room specifically: a low return here *is* the intended outcome of the deliberate softening, "HOLD it for his eye rather than adjusting vigour again."

DECISION: HOLD
WHY: The current spec's render, ri35, already exists at the pipeline default and cleared every reject-only gate with direct frame measurement confirming the dust sheet alive, so the remaining question — whether the deliberate softening overshot — is an aesthetic call that belongs to Lucas's eye, not to another render.

One item from c39's park is still unanswered and worth carrying to the review page rather than acting on: everything outside the sheet drifts monotonically ~3.5 grey levels over the loop. The camera gate calls it still and it is probably an invisible exposure shift — but if Lucas *can* see it, the fix is a `motion.still_as` rigid clause on the marble walling, piers and vitrines, not a vigour change.