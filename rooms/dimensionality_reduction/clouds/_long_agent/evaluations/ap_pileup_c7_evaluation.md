I checked every claim against the files and the image rather than the worker's description.

**Verified independently:**

- `render_prompt(current sceneSpec)` is byte-identical to the committed `scenePrompt` (10,407 chars both). The still is not stale — it *is* what this spec produced, torn-cloud clause included.
- I looked at `ap_pileup/scene.png` at the `just left of centre` position (`_POS` → x=0.36). There are no near torn rags of cloud and no wing struts there. What is there — large, sharp and unmistakable — is the glass sampler globe with a glowing bloom inside it, centred almost exactly on x≈0.355. The art was asked for the mover and produced the globe instead.
- The current motion prompt would therefore instruct "Torn cloud streaming close past the wing struts and parting around them" over a crop containing a glass globe and a distant city — the exact failure this loop was built to eliminate.
- The phrase does violate live canon: `notes/cinemagraph_pipeline.md` §"THE NO-TRAVEL RULE" names "clouds drifting" and "anything crossing frame" under **Never name**, with the gulls/clouds evidence. (The worker dated it 2026-08-30; the file records it migrated 2026-09-22. Substance right, date off — immaterial.)
- The `cockpit` precedent is real and matches exactly: same `sampler` element, same `at`, RENDER at cycle 1 then HOLD at return 0.28, peak 10.17, glitch breadth 0.146, dead false, camera still. Vigour and phrase are copied verbatim.
- `torn_cloud` appears nowhere outside the sceneSpec, so no `plannedHotspot` breaks.
- I simulated the runner's merge: the fragment is valid JSON, matches on `at`, and overrides id/desc/motion/animate/sound wholesale — the old travel phrase cannot survive. One mover remains; the art prompt changes, so the runner sets `needs_still` and regenerates the panorama before any clip, which is the correct order.

None of the six reject conditions holds. The mover **has** been rendered — through the art, where it failed — so the last criterion, which exists to stop re-authoring before evidence, does not apply here.

Two things worth the runner's awareness, neither disqualifying: the proposal uses `crossfade` where cockpit's proven clip used `boomerang` (both defensible under `SCENE_SPEC_GUIDE` rule 4 for a slow turning subject), and the regenerated still could double the globe since `nose` also names it — the worker's explicit "ONE and only… drawn exactly once" guard is the right available lever for that.

VERDICT: PASS