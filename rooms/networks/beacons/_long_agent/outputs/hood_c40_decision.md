Read the pipeline, report, ledger and `scene_spec.py`, then checked hood's actual state on disk rather than trusting the brief.

**What I found:** the sceneSpec has already been re-authored with a bounded mover — `drip_curtain`, a heavy continuous curtain of meltwater coming off the lip of the cowl, carrying a full `motion: {moves, vigour, phrase}` block. `scene.png` was regenerated from that spec today at 22:23, and the crop confirms the art actually depicts it: a bounded sheet of falling water over the left third, landing on wet flags. Falling water is on the ledger's confirmed-mover list.

**The motion prompt in the brief is stale.** It's the `art_prompt_motion/beacons/hood.txt` fallback, still naming the frame-filling cloud sea — the exact thing that makes hood the weakest room at 3072. Rendering `render_motion_prompt` against the live spec gives the right one:

> locked-off static camera, zero camera movement. The curtain of meltwater drips falling from the lip of the cowl just outside the rail, its threads breaking and reforming. Only that moves; everything else stays perfectly still. Seamless natural loop.

Since the spec declares a mover, the renderer takes that and ignores the `.txt`. The `inversion` cloud keeps only a legacy `animate` block, which neither `_has_authored_mover` nor `render_motion_prompt` reads — so the frame-filling cloud is no longer what this clip is being asked to animate. I did not pre-emptively pin it: the rigid clause is reactive by design, and used before there's evidence it causes the drift it exists to prevent.

The existing `cine_base.mp4` is from Sep 9 and predates the new still, so no clip exists for this art.

DECISION: RENDER
WHY: The spec carries a bounded, vigorously-depicted mover that the freshly regenerated still genuinely shows, the spec-derived motion prompt names that mover and nothing else, and no clip exists from this art yet.