I read the four authority files and then checked anvil's actual state on disk rather than trusting the brief's table.

**What I found.** The motion prompt shown in my brief is stale — it's the old text file at cinemagraph_tools/art_prompt_motion/beacons/anvil.txt, which the renderer only uses as a fallback. anvil's spec declares a mover, so the live prompt comes from the spec.

The timeline: ri96 rendered and was held at 12:24 UTC, the 360 page went up at 12:41, and Lucas's note — the clip "weirdly merged the tarpaulin with the book on the table" — landed after that. The disambiguation was then applied to the spec at 12:47 UTC, twenty-odd minutes *after* the only clip on disk was rendered. Two changes, both motion-only: the phrase now locates the subject on the left and ties it to the fuel stack, and the rigid clause names the writing-slab and its filed papers by name instead of a vague catch-all about pavement and mountains.

I verified the important safety property directly: render_prompt on the live spec is byte-identical to the committed scenePrompt, 7056 characters both ways, and fuel_tarp's desc and vigour are untouched. So the committed panorama still stands and no new art is implied. The live prompt resolves through exp_art_prompt at 69 words, one named mover, a two-item rigid pin — well short of the 176-word length that made a_opera's camera drift.

So the wrong-subject fix is already authored and has never been rendered. Nothing is in flight, the room's attempt count is reset, and seed stays at 4242 so the disambiguation isn't confounded with a roll.

DECISION: RENDER
WHY: The wrong-subject fix is already in the spec as a locating phrase plus a two-item rigid pin, the art prompt is byte-identical to the committed still so no new panorama is implied, and the resulting 69-word prompt has never been rendered — the only clip on disk predates that edit by twenty minutes.