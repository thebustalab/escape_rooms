I've read the four authority documents and inspected the room. Here's what I found.

**The spec already carries a bounded authored mover.** The `porthole` element has a full `motion` block — `moves: true`, `vigour: "the slow swell rising and falling close beyond the glass"`, `phrase: "the slow sea swell rising and falling beyond the porthole glass"` — so `_has_authored_mover` sees it and `render_motion_prompt` resolves from the spec rather than a fallback file:

> locked-off static camera, zero camera movement. The slow sea swell rising and falling beyond the porthole glass. Only that moves; everything else stays perfectly still. Seamless natural loop.

**The committed still actually depicts it.** I opened `b_stateroom/scene.png` (3072x1024, triaged `hold`, built from `l1_b_stateroom_1.png`). The porthole sits at the left with open sea behind the glass — a textured, choppy horizon with visible wave crests, occupying roughly 6% of the frame. That is the "water in one channel" archetype: bounded, not frame-filling. The judge note even remarks on the porthole sea's tone, confirming it was rendered as real water and not a dark disc. The stored prompt at build time already carried the vigour clause, so the still is not stale against the current authored intent.

Two things I checked and deliberately did **not** act on. The stored `scenePrompt` predates the equirect/style/edge-discipline clauses — this is one of the known stale-prompt rooms — but that is a seam-and-look concern, not an animatability one, and regenerating would discard a human-triaged still to fix something the motion loop was not asked about. And the desk charts and table plan are the kind of paper that sometimes wanders; the pipeline's fix order pins non-movers only after a clip shows them moving, so pre-emptive pinning would be guessing.

Every predecessor room in this plan (briefing, a_opera, a_townhouse, b_pawnshop) reached HOLD on exactly this shape — one render, no re-authoring — and b_stateroom has no entry in `state.json` at all, so no attempt has been spent.

DECISION: RENDER
WHY: The sceneSpec carries one bounded mover with an authored vigour that the committed 3072 still visibly depicts as open sea beyond the porthole glass, the motion prompt derives from that same spec and names only that mover, and no clip exists yet — so the single render the pipeline allows is the next step.