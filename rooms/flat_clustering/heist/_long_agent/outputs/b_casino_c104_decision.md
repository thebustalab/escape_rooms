I read the four authority docs, then checked the room's actual state on disk rather than trusting the gate report on the table.

**What I found.** The gate report shown to me belongs to clip `ri98`, baked at 18:54 UTC. The committed `scene.png` was replaced at 19:04 UTC — ten minutes *later*. So that gate measured the superseded art. I looked at both stills side by side:

- **Old still (ri98's conditioning image):** a diffuse haze lying across the whole near half of the room, with only a thin wisp off the cigar. Exactly the room-wide bank cycle 100 diagnosed — and a frame-filling haze is the documented non-mover.
- **Current still (19:04):** one bold, clearly defined ribbon of cigar smoke climbing off the ashtray in three legible coils, confined to a narrow column, the rest of the air clean. That is a textbook bounded mover.

Both prompts resolve clean from the one spec: the art prompt matches the stored `scenePrompt` byte-for-byte (so the still really was drawn from this spec), and the motion prompt names the plume exactly once, at 38 words in the house form — cycle 103's demotion of the stale bank element did what it intended. The runner's own last log line agrees: *"The art prompt is unchanged, so the committed still still matches — only the clip needs re-rendering."*

So nothing is owed to the art. What is owed is the render that has never happened against this still.

DECISION: RENDER
WHY: The 19:04 still depicts the bounded, visibly coiling plume the spec asks for and both prompts resolve clean and consistent from that same spec, but the only clip in hand is ri98 — rendered from the superseded room-wide-haze art ten minutes earlier — so the standing gate report is stale evidence and a single render at the pinned 0.70 is the one thing that can say anything about the current room.

A note for when you look at this one, Lucas: b_casino is the room the ledger records as a **cyclic-flow** case — its smoke scored return 0.00 at both 0.65 and 0.70 and you called it alive with a good loop. So expect the return gate to flag zero again and expect that to mean nothing. The number I'd actually watch is peak amplitude: live cyclic movers have measured 8.06–9.35, dead ones 5.1–5.2, and ri98 on the old haze came in at 3.78. If the new still is doing its job, that figure should climb.