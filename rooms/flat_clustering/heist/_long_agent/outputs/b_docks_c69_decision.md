I read the four authority docs, then measured the actual render rather than trusting the global numbers.

**Why the global metrics look borderline but aren't.** `peak 5.11` sits exactly on hood's dead signature (5.1–5.2), and `return 0.07` is near the zero the ledger calls ambiguous. But both are frame-global means, and this room's mover is now deliberately ~6% of frame width — the re-author Lucas asked for. Localising the measurement resolves it:

- Per-column temporal std: background ~2.0 everywhere, **11.4 / 12.1 at x=0.14–0.20** — the tarpaulin's authored position. Peak tile std **32.6**, in a single blob at x 0.135–0.20, y 0.28–0.72.
- Restricted to that band: **peak 10.26, return 0.34, argmax frame 28/73** — a clean mid-clip out-and-back arc, the a_vault/station1 signature, not the monotone one-way rise of a dead clip.
- Frames 0 and 28 confirm it by eye: the loose lower corner lifts from hanging to a wind-filled billow and comes back. Correct object, cloth behaviour, no invented content.
- Nothing else of consequence moves. The two secondary regions (x≈0.26 and x≈0.83) are wet water and lamp reflections seen *through* the hatch and the gangway door, at std 6–8 against the tarp's 30 — not panelling, not the board, console or crates. No rigid escalation is warranted.

Camera still; glitch 0.021 / 0.042 against a 0.70 threshold on both readings. Every reject-only gate passes and the room is alive on the authored mover.

```
DECISION: HOLD
WHY: Localised measurement shows the authored tarpaulin is the only significant mover — peak 10.26 and return 0.34 over a clean mid-clip arc at x=0.14-0.20, against a ~2.0 background elsewhere — so the low global peak is the arithmetic of a correctly bounded mover rather than a dead clip, and with camera and glitch both clear the only question left is whether the billow's excursion is to Lucas's taste, which is his eye's call and not another render's.
```

One note for the record, not a change: the brief's quoted motion prompt ("billows and slackens") is the stale `art_prompt_motion/heist/b_docks.txt` fallback. The spec declares a mover, so the render used the softened `motion.phrase` — "the loose lower corner of the lashed-back tarpaulin flapping and snapping in the wind off the water" — which is what the frames show.