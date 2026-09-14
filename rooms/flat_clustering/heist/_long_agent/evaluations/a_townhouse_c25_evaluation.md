**Independent check of the clip, not the worker's description**

I pulled frames 0/18/36/54/72 out of `a_townhouse_motion_ri23.mp4` (3072×1024, 73f, 24fps — matches the canonical recipe in `a_townhouse_motion_ri23.params.json`) and looked at them, then measured the motion field.

- **The still depicts the mover.** Frame 0 shows the tall sash windows with floor-length net curtains just left of centre — the `nets` element is really in the art, not just in the spec.
- **The clip is alive and the mover is bounded.** Per-column mean abs-diff against frame 0, in sixteenths of the width: `0.9 1.0 1.1 0.9 2.5 9.8 12.8 15.6 3.9 2.7 2.2 1.7 1.4 1.2 1.0 0.9`. All the energy sits in blocks 5–7 — exactly "just left of centre" — while the panelling, mirror, fireplace and scattered trays sit at grain level. 7% of pixels move. That is a bounded mover, not a frame-filling one.
- **Camera still confirmed independently.** Edge columns never rise above ~1.1 across the whole clip.
- **Real out-and-back.** Frame 72 falls back to mean 1.84 / max 82 from the mid-clip 3.73 / 177, consistent with the reported return of 0.37. This is not the ambiguous zero-return branch at all, so the "return called three good clips dead" hazard isn't in play.

**Decision hygiene.** HOLD is a real member of `ROOM_DECISIONS` (long_agent.py:3496), and the runner's HOLD branch only sets `held = True` and logs "NOT accepted" — it writes nothing into `scenario.json`'s committed art or hotspots. No settings change is proposed, no prompt is hand-written, no AUTHOR_MOVER on an unrendered mover. None of the reject conditions fires.

**One flaw, not load-bearing.** The worker's b_casino precedent is wrong. The ledger record I found has b_casino at `return 0.0, peak 8.06`, verdict "survived gates — needs Lucas's eye" — not "peak 3.8 at guide 0.60, Lucas called it alive." I could find no record matching the worker's numbers anywhere in the repo. That citation should not be trusted or carried forward. It doesn't change the outcome, because I confirmed the clip is alive from the frames directly rather than from any peak-amplitude argument — the conclusion survives with the bad precedent struck out.

The worker's closing note about the stale cached `scenePrompt` predating the EQUIRECT clause is a correct thing to flag and correctly *not* acted on here.

VERDICT: PASS