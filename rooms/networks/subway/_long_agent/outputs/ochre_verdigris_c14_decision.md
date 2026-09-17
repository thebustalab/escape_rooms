Read the four authority files, then checked this room's actual state rather than trusting the header.

**What I found**

- The spec already carries exactly one bounded mover: `seep_channel`, with `motion.moves`, an authored `vigour` ("fed by a steady seep down the tile face above it") and a `phrase`. It is bounded, not frame-filling, and falling water is a confirmed mover category in the ledger.
- The motion prompt is not actually missing — it resolves cleanly from the spec via `render_motion_prompt`, at 32 words in the house form: *"locked-off static camera, zero camera movement. The seep running gently and steadily down the tile face into the channel below. Only that moves; everything else stays perfectly still. Seamless natural loop."* The "NONE" in the header reflects the absent .txt fallback, which the 2026-09-13 one-spec-two-consumers change made irrelevant.
- The still at rooms/networks/subway/ochre_verdigris/scene.png was regenerated today at 14:50 from the current spec (state.json: `art_generated: 1`, no `needs_still`), and it satisfies Lucas's round-3 review note — one tunnel mouth at the left only, buffer stops with the red lamp at the right, one train, spiral stair single. I looked at it: the seep is genuinely depicted, a bounded sheet of water running down the low tile face into a channel at the foot of the wall on the right. This is the room whose past fault was an invented ceiling waterfall from a motion spec naming a mover the art lacked; that mismatch is not present now.
- No clip exists, gate report is empty, nothing tried.

So the art and the prompt are both right and there is nothing to judge yet. No re-authoring, no vigour change, no seed or end-guide question arises.

DECISION: RENDER
WHY: The spec declares one bounded mover with authored vigour, today's committed still plainly depicts that seep as a bounded fall of water, the motion prompt resolves from the spec at the gentle register, and no clip exists yet — so the single default render at 3072x1024, end guide 0.70, is the next step.