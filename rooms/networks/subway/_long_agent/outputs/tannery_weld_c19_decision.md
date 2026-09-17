Read the four evidence files, then checked this room's own state rather than re-deriving anything.

**What I found:**

- The spec already carries exactly one **bounded** mover — `hide_rail`, with `motion.moves`, an authored `vigour` and a `phrase`. Hanging cloth is the ledger's strongest confirmed mover category, and the rail occupies one band right of centre, not the frame.
- Every `at` resolves inside the closed vocabulary (`just left of centre` → 0.36, `just right of centre` → 0.64, etc.) — nothing falls through to `None`.
- `render_motion_prompt` resolves from the spec at 37 words in the house form, naming only the depicted mover. It matches the current motion prompt exactly, so the spec and the prompt cannot have drifted.
- `scene.png` was regenerated and committed today at 15:10 (the `pre_regen3_tunnels` archive), so the still is current. I cropped the mover region and looked: the row of canvas sheets is there, hung singly with gaps and lamplight between, hems lifted clear of vertical and every sheet leaning the same way — the authored vigour rendered faithfully.
- The gate report is `{}` and nothing has been tried this job: no clip exists for this still.

The archived round-2 cycle had this same mover clear every gate on the *previous* still (camera still, glitch 0.042, dead ratio 15.73, return 0.23). The art was regenerated for the tunnel-mouth fix, not for motion, so there's nothing to re-author and no reason to pre-soften a register that already measured at market_price's shipping level. Pipeline step 3 applies: one render at the default.

DECISION: RENDER
WHY: The spec declares one bounded mover with authored vigour, today's committed still plainly depicts that row of canvas sheets blown out of plumb on its rail, the motion prompt resolves cleanly from the spec at the register this mover already gated well at — and no clip exists yet for this still, so the single default render at 3072x1024, end guide 0.70, is the next step.