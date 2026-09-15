Checked the worker's claims against disk rather than the write-up.

**Verified:**
- `scene.png` is 3072×1024, mtime 2026-09-14 22:23; `cine_base.mp4` is 2026-09-09 12:16. No clip exists from this art.
- The still genuinely depicts the mover, and it is **bounded**: a heavy curtain of falling meltwater over roughly the left fifth of the frame, landing on wet flags. Not frame-filling.
- `drip_curtain` carries a real `motion: {moves, vigour, phrase}` block on disk; `inversion` carries only the legacy `animate` block, which neither `movers()` nor `render_motion_prompt` reads (`authoring_v2/scene_spec.py:389-433`).
- `exp_art_prompt.motion_prompt` takes the spec over the `.txt` fallback (`cinemagraph_tools/exp_art_prompt.py:87-107`). Ran it against the live scenario: it returns the worker's quoted prompt verbatim, naming only the meltwater curtain. The prompt was not hand-written.
- No `hood_motion_pipe*` in the staging dir, so no stale-skip re-gating an old clip on the default tag.

None of the reject conditions fire: no settings lever, bounded mover, no zero-return reasoning, no clip acceptance or scenario.json art/hotspot write, and RENDER is the correct action for a mover that has never been rendered.

**One thing the worker missed, non-blocking for this action:** `authoring.motionSpec` for hood is stale and describes a different room (rock arch, reading slab, a river) with hero subject `cloud_sea_left` plus two more cloud-sea boxes. `cine_room.py`'s render path never reads it, so the render is clean — but `cine_scenario.py`'s `box_mask`/hero-box logic does. If this clip is later baked into the room dir, the mask will play only the cloud-sea box and drop the drip curtain entirely. That needs fixing before the bake, not before the render.

VERDICT: PASS