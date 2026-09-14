I looked at the clip myself rather than taking the worker's read on trust.

**What I checked**

- Render params at temp/cine/_art_prompt_exp/heist/gala_motion_ri32.params.json: 3072x1024, end_guide 0.70, cfg 2.0, 8 steps, 73 frames, seed 4242 — canonical, as claimed. ffprobe confirms the stream.
- Frame 1 at native res matches the spec: drapes and bunting on the left, three laid tables, brass-framed easel plan dead ahead, rail and gold sea just right of centre, salver with five distinct effects at right. No lettering. Spec and image agree.
- Per-region temporal std over all 73 frames: drapes 3.98, sea 3.61, tablecloth 2.27, static deckhouse boarding 1.51, sky 1.26. The hottest 64px blocks cluster at x 576–1088 — the drape run. So the activity that exists is real, bounded, and in exactly the declared mover's region, not frame-filling.
- Against that: 64px block matching (±16px, 2px step, frame 1 vs 37) returns zero displacement everywhere, and the most temporally distant frame pair in the drape region is (first, last) rather than an interior pair. Side-by-side of frame 1 and frame 73 cropped tight on the swag shows identical fold geometry, fringe and lantern placement — the amplified diff is edge shimmer, not a fold sweeping.

**Judgement**

That leaves it genuinely ambiguous, which is the condition the gate report names. The drape region carries the frame's strongest, correctly-localised signal at 2.6x the static baseline, but no fold displacement I can resolve from stills. Sheer silk under raking light can read alive in playback without gross displacement, and the raw clip is delivered boomerang-looped, which is the designed handling for a non-returning raw clip. I can't call it dead from PNG diffs — a re-render on this evidence is the error the ledger already records.

Checked against the reject list: no settings change proposed, no frame-filling mover, the zero return is explicitly refused as grounds for rejection rather than treated as proof of death, nothing accepted and nothing written to scenario.json, no hand-written art prompt, no AUTHOR_MOVER. None applies. HOLD costs nothing and parks it for your eye, which is where this one belongs.

Two things worth carrying: `authoring.seam.accepted` is still false in websites/thebustalab.github.io/escape_rooms/rooms/flat_clustering/heist/gala/scene.judge.json though the seam measures clean, and gala's cached scenePrompt still predates the EQUIRECT clause — correctly left alone, since regenerating the panorama is the expensive lever.

VERDICT: PASS