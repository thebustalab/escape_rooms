I verified every load-bearing claim against the files rather than the narrative.

**Confirmed independently:**

- **One mover, not two.** `scene_spec.movers()` keys only on `motion.moves`; `dome_banner` carries an `animate` block, which that function ignores. Running it on the live `scenario.json` returns exactly `['juniper_smudge']`.
- **The spec-derived prompt.** `render_motion_prompt(spec)` emits *"locked-off static camera, zero camera movement. The rope of juniper smoke climbing and rolling from the smouldering dish on its tripod. Only that moves; everything else stays perfectly still. Seamless natural loop."* — 32 words (worker said 33; immaterial). `rigid` stays off, correctly, since the spec has no `rigid` and no `still_as`.
- **The stale `.txt` genuinely cannot win.** This was the claim most worth distrusting, since the RENDER branch doesn't rewrite `motion_p`. Traced it through: `_launch_cine_room` → `cine_room.py` → `exp_art_prompt.motion_prompt()`, which tries `sceneSpec` first and falls back to `art_prompt_motion/<scenario>/<room>.txt` only if the spec yields nothing. beacons is migrated, so the banner/heat-shimmer text is unreachable here.
- **The still depicts the mover.** Viewed `scene.png` (regenerated today 01:40) at native crop: an iron dish on a low tripod heaped with juniper brush, throwing a well-formed pale rope of smoke against the red dome, left of centre, roughly a tenth of frame width. Textbook bounded near-field mover — not frame-filling. No flame in the dish; the fire-basket on the right is rusted iron over sunlit straw, unlit.
- **No clip exists for this authoring.** `cine_base.mp4` is 2026-09-07 14:14; the `near_movers` spec backup is 2026-09-14 20:18, and the still is 2026-09-15. Its `judge.json` scored `banner_cloud` and `range_haze`, and its mask boxes those same two — subjects the current spec no longer drives.
- **It will actually execute.** State has `kiln: {"art_generated": 1}` with no `needs_still` and no `parked`, and `_has_authored_mover` passes on moves+vigour+phrase — so RENDER reaches `_launch_cine_room` rather than hitting the safety-net park.

**Against the reject list:** no settings change; the mover is bounded, not frame-filling; no zero-return-means-dead reasoning is invoked anywhere; no clip is accepted and nothing is written to committed art or hotspots; the prompt is spec-derived, not hand-written; and RENDER is the correct call precisely *because* this mover has never been rendered — AUTHOR_MOVER here would be the violation.

VERDICT: PASS