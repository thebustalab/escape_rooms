I've read the four evidence documents and inspected the live room. Here's what I found before deciding:

**The spec is already correct.** `hearth_kettle` carries a proper `motion` block (`moves/vigour/phrase`), so `movers()` sees it and `render_motion_prompt` resolves from the spec — I ran it:

> locked-off static camera, zero camera movement. The plume of steam standing up from the boiling kettle over the hearth fire, and the flames working under it. Only that moves; everything else stays perfectly still. Seamless natural loop.

**The "current motion prompt" quoted in the brief is the stale `.txt` fallback**, not what will actually be used. Since the spec declares a mover, `art_prompt_motion/beacons/whistlegate.txt` is dead weight here — pipeline step 2 makes the spec authoritative. No action needed.

**The still already depicts the bounded mover, and depicts it well.** `scene.png` was regenerated today (Sep 15 00:59) — 8 days newer than `cine_base.mp4`, so the existing clip is stale art and effectively no clip exists. I looked at it at native crop: a black iron kettle hanging on a crane over a live split-wood fire, with a thick steam plume standing up into the ceiling beams. Bounded, not frame-filling, and squarely in the confirmed-mover categories (flame, coals, chimney smoke). The authored vigour ("hard rolling boil, steam standing up thick") landed in the art.

There is nothing to author, nothing to soften (no clip to judge as too lively), and no evidence of a wrong thing moving. The one thing I'd note for later: the spec carries a *second* hearth (`hearth`, right of centre) whose fire and plume are also depicted but which only has a legacy `animate` block, invisible to `movers()`. The prompt's "Only that moves" will be asking it to hold still. That's a question for the gate and Lucas's eye, not a reason to re-author.

DECISION: RENDER
WHY: The spec carries a bounded, well-depicted mover with authored vigour, the spec-derived motion prompt names exactly that mover, and the still is 8 days newer than the only existing clip — so this room has never been rendered from its current art.