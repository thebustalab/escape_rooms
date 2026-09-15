I read the four authority docs, then checked the live spec, the runner's apply logic, and the previous cycle's evaluator note.

**What's actually going on.** The whole-frame gate is benign (camera still, glitch 0.208 well under 0.70, return 0.0 → ambiguous), but the evaluator recorded in `state.json` already re-measured the raw clip region by region: the pour + butt peaks **19.24 at frame 35 with return 0.13** — a genuinely alive, cyclic bounded mover — while every *stone* region (centre office 9.33, right seam wall 9.96, left seam wall 7.62) peaks on the **final** frame and never returns, with the smooth sky quiet at 1.21. That signature is a non-rigid warp on textured masonry, not an exposure shift. This is exactly heist/a_opera's *"the wall is like weirdly breathing"*, whose fix is step 6 rule 2, the `rigid` escalation — not new art.

The last cycle reached the same conclusion and **failed on payload format**: `long_agent.py:4170` treats a rigid list as a bare JSON string or a JSON list, so `{"rigid": "..."}` fell through to the element branch, would have been inserted as a junk 10th element, and `spec["rigid"]` would never have been set. The spec on disk is clean (9 elements), so nothing was corrupted — it just changed nothing.

I verified the correct payload against the real renderer: the art prompt comes out **byte-identical**, so the still generated at 20:21 today is not discarded and only the clip re-renders. The motion prompt lands at **66 words with two pinned items** — the a_opera register that worked (61 words, camera still), not the seven-item 176-word version that induced camera drift.

Also worth flagging for the record: the "current motion prompt" about woodsmoke and river mist is the stale `art_prompt_motion/beacons/fenwatch.txt` fallback from Sep 8. The spec renders the gutter-pour prompt, and that is what governs.

DECISION: PIN_NON_MOVERS
SPEC: ["the drystone yard wall", "the stone office range and its slate roof"]
WHY: The authored pour is alive and cyclic (peak 19.24 at f35, return 0.13) but the stone office and both seam walls warp non-rigidly to a final-frame peak, so the fix is a two-item rigid scalpel — which leaves the art prompt byte-identical and re-renders only the clip.