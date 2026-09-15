I checked the room on disk rather than the write-up.

**What I verified myself**

1. **Spec state.** The committed sceneSpec in rooms/networks/beacons/scenario.json has exactly one element carrying a `motion` block — gutter_pour, with moves + vigour + phrase all present, so `_has_authored_mover` returns True. river_mist and chimney_smoke now carry `animate` only. I traced `animate`: nothing in cinemagraph_tools or scene_spec's `movers()` reads it. It is inert for motion. So this really is one mover, and the two distant atmospherics Lucas killed are genuinely demoted, not smuggled back in.

2. **Prompt provenance.** `authoring.scenePrompt` compares byte-identical to `SS.render_prompt(spec)`. I ran the real render path with --dry-run: exp_art_prompt resolves the motion arm from the spec, not from art_prompt_motion/beacons/fenwatch.txt (which still holds the stale woodsmoke/mist text from 8 Sep). The prompt that will actually go to the model is the 39-word pour sentence. I also checked the motion arm's negative — it's the fixed short camera/quality string; the room's motionSpec negatives (which ban "churning water", "splashing") feed only the unused `spec` arm, so there is no mover-vs-negative conflict.

3. **The still depicts it.** I looked at scene.png (3072x1024, committed 20:21). A lead downpipe at the office corner throws a heavy unbroken white rope of water into a brim-full slate butt that overflows down both sides onto the cobbles. Hard-edged, high-contrast, roughly 8% of frame width — bounded, not frame-filling, and falling water is a confirmed mover.

4. **Seam.** I built the wrap strip by hand. Wall courses, cobbles and hillside all run straight through the join. No occluder needed; seamBandRun 0.015, needsWork false.

5. **No tag collision.** Next tag is ri16; no fenwatch_motion_ri16* exists, so exp_art_prompt won't skip and silently re-gate an old clip.

**One thing the worker got wrong.** "No clip has ever been rendered from this art … the room has never been driven" is only half true. progress.md shows fenwatch rendered at cycle 1 (tag ri1, seed 4242), gated at return 0.00, and HELD at 23:10 UTC. That clip animated the *previous* art with the two-atmospheric-mover prompt. The runner's state was reset for the full re-author, which is why the brief says "Clip: none yet" — the worker inherited the gap rather than inventing it. It doesn't move the decision: the art was regenerated at 20:21, so a render against the new still is the correct next step either way.

**Against the six rejection criteria:** no settings change; mover is bounded and verified in-frame; the zero-return caveat is stated in the right direction (ambiguous, never fatal, never grounds for re-author alone); RENDER writes nothing into committed art or hotspots and accepts nothing; the prompt is spec-derived, not hand-written; and this is not a premature AUTHOR_MOVER. The needs_still flag is clear, so the RENDER branch won't park.

VERDICT: PASS