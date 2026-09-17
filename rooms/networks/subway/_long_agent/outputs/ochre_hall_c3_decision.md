I read the four evidence files, then checked this room's actual state on disk.

**What I found**

- `rooms/networks/subway/ochre_hall/scene.png` was regenerated today at 14:08, and `_long_agent/state.json` records `ochre_hall: {art_generated: 1}` — so the still is fresh **from the current spec** (the round-3 tunnel-mouth fix), not stale.
- The spec carries exactly one bounded mover: `dust_sheeting`, with a full `motion` block (`moves`/`vigour`/`phrase`). `vault_shafts` has only a legacy `animate` block, which `_has_authored_mover` and `render_motion_prompt` both ignore, so there is no second mover competing.
- I rendered the motion prompt from the spec through `scene_spec.render_motion_prompt` — it reproduces the stated prompt byte for byte, 40 words, house form, naming only the depicted mover.
- The vigour register here is the one the ledger already proved on **this exact room**: ochre_hall's gentle arm measured 9.91 in the three-way vigour ladder and Lucas's verdict was "Ochre and crown worked."

So the spec is right, the prompt is right, the art matches both, and no clip exists for this still. Nothing to re-author and nothing to dial.

DECISION: RENDER
WHY: The spec carries one bounded mover with authored vigour, the still was just regenerated from that same spec, the motion prompt derives from it cleanly at the gentle register this room has already animated well at — and no clip exists yet to judge.