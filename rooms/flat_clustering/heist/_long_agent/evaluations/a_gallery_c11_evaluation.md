I checked every load-bearing claim against the files rather than the worker's summary.

**Verified:**

- **Live spec is the one shown.** `scenario.json` → `authoring.sceneSpec` for `a_gallery` matches the prompt's spec exactly. (Note: `scene_specs_heist.json` on disk is *stale* — missing the `fob` element and carrying vigour inline in `desc` — but that's the pre-art authoring input, not the live spec. Worth a cleanup sometime; not a blocker.)
- **One bounded mover.** `sheet` — canvas dust sheet over a near plinth, `motion.moves: true`, vigour "lifting and settling in the draught from a propped fire door". Bounded cloth, explicitly the strongest confirmed category in `cinemagraph_pipeline.md` §1. Not frame-filling.
- **No prompt drift.** I ran `scene_spec.render_motion_prompt` on the live spec and diffed it against `cinemagraph_tools/art_prompt_motion/heist/a_gallery.txt` — identical, byte-for-byte. The committed `scenePrompt` also carries the vigour clause, so the still depicts what the motion prompt names.
- **Still is committed and seam-clean.** `scene.judge.json`: verdict `hold`, `triaged: true`, committed `l1_a_gallery_1.png`, reason cites a clean plain-marble seam needing no repair. `authoring.seam.needsWork: false`, stage `screened`.
- **The 16-cell claim is real.** `notes/z_archive/report.md` (archived) → *§2. Animatability is authored, not discovered* — "The four `heist` rooms animate in **all 16 cells** of their grids"; the same section names `compare_cal_a_gallery.mp4` (dust sheet) among the alive positive controls. (Line numbers dropped: `cinemagraph_findings_report.md` was folded into this file on archiving, shifting it by ~13 lines.)
- **Not a settings change.** `cinemagraph_pipeline.md` §3 states the standing render config verbatim: "3072x1024, end guide 0.70, cfg 2.0, 8 steps, 73 frames, 24 fps, seed 4242." The worker is restating canon, not proposing a lever. The same file records the end guide as inert across 0.65–0.85.

**Against the reject list:** no settings change, mover is bounded not frame-filling, no zero-return reasoning invoked (no clip exists), no clip acceptance and no write to committed art or hotspots, no hand-written prompt, and the decision is RENDER rather than AUTHOR_MOVER — which is the correct call precisely *because* this mover has never been rendered.

One caveat that does not reject: `authoring.seam` has no explicit human `accepted` field, only `needsWork: false` plus the judge's `triaged: true`. If the runner's contract strictly requires a human accept stamp before motion, that's the one thing a later pass should tighten. It doesn't hit any listed reject condition here.

The spec is authored, the art matches it, the prompt derives from it, and the only missing artefact is the render itself.

VERDICT: PASS