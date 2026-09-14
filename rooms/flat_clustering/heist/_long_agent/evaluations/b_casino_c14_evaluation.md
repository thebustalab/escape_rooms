I checked the decision against the live tree rather than the write-up.

**What verified true:**

- **The mover is real and authored.** Live scenario.json for b_casino carries smoke with `motion.moves`, `vigour` and `phrase` all set, so `_has_authored_mover` (Utilities/long_agent/long_agent.py:3549) returns True and RENDER will not be refused at line 3910.
- **Bounded, not frame-filling.** `movers(spec)` returns exactly one element — smoke, a bank under one low table lamp over the near baize. The ledger's own calibration row (notes/cinemagraph_ledger.md:1070) confirms it empirically: *"distinct per seed; only the smoke moves"*, in all 16 cells.
- **The motion prompt is derived, not hand-written.** I ran the live spec through `render_motion_prompt` and it comes out **byte-identical** to the committed cinemagraph_tools/art_prompt_motion/heist/b_casino.txt. And RENDER doesn't write prompts at all — it goes straight to `_launch_cine_room`.
- **The zero-return note is correct and pre-emptive.** Ledger line ~1299 has b_casino at 0.00 / 0.00 labelled **cyclic flow (smoke)**, with the retraction of the "3 of 5" false rejection right below it. This matches the loop's own review_note. The worker flags it as escalate-not-dead, which is the right reading.
- **No clip in this loop.** b_casino has no entry in state.json; the 76 artifacts on disk are the cal50/60/70/80 grid, not a full-res run.
- **No settings change.** The 0.70 comes from plan.json's fixed `end_guide` — the worker isn't proposing a lever.

**One thing I checked that could have sunk it, and didn't:** today's animate→motion migration rewrote the smoke element. I diffed it against the backup — it split the old desc into desc + vigour verbatim, same noun, same place, and left scenePrompt untouched. So the Sept 5 still genuinely depicts the mover its motion prompt names. Done-criterion 3 holds.

**Two notes for whoever reads this next, neither a reject:**

1. `market_price` in the worker's write-up is a **room** in the ledger table, not a function — "market_price returns 0.23 and ships" is a room-to-room analogy dressed up as an API call. Sloppy phrasing over a real ledger row, not a fabrication.
2. The committed scenePrompt is 1664 chars; the current renderer emits 3023. That divergence is the same one that sank the b_docks cycle — but it only bites on an **authoring** decision, which rewrites scenePrompt. RENDER never touches it. If b_casino comes back needing a re-author, that overwrite risk is live again on an un-versioned tree.

VERDICT: PASS