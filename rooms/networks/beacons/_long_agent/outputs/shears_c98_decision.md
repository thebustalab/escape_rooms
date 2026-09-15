Evidence checked against the files, not the summaries.

**What the state actually is**

- **The spec's mover is real and depicted.** `blade_spout` is the only element with a full `motion` block (`lenticulars` carries only a legacy `animate`, invisible to `_has_authored_mover` and absent from the prompt). I looked at the committed `scene.png` at native crop: a thick jet arcs clear of the blade face into a worn basin, bounded at roughly an eighth of the frame width. That is the condition the whole loop rests on, and it is met.
- **The art is current.** `SS.render_prompt(spec)` reproduces the committed `authoring.scenePrompt` **byte-identical** (6119 chars both). The vigour was not touched, so `needs_still` must not fire.
- **The softening is already in the spec, and has never been rendered.** `motion.phrase` now reads *"running gently and steadily … a slow unhurried fall"*; `render_motion_prompt(spec, rigid=True)` gives a 66-word prompt with a one-item rigid clause. `scenario.json` was edited 11:54 UTC; the newest clip, `shears_motion_ri92_looped.mp4`, is 11:31 UTC — it was rendered from the old *"jetting … arcing down"* phrase, which is the one Lucas called too fast.
- **The stale `.txt` is inert.** The prompt handed to me as "current" is `art_prompt_motion/beacons/shears.txt` (00:19), still carrying the unsoftened wording. `exp_art_prompt.motion_prompt` takes the spec first and falls back to the `.txt` only when the spec declares no mover, so the render will use the softened phrase.

This is the same position `anvil` was in at cycle 96 and `sisters` at 94: phrase softened, art untouched, clip on disk predating the edit. Nothing to author, soften or pin — the remaining move is the render.

DECISION: RENDER
WHY: The spec's one bounded mover is visibly depicted in a still whose art prompt is byte-identical to the committed one, and the already-softened spec-derived motion prompt has never been rendered — the clip on disk predates the phrase edit by 23 minutes — so one render at the pinned 0.70, seed 4242, is the whole remaining move.