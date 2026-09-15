Verified independently against the files rather than the worker's summary:

**Mover is real and singular.** `movers()` in `authoring_v2/scene_spec.py:396` selects only on `motion.moves`, so `cirque_tarn`'s legacy `animate` block is invisible to it. Running `render_motion_prompt` on the live spec (`rooms/networks/beacons/scenario.json`, `rooms[2].authoring.sceneSpec`) returns exactly one mover — `melt_ribbon` — and a 42-word house-form prompt naming only the waterfall. (Small correction to the worker's account: the cat's-paws text is `cirque_tarn`'s legacy `animate`, not an `art_prompt_motion` fallback — the room has no such field. Doesn't change the outcome; the renderer reaches neither.)

**Bounded, not frame-filling.** I looked at `scene.png` (3072×1024) at native crop. The fall occupies roughly x 0.06–0.28 of the panorama — a hard-edged braiding column against dark rock, matching the authored text ("falls clear of the rock", "braid and come apart"). The frame-filling tarn behind it is *not* named in the prompt. Falling water is the confirmed-alive family, and `notes.md` records Lucas approving the equivalent cascade in `ladder`.

**Never rendered in this form.** `cine_base.mp4` is 2026-09-09; `scene.png` is 2026-09-14 21:59. `melt_ribbon` is absent from every backup up to `bak_20260914_201850_near_movers` and present only from the current file — it came in with the 2026-09-14 near-movers re-author that regenerated the stills, and the image plainly depicts it. Gate report empty, `tried` empty.

**Seam clean:** `seamBandRun` 0.004, `needsWork` false, screened 2026-09-15.

None of the reject conditions fires: no settings lever, bounded rather than frame-filling mover, no zero-return reasoning, no clip acceptance and no write into committed art or hotspots, prompt resolved from the spec rather than hand-written, and the decision is RENDER rather than a re-author of an unrendered mover.

VERDICT: PASS