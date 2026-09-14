I checked the worker's claims against the files rather than the write-up.

**Verified on disk:**

- **Spec vs. still.** `scenario.json` was touched this morning (07:39), *after* the still — but the only gala diff against the 22:23 backup is `builtFrom` (`l1_gala_1` → `l1_gala_2`) and a seam-bookkeeping note. The `sceneSpec` itself is unchanged since the 22:01 re-author, and `scene.png` was written at 22:24. Art and spec agree.
- **The still depicts the mover.** I cropped the left-of-centre region at native resolution. The navy house pennant is on its varnished staff, streaming near-horizontal against open sky, free end curling over on itself, halyard visibly bowed — exactly the authored vigour. It occupies a narrow slice against high-contrast sky. Bounded, not frame-filling.
- **The prompt is genuinely single-mover.** I ran `scene_spec.render_motion_prompt` on the live spec. It returns verbatim what the worker quoted — the pennant phrase and nothing else. The drapes' legacy `animate` block is invisible to it, and the `rigid=True` escalation is available later if the drapes misbehave.
- **The clip really does predate the art.** The only gala clips are 21:22/21:23 local on 09-13. The progress log's gala render (01:14–01:31 UTC) is that same one, held with the zero-return note — and Lucas's feedback, the re-author, and the art regeneration all landed *after* it, between 22:01 and 22:24. So the mover in this still has never been rendered.
- **The brief's history is wrong, as the worker said.** There are `gala_c32`/`gala_c34` evaluations on disk, and c52–c55 died on a `settings.local.json` wildcard permission error without deciding anything.

**Against the reject list:** no settings change, mover is bounded not frame-filling, the zero return isn't used to call anything dead, no clip accepted, nothing written to committed art or hotspots, no hand-written prompt, and AUTHOR_MOVER is correctly *not* proposed — the whole argument is that the existing mover has never been rendered, which is precisely when RENDER is the right move.

The worker's incidental note is also correct: `motion.vigour` appears both in the authored `desc` and again appended by `render_prompt`. Duplicated emphasis, not a defect, and it was rightly left alone.

VERDICT: PASS