Read the four evidence docs, then checked the room against them rather than re-deriving anything.

**What the room actually has.** The live spec carries one mover — `tooth_pour` — with `motion.moves`, an authored `vigour` ("running hard off the snow lip, a heavy pour onto the wet flags") and a `phrase`. Rendering the motion prompt from the spec gives:

> locked-off static camera, zero camera movement. The pour of snowmelt falling from the snow lip on the near tooth onto the flags below it. Only that moves; everything else stays perfectly still. Seamless natural loop.

The motion prompt quoted in the brief (the avalanche plume) is the stale art_prompt_motion/networks/beacons/broken_tooth.txt fallback. The spec is the source of truth since 2026-09-13, and the `avalanche` element carries only a legacy `animate` block, which `render_motion_prompt` correctly ignores. Nothing to fix — the right prompt already derives.

**The still depicts it.** scene.png and scenario.json were both written today at 01:21, so the art is current with the spec. I looked at it at native crop: the pour is there, a heavy fall of meltwater off the snow lip on the near tooth onto wet flags, cutting the dark channel the desc asks for. Bounded — about 5% of the panorama's width, well inboard of both margins, nothing like hood's frame-filling cloud sea. Depicted vigour matches the authored vigour.

**No clip exists for this art.** cine_base.mp4 dates from 2026-09-07, eight days before the current still and spec; the gate report is empty and nothing has been tried this cycle. There is no authoring defect to act on, so the next step is the one render.

DECISION: RENDER
WHY: The spec declares one bounded mover with authored vigour, today's still visibly depicts that pour, and the spec-derived motion prompt names it and nothing else — so the room is correctly authored and simply has no clip yet at 3072x1024, end guide 0.70.