I checked the spec and the runner code rather than the worker's summary.

**The decisive fact the worker missed.** `_has_authored_mover` (`Utilities/long_agent/long_agent.py:3549`) requires an element with `motion.moves` **and** `motion.vigour` **and** `motion.phrase`. Dumping the committed spec:

```
tarp | motion= None | animate= {'motion': '…flapping and snapping…', 'loop': 'crossfade'}
```

Every element has `motion = None`. The tarp's vigour lives in a legacy `animate` block. So at `long_agent.py:3847` the RENDER branch falls straight into:

> `b_docks: RENDER refused — the spec has no element with motion.moves and a vigour.`

The worker's central claim — "the spec already satisfies the one thing that governs animatability" — is false as the pipeline measures it. It inspected the `desc` text and the cached art prompt, both of which do carry the tarp, but never checked the field the gate actually reads.

**This is a repeat of a failure recorded in the worker's own instance.** `_long_agent/state.json` and `progress.md` show a_vault hitting exactly this at 19:14 UTC, and cycle 2 fixing it with AUTHOR_MOVER — "it lives in a legacy `animate` block that `_has_authored_mover` cannot see, so RENDER is refused unconditionally." b_docks has the identical shape.

**Cost of passing it.** `attempts` increments on every decision beat (`long_agent.py:3723`), and `max_attempts_per_room` is 2. Acting on this spends one of the two attempts on a log line and no render. Failing it spends the same attempt but puts the reason into `last_eval`, so attempt 2 can go straight to the correct move.

**What's genuinely right in the decision, for the next cycle's benefit:** the motion prompt at `cinemagraph_tools/art_prompt_motion/heist/b_docks.txt` is in house form and names the tarp alone; the committed still matches the cached prompt; and the tarp is a bounded, not frame-filling, mover. None of the listed reject criteria fire — no settings change, no frame-filling mover, no zero-return reasoning, no clip accepted, no hand-written art prompt. The correct next action is AUTHOR_MOVER migrating the existing `animate` text into `motion.{moves, vigour, phrase}` — a pure field migration that, as a_vault verified, re-renders both prompts byte-identically and needs no new art, though the runner will still set `needs_still` and require a human touch of `scene.png`.

VERDICT: FAIL