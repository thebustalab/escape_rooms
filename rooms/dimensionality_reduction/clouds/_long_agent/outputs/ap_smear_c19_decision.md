Read all four authority docs (`report.md` is archived at `notes/z_archive/report.md`), then inspected the room itself.

**What I found:**

- The spec **already carries one bounded authored mover**: element `rain`, with a full `motion` block (`moves: true`, `vigour: "heavy and continuous"`, `phrase: "rainwater streaming off the wing's trailing edge in a broad, glittering sheet"`). That is the shape `_has_authored_mover` reads — not the legacy `animate`-only shape that made the loop skip pre-migration rooms.
- `render_motion_prompt` produces the house form cleanly, so "motion prompt: NONE" is only the absent `.txt` fallback, not an absent prompt: *"locked-off static camera, zero camera movement. Rainwater streaming off the wing's trailing edge in a broad, glittering sheet. Only that moves; everything else stays perfectly still. Seamless natural loop."*
- **The still depicts it.** I looked at the committed `scene.png` at 3072x1024 and cropped both wings: a clear curtain of falling water streams off each wing's edge, roughly 8% of frame width and half the height — bounded, not frame-filling, and falling water is a confirmed-mover category (and loops perfectly, since a fall looks identical at every instant). This is the `logwood_verdigris` / `alum_madder` failure avoided: the mover is drawn, not implied.
- The art is **not stale**: the cached `scenePrompt` is byte-identical to `render_prompt(sceneSpec)` today, carries the EQUIRECT clause, and carries the appended vigour.

Nothing here calls for touching the art. Adjusting vigour would regenerate a panorama that has not yet failed anything, and softening the prompt is a too-lively remedy with no clip to be too lively. The end guide is pinned at 0.70 and is not searched.

DECISION: RENDER
WHY: The spec carries one bounded, depicted mover with authored vigour, the motion prompt renders correctly from it, the committed still matches the current spec prompt exactly, and no clip exists yet.