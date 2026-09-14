I've read all four documents and verified the on-disk state.

**What I found:**

- The clip exists: `temp/cine/_art_prompt_exp/heist/b_pawnshop_motion_ri26_looped.mp4`, seed 4242, rendered cycle 26 at 20:33–20:42.
- Camera gate: **pass** — `frame0_corr 0.946`, `landmark_drift_px 0`, reported as "one object moving (camera still)".
- Return gate: **pass** — 0.14, non-zero and squarely inside the shipped range (lantern 0.13, emporion 0.17, quay 0.23). No ambiguity to escalate.
- Glitch gate: **pass** — breadth 0.0 on *both* readings (raw and brightness-normalised), against a 0.70 threshold that requires both.
- `cine_room` already filed the verdict: `"survived gates — needs Lucas's eye"`.

**On "motion prompt: NONE":** that is the *fallback file* field, not a prompt-less render. `cinemagraph_tools/art_prompt_motion/heist/` holds only a_gallery, a_vault, b_casino, b_docks — no b_pawnshop. Per the pipeline's step 2, the spec is now the single source of truth and the file is only a fallback for a room whose spec declares no mover. The `beads` element carries `motion.{moves, vigour, phrase}`, so `render_motion_prompt` built the prompt from `"the beaded curtain swaying and settling in the draught"`. That is the correct, non-drifting path.

The mover is bounded and doorway-sized, the depicted vigour is authored, every gate cleared, and no metric may approve. There is nothing left for this loop to do.

DECISION: HOLD
WHY: The cycle-26 render at seed 4242 cleared all three reject-only gates — camera still with zero landmark drift, return 0.14 inside the shipped 0.13–0.51 band, glitch breadth 0.0 on both readings — on a spec-derived motion prompt naming a bounded depicted mover, so the clip now waits on Lucas's eye rather than on any further authoring or drive change.