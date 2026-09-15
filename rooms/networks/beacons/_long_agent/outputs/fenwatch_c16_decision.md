I read all four authority documents, then checked the room's actual state on disk rather than trusting the brief.

**What I found.** fenwatch was re-authored a few minutes ago — there's a spec backup at 20:18 labelled `near_movers` and a fresh scene.png at 20:21. The spec now carries exactly one bounded mover, `gutter_pour`, with a proper `motion.{moves, vigour, phrase}` block, so `_has_authored_mover` can see it.

Four checks, all clean:

1. **The still was generated from the current spec.** The stored `scenePrompt` is byte-identical to `render_prompt(spec)` and carries the equirect clause — not one of the two stale cached prompts.
2. **The mover is genuinely depicted.** I looked at the panorama. A lead downpipe at the office corner throws a heavy unbroken rope of white water into a brim-full slate butt that's overflowing down both sides onto the cobbles. Bounded — roughly a tenth of the frame width — hard-edged, high-contrast, and falling water is on the ledger's confirmed-mover list.
3. **The motion prompt resolves from the spec, not the stale file.** `exp_art_prompt.motion_prompt` prefers the spec and only falls through to `art_prompt_motion/` when the spec yields nothing. The prompt quoted in my brief — woodsmoke and river mist — is the old `.txt`, a leftover from the pre-migration art, and it will not be used. The spec emits: *"…the rope of meltwater pouring from the gutter spout into the brimming water butt, churning its surface and spilling over the rim. Only that moves…"* — 38 words, house form, naming only what's depicted.
4. **The seam is sound.** `seam_band` reads frac 0.048, "continues" — inside the accepted range (accepts 0.000–0.044, rejects 0.158 and 0.221). The centred strip confirms it by eye: the drystone wall, the cobbles and the hillside all run straight through the join. No occluder needed.

No clip exists from this art — the newest one, `cine_base.mp4`, is from 9 September and predates the still by five days. The gate report is empty because nothing has been rendered yet. So the spec and the prompt are both right and the room has never been driven. That is RENDER, not an authoring change.

One thing worth flagging for the gate: a pour is **cyclic flow**, not out-and-back. Falling water never returns to its starting configuration pixel-wise, so expect `cine_return_check` to read 0.00 and escalate as ambiguous — exactly as it did on b_casino's smoke and logwood_verdigris' water, both of which Lucas called alive. A zero here is not a death sentence.

DECISION: RENDER
WHY: The spec carries one bounded authored mover, the committed still genuinely depicts it, the motion prompt renders correctly from that spec, and no clip has ever been rendered from this art.