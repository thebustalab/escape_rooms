I checked the worker's claims against the code, the live spec, and the clip itself rather than its summary.

**Verified:**
- `rooms/flat_clustering/heist/scenario.json` → `a_opera` elements: index 3 is a bare `{"rigid": ...}` with no `id`/`at`/`desc`. Cycle 64's fragment did land as an inert element, exactly as described. `long_agent.py:3886-3899` confirms why: only `str`/`list` sets `spec["rigid"]`; a dict without `"elements"` goes to `els.insert(len(els)//2, frag)` — 6 elements at the time → position 3.
- Top-level `spec["rigid"]` still reads "…and both curtained doorways" — the wording cycle 64 proved insufficient. Rendering `render_motion_prompt` from the live spec reproduces the old clause verbatim. The pin is unfixed.
- Simulating the proposed bare-string fragment: `json.loads` → str → `spec["rigid"]` → `rigid=True` at `exp_art_prompt.py:98` → the drape clause appears in the motion prompt, and every item the old clause pinned (parapet, walls/mouldings, tiers, writing-slope, terminal, lighter, both doorways) is retained. Nothing dropped.
- `render_prompt(spec)` is byte-identical before/after — confirmed by diff, so `scene.png` stays valid art.
- The SPEC line parses cleanly: only one line in the worker's output starts with `SPEC:`, the body is a single-line quoted JSON string with no internal quotes, and the `\nWHY:` cut lands correctly.

**The frames back the diagnosis.** Cropping x≈0.63–1.0 across the loop: at the start both right-hand doorways are open — one showing the lit corridor and mirror, the other the marble grand stair — and by the late frames the velvet portière drapes have swept fully across, closing both openings. Two clickable exits occluded. That is the motion at x=0.72–0.84, not the authored swag at x=0.20.

No rejection criterion fires: no settings lever, no frame-filling mover, no zero-return reasoning (return is 0.43 anyway), no clip acceptance, no committed-art or hotspot write, no hand-written art prompt, not AUTHOR_MOVER.

One caveat the worker itself raised and I confirm: the apply branch sets `needs_still = True` unconditionally, and the `RENDER` branch parks on it — so the room is already blocked on a manual harness still-regeneration from cycle 64. That block is spurious for a rigid-only edit, but it predates this decision and the byte-identical art prompt means the existing still remains correct when a human clears it. This decision does not worsen that.

VERDICT: PASS