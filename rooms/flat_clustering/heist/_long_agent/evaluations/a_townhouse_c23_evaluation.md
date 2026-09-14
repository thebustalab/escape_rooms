Checked the worker's claims against the tree rather than the write-up.

**Verified:**
- `nets` carries `motion.moves` + `vigour` + `phrase`, so `_has_authored_mover` (`Utilities/long_agent/long_agent.py:3549`) returns true and the RENDER branch at :3926 will not refuse it.
- The committed 3072×1024 still genuinely depicts the mover: two floor-length net panels lifted clear of the open sashes, mid-billow across the boards, spanning roughly x≈0.28–0.48 of the panorama. **Bounded, not frame-filling** — the rest of the room (stair, jewellery trays, terminal, mirror, fallen lamp, both doorways) is static. Hanging cloth, the strongest confirmed mover category.
- `render_motion_prompt` yields exactly: *"locked-off static camera, zero camera movement. The net curtains billowing inward and falling back on the night air. Only that moves; everything else stays perfectly still. Seamless natural loop."* — mover-only, oscillatory, no travel, no re-description of the scene.
- No `a_townhouse` artefacts exist in `temp/cine/_art_prompt_exp/heist` — 0 files. Nothing rendered yet, so RENDER is the correct beat and the never-rendered veto is not in play.
- End guide 0.70 is `cine_room.py:101`'s default, not a proposed change. No settings lever is touched anywhere in the decision.
- The "NONE" motion prompt is indeed just the absent `.txt`; `exp_art_prompt.py:81-89` falls back to the spec. (Small imprecision in the worker's phrasing — the fallback lives in `exp_art_prompt`, not the runner's RENDER branch — but the substance holds: the prompt derives from the spec, not from hand-written text.)

**Its stale-prompt note is also correct and correctly left unacted:** committed `scenePrompt` is 1876 chars, current `render_prompt` emits 3215, missing the EQUIRECT/style/edge blocks. RENDER does not rewrite `scenePrompt` (only the author/adjust branches do, at :3881), so there is no overwrite risk this cycle — and re-authoring would spend the room's render budget on art that visibly works.

Nothing in the reject list fires.

VERDICT: PASS