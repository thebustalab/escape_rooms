Checked the frames and the code path myself rather than the worker's description. Findings:

**The still** (`rams_head/scene.png`, 3072×1024, Sep 14 21:35) plainly depicts the authored mover: a near, high-contrast meltwater ribbon falling clear of the horned outcrop down the left third, visibly braiding and coming apart. It occupies roughly 13% of frame width — **bounded, not frame-filling**. The tarn, spyglass, cold fire-basket and valley gap are all present as specced.

**The prompt that will actually render.** I traced it rather than trusting the claim. `exp_art_prompt.motion_prompt()` resolves spec-first with the `.txt` as fallback, so the worker's read of the ordering is right. Rendering the live committed `sceneSpec` gives:

> locked-off static camera, zero camera movement. The ribbon of meltwater falling clear from the notch above and dropping past the edge of the shelf, braiding and coming apart as it goes. **Only that moves**; everything else stays perfectly still. Seamless natural loop.

One mover named, 42 words (the worker said 34 — miscount, immaterial). `cirque_tarn`'s legacy `animate` block is indeed invisible to `render_motion_prompt`, which reads only `motion`. No two-movers conflict.

**One thing the worker didn't address, which I checked.** `authoring.motionSpec` still declares `tarn_surface` as **hero** — the stale mover. That looks alarming, but it feeds only the `spec` arm in `arms_for()`, and `cine_room.py:137` renders `--arms motion`. It is inert for this render. The conclusion survives.

**No clip from this art.** `rams_head_motion_ri9.mp4` is Sep 14 19:50, predating the 21:35 still. `state.json` rooms.rams_head is `{"art_generated": 1}` — no gate, no clip, and critically **no `needs_still`**, so the RENDER branch won't trip its safety net. `cycles_completed` is 29, so the next tag is `ri30`; no such file exists, so there's no tag collision that would make `exp_art_prompt` print "have …" and silently skip into a stale poll.

**Against the reject list:** no settings change (the worker explicitly declined to pre-soften vigour, and end guide stays as planned); mover is bounded; no zero-return reasoning invoked; RENDER touches only state and launches the render, writing nothing into committed art or hotspots; the prompt is spec-rendered, not hand-written; and `_has_authored_mover` passes — `melt_ribbon` carries all three of `moves`, `vigour`, `phrase`.

Spec, still and rendered prompt agree, and this mover has never been rendered. Declining to pre-soften vigour before anyone has watched it move is the right call — that lever only works downward and stays available afterward.

VERDICT: PASS