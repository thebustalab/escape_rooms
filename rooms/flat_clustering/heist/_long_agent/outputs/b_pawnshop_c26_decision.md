I read the four evidence files, then checked the room's actual state on disk.

**What the evidence says about this room:**

- `rooms/flat_clustering/heist/b_pawnshop/scene.png` exists (3072x1024, committed 2026-09-05, verdict `hold`).
- The spec already carries a bounded mover: `beads`, with a full `motion` block — `moves: true`, a vigour string, and a phrase. So `_has_authored_mover` can see it (this room was in the 2026-09-13 migration).
- Looking at the still at native resolution: the beaded curtain is genuinely depicted, twice — the shop doorway at left and the street doorway at far right. Both are doorway-bounded, not frame-filling, and hanging fringe is the strongest entry in the confirmed-mover menu (p95 76.8).
- "Motion prompt: NONE" is not a blocker. `exp_art_prompt.motion_prompt` falls back to `scene_spec.render_motion_prompt`, which builds the house-form prompt from `motion.phrase`: *"locked-off static camera, zero camera movement. The beaded curtain swaying and settling in the draught. Only that moves; everything else stays perfectly still. Seamless natural loop."*

So the mover exists, the still depicts it, no clip has ever been rendered, and the gate report is empty. ADJUST_VIGOUR and SOFTEN_PROMPT are both defined as responses to a clip that doesn't exist yet, and re-authoring a committed, judged still on speculation would throw away the seam triage for nothing. Step 3 of the pipeline is one render at the default.

DECISION: RENDER
WHY: The spec carries a bounded, doorway-sized depicted mover with authored vigour and phrase, the committed 3072 still shows the beaded curtain clearly, and the motion prompt derives from the spec — so the only thing missing is the single render at end guide 0.70.

Spoken version: this room is ready to go. It already has a beaded curtain hanging in the doorway, which is exactly the kind of bounded mover the whole pipeline says you need — hanging fringe is the best-performing thing in our records. Nothing has been rendered yet, so there's nothing to soften or re-author. I've sent it for its one render.