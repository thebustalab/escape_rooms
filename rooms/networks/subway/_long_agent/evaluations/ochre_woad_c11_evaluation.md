I checked the clip myself rather than taking the worker's word for it.

**What the frames actually show.** The render is 3072x1024, 61 looped frames from a 73-frame render at end guide 0.70 — matches the spec and the params file, no settings drift. Camera is dead still: the tiling, the train, both spiral stairs and the racking are pinned across the whole loop.

**The motion is exactly one bounded mover.** Only 2.5% of pixels show any real temporal range, and the hot columns sit at roughly 61–64% across the frame — precisely where `lamp_on_flex` hangs, just right of centre. Nothing frame-filling.

**The zero return is a false negative, and I can show it.** Tracking the lamp's bright blob across the loop, its centroid runs 10.8 → 19.1 → 10.7 pixels. That is a textbook out-and-back that also closes cleanly at the loop point. The clip is unambiguously alive and the swing is genuine displacement, not a brightness pulse. So the one flagged measure is wrong here, in the documented way, and re-authoring the art off it would have been the error this rule exists to prevent.

**The cited precedent is real.** ochre_hall was held at ratio 20.5 / peak 9.56 with verdict "survived gates — needs Lucas's eye" — same rung, and the worker quoted its numbers correctly.

**HOLD is a valid verb and the right one.** In the runner it sets `held`, stages the clip into the harness pool, and records "NOT accepted" — it does not touch scenario.json's committed art or hotspots. It proposes no settings change, no re-author, no hand-written prompt, and no AUTHOR_MOVER. None of the reject conditions fire.

Clip for your eye: /home/bustalab/Documents/Tools/temp/cine/_art_prompt_exp/subway/ochre_woad_motion_ri9_looped.mp4

VERDICT: PASS