I read the four authorities, then reconstructed the room's real state on disk rather than trusting the brief's summary — the brief's "current motion prompt" is again the stale 104-word `cinemagraph_tools/art_prompt_motion/heist/a_opera.txt`, while the renderer resolves a 57-word prompt from the spec (verified by calling `render_motion_prompt` on the live spec).

**What the gate report is.** It is ri78, and cycle 80 already resolved its ambiguity against it by direct measurement (swag band temporal std 0.83 against a frame median of 0.86 — no localised variance anywhere, which is what rules out the cyclic-flow reading; ri75's swag band measures 5.23 at exactly the authored position). The clip is dead, not cyclic. Cycle 80 then PARKed and was failed, correctly: its load-bearing premise — that the cheap fix would redraw the panorama — is false.

**I verified that myself against this exact spec rather than taking the evaluator's word:**
- `render_prompt` folds in only `motion.vigour`; `motion.phrase` is read by `render_motion_prompt` alone.
- A phrase-only fragment on this spec leaves the art prompt **byte-identical** (3129 chars, and it already matches the stored `scenePrompt`), so `long_agent.py:4093` will not set `needs_still`. The committed still and Lucas's lighter sizing are untouched.
- The rigid clause survives: `exp_art_prompt.motion_prompt` turns `rigid` on from `spec["rigid"]` itself, so the walls-and-parapet pin stays in — Lucas's "wall weirdly breathing" note remains answered. The new prompt is 62 words, far short of the 176-word pin that made ri73 drift.

**The wording.** Two points measured on the same still, same seed 4242, same settings: "stirring gently in a draught, its folds shifting and settling" → 5.23, too aggressive; "breathing very slightly, its folds barely shifting" → 0.83, dead. This is not strengthening a prompt past what the art depicts — the ledger's "works down only" — it is *softening the measured-alive wording*, the direction the lever reliably works, and landing it on the vigour the still actually depicts ("stirring gently in a draught from the flies, its folds shifting a little"). It also ends the spec's internal inconsistency between `vigour` and `phrase` without touching `vigour`, which would cost a still.

One render remains in budget (attempts 1 of 2), which is the right size for this: one intermediate point, gated, then Lucas's eye.

DECISION: ADJUST_VIGOUR
SPEC: {"id": "swag", "at": "to the left", "motion": {"phrase": "the heavy crimson velvet swag curtain at the box mouth stirring slowly in a draught, its folds shifting a little and settling"}}
WHY: ri78 is dead because Lucas's round-2 softening overshot, and a phrase-only spec edit sets the amount between his two measured endpoints while leaving the art prompt byte-identical — so no still is regenerated and the next render hands him a third measured point instead of a question he must answer blind.

Aside for a human, outside the decision: the brief has now quoted the stale `art_prompt_motion/heist/a_opera.txt` as this room's motion prompt for five cycles running. It is genuinely unreachable for heist and it is a one-line fix in whatever assembles the brief.