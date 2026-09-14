I read the four authorities, then measured ri78 on disk rather than deciding from the gate summary — because the summary's own note says this measure has called three good clips dead.

**The gate's ambiguity resolves, and it resolves as dead.** A per-column temporal-std profile on the RAW render (the same method that characterised ri75 and ri61) settles it without leaning on return or peak, which are the readings that have made wrong calls before:

| band | ri78 | ri75 (the clip Lucas called too aggressive) |
|---|---|---|
| swag, x 0.15–0.33 (its authored position) | **0.83** | 5.23 |
| frame median | 0.86 | 1.17 |
| global max | 1.49 | 10.51 at x=0.26 |
| pixel-std max | 4.74 | 81.30 |

ri78's mover measures **below its own frame's median** — there is no localised variance at the swag, or anywhere else. That is what rules out the cyclic-flow reading: b_casino's smoke and verdigris' water score return 0.00 while still showing strong local variance at the mover. Here nothing does. Brightness and spatial contrast are identical across the two renders (31.6/31.0, contrast 30.8 both), so the numbers are comparable. The `|f_t − f_0|` trace confirms it: ri78 jumps to 1.3 by frame 6 and flatlines; ri75 arcs 1.2 → 3.0 → 1.5.

**The cause is known and it is not the art.** Same still, same seed, same settings, one hour apart — only `swag.motion.phrase` changed, from "stirring gently in a draught, its folds shifting and settling" to "breathing very slightly, its folds barely shifting". The intensity lever worked exactly as the ledger says it does, downward, and Lucas's round-2 wording overshot from too-aggressive to nothing. Peak fell 5.04 → 3.70, below hood's dead 5.1–5.2.

So none of the loop's fix ladder fits. `ADJUST_VIGOUR` regenerates a still that is demonstrably fine and would redraw the panorama Lucas already accepted, including the lighter sizing he asked to be fixed. `SOFTEN_PROMPT` is the wrong direction, and the ledger is explicit that strengthening language does not turn motion up. Re-authoring the art is the documented remedy for dead, and it is the wrong remedy here. What is left is a single wording dial between two measured endpoints — 5.23 too much, 0.83 nothing — and where it should sit is a liveliness judgement, which is the one call no metric and no reading of mine may make.

DECISION: PARK
WHY: ri78 is dead by spatial measurement rather than by the ambiguous return, the cause is Lucas's own round-2 softening overshooting on an art still that is correct and must not be re-authored, and picking the wording between his two measured endpoints is a liveliness call that belongs to his eye.

**What I want asked:** *Your softening of a_opera's swag overshot — "breathing very slightly, its folds barely shifting" renders stone dead, not just quieter, while your previous "stirring gently in a draught, its folds shifting and settling" is the ri75 clip you called too aggressive. Do you want an intermediate phrase rendered once (something like "stirring slowly in a draught, its folds shifting a little and settling"), or would you rather just ship ri75 as-is?*

One thing for a human, outside the decision: this cycle's brief again quotes the stale 104-word `cinemagraph_tools/art_prompt_motion/heist/a_opera.txt` as the room's current motion prompt, while the renderer resolves the 57-word prompt from the spec. Cycle 78 flagged the same thing; it is still a one-line fix in whatever assembles the brief, and it has now misled four briefs running.