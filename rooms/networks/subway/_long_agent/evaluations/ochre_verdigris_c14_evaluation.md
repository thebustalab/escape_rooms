I checked the room myself rather than going on the worker's word.

**What the files say**

- Room state in _long_agent/state.json is `ochre_verdigris: {art_generated: 1}` — no `needs_still`, no `clip`, and the gate report is genuinely empty. The still at rooms/networks/subway/ochre_verdigris/scene.png is stamped 14:50 today, matching `last_cycle`, so it is current against the spec.
- I ran `render_motion_prompt` on the live spec myself: it resolves cleanly — *"locked-off static camera, zero camera movement. The seep running gently and steadily down the tile face into the channel below. Only that moves; everything else stays perfectly still. Seamless natural loop."* 31 words, one mover, gentle register. The header's "NONE" is the missing .txt fallback, not a missing prompt.
- 3072x1024 and end guide 0.70 are the values already in plan.json (`end_guide: "0.70"`). The worker is restating the configured default, not reaching for a lever.

**What the frames say**

I looked at the panorama in four crops. The seep is really there and really bounded: water runs down a low tile face right of centre, behind the buffer stops, and spills over a lip into a channel at the foot of the wall — a few hundred pixels of a 3072-wide frame, nowhere near frame-filling. Crucially, this room's old fault is absent: there is no ceiling waterfall, so the spec is not naming a mover the art lacks. Lucas's round-3 note also holds — exactly one brick-ringed tunnel mouth at the left, one spiral stair with its single roof shaft, buffer stops with the red lamp against a blind wall at the right, one train.

**One correction to the worker's narration**

"No clip exists" is true of this instance, but .cine_published.json still points ochre_verdigris at ochre_verdigris_motion_ri13_looped.mp4 from 09:09 this morning — a clip made from the pre-round-3 still. That is a stale publish animating art that no longer exists, which makes a fresh render more clearly right, not less. Worth the runner replacing that entry once a survivor is held.

None of the reject conditions fire: no settings search, bounded mover, no zero-return misreading, no acceptance, no hand-written prompt, and AUTHOR_MOVER isn't proposed on an unrendered mover.

VERDICT: PASS