I've read the pipeline, the report, the ledger head, and `render_prompt`/`render_motion_prompt`, and checked the room's actual state on disk.

**Situation.** Cycle 17's RENDER executed. The clip exists — `temp/cine/_art_prompt_exp/heist/briefing_motion_ri17_looped.mp4`, baked with crossfade and seam repair — and the runner's own log already files it as *"survived gates — needs Lucas's eye"*.

All three reject-only gates cleared:
- **camera** — `still` (frame0_corr 0.963, landmark drift 0 px). Pass.
- **glitch** — breadth 0.0 and breadth_normalised 0.0, against a threshold of 0.70 on *both*. Pass, not marginally.
- **return** — 0.0, which is the ambiguous case the pipeline says must escalate and never reject.

The zero return is expected here, not alarming. The mover is rain running down glass: continuous one-way flow, which never returns to its frame-0 configuration pixel-wise while looping perfectly. That is precisely the family the ledger retracted a wrong "dead" call on — b_casino's smoke and logwood_verdigris's water both scored exactly 0.00 at 3072 and Lucas called them alive. Re-authoring on this number would repeat a recorded mistake.

There is nothing left for me to decide: the spec carries one bounded mover (the window bank, ~x 0.12–0.30 of a five-element room), the motion prompt derives from that same spec via `render_motion_prompt`, the still visibly depicts the rain, and no gate may approve. It goes to the eye.

DECISION: HOLD
WHY: The cycle-17 clip cleared the camera and glitch gates outright and its 0.0 return is the documented cyclic-flow ambiguity for a flowing mover like rain — escalate to Lucas's eye, never reject or re-author on it.