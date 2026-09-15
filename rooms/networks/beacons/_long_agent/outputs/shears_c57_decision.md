I've read all four authority documents and verified the room's actual state on disk.

**What I found (no experiment re-run needed):**

- `blade_spout` already carries a full `motion` block — `moves/vigour/phrase` — and it is a **confirmed mover category** (falling water: fountain pour, spring fall, waterfall). The `lenticulars` lens cloud carries only a legacy `animate` block, invisible to `_has_authored_mover` and to `render_motion_prompt` — which is correct, since lens clouds are on the ledger's *not confirmed* list and shears' entire historical trouble ("too fast at 0.75", three different takes per seed) was that cloud.
- The motion prompt quoted in the briefing is the **stale `.txt` fallback**. The spec declares a mover, so the spec wins. `render_motion_prompt` returns: *"…The spout of meltwater jetting from the crack in the blade and arcing down into the stone basin at its foot. Only that moves…"* — 38 words, house form, names the depicted mover and nothing else.
- `authoring.scenePrompt` is **byte-identical to `render_prompt(sceneSpec)`** — fresh, equirect clause present, not hand-written.
- `scene.png` was regenerated 2026-09-14 23:48 from that prompt, after the 20:18 spec edit. I looked at the x≈0.20 crop at native resolution: the spout is **there and bounded** — a thick jet arcing clear of the blade into a worn basin, streaming wet rock below, roughly a sixth of the frame width. Not frame-filling, unlike `hood`'s cloud sea.
- Seam screened the same minute: `seamBandRun` 0.008, `needsWork` false.
- The only clips in the room date from Sep 7, long predating this still. Gate report is empty.

Spec, prompt and art are all correct and mutually consistent, and nothing has been rendered against them. There is nothing to author, soften or pin — pinning the cloud pre-emptively would be the a_opera mistake (a rigid clause used before anything was observed moving, which took that prompt to 176 words and made the camera drift). The next thing this room needs is the one render.

DECISION: RENDER
WHY: The spec carries a bounded, confirmed-category mover (`blade_spout`) with authored vigour, the committed still visibly depicts it, `scenePrompt` matches `render_prompt` exactly and the motion prompt resolves from the spec to name that spout — and no clip exists against this art.