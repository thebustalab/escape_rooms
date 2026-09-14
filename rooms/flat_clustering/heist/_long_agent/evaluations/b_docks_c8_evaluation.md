Checked the tree myself rather than the write-up.

**Holds up:**
- The mover is authored on disk. The live spec at rooms/flat_clustering/heist/scenario.json → rooms[7].authoring.sceneSpec has `tarp` carrying motion.moves / vigour / phrase, so the mover gate is genuinely satisfied. (The legacy scene_specs_heist.json still lacks it, but that isn't the file the gate reads.)
- The mover is bounded, and I confirmed that by eye, not by description. In the committed 3072×1024 panorama the tarpaulin is lashed to one side of the hatch and occupies roughly an eighth of the frame width, with the rest of the left wall static boarding. Nothing frame-filling.
- The motion prompt at cinemagraph_tools/art_prompt_motion/heist/b_docks.txt names only the tarp and its sentence is verbatim the spec's motion.phrase. It is not hand-written for this cycle; it derives from the spec.
- Still is committed and seam-clean: needsWork false, stage screened, judge verdict hold/triaged.
- No clip in the room's own path — b_docks/ holds only scene.png and scene.judge.json. Gate report and tried-list both empty.
- The decision changes no settings, accepts no clip, touches no committed art or hotspots, and correctly declines to edit the spec (which would overwrite the 1782-char committed scenePrompt with the current renderer's 3121-char output in an unversioned tree — I confirmed that length).

**One claim that doesn't hold:** the artifact inventory. b_docks_motion_firstrun in temp/cine/_art_prompt_exp/heist is at end_guide 0.70, 3072×1024, steps 8, cfg 2.0 — that *is* the pinned default, not a cal-grid or Y-fan probe. So the worker's "none a render at the pinned default" is wrong. It doesn't change the action: that clip lives in an experiment directory, was never gated, and the pipeline still needs a render it owns. The proposed step is the same one either way.

None of the six rejection conditions applies, and the action is the conservative next move for a room with an authored bounded mover and no gated clip.

VERDICT: PASS