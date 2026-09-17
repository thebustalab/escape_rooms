I read the four evidence files, then checked this room's actual state on disk.

**What's on disk for `logwood_woad`:**
- `logwood_woad/scene.png` (Sep 17 15:29) was generated from the **current** spec — `_scratch/.l1prompt_logwood_woad.txt` (15:28) carries the round-3 stair wording and the current `river_wall` line, so the art is not stale against the spec.
- Seam record: `screened`, ratio 2.36, `seamBandRun` 0.007, `needsWork: false` — well inside the accepted 0.000–0.044 band, no occluder needed.
- The spec declares **exactly one** mover, `river_wall`, with both `motion.vigour` and `motion.phrase` authored, so `_has_authored_mover` sees it and `render_motion_prompt` resolves from the spec: *"locked-off static camera… The thin film of water on the curved retaining wall sliding down it very slowly and steadily. Only that moves…"* — 38 words, house form, already in the soft register.
- The still plainly **depicts** that mover: a lit teal sheet of water running down the curved brick above and behind the train, bounded left and right by the arch ribs. One surface, one band — the same water-on-a-wall family as sibling `logwood_verdigris`, which is one of Lucas's six winners.
- **No clip exists for this art.** `state.json` has `{"art_generated": 1, "retries": 1}` — no `attempts`, no `history`, no `clip`, empty gate report. The only recent renders (`ri87` 09-16 03:00, `ri44` 09-17 10:38) both predate the 15:29 art and belong to the round-2 panorama.

So the last cycle's re-authoring proposal was argued from the still alone and was correctly rejected: the authored mover has never been put in front of the clip model. Re-authoring art that has never been rendered would spend a generation to answer a question one render answers, and the loop's own rule is that *dead* is a verdict from a clip, not from a picture.

DECISION: RENDER
WHY: The spec carries one bounded mover with authored vigour, the committed still depicts it and was generated from that same spec, the seam is clean and the motion prompt resolves cleanly at the gentle register — and no clip has ever been rendered from this art, so the single default render at 3072x1024 / end guide 0.70 is the next step.