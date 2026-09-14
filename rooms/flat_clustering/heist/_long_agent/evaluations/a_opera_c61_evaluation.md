I checked each load-bearing claim against the disk rather than the write-up.

**Verified:**
- Clip `a_opera_motion_ri20_looped.mp4` exists, baked **2026-09-13 20:04:39**; render log confirms return 0.13, glitch breadth 0.0, "survived gates — needs Lucas's eye" (not accepted).
- `a_opera/scene.png` committed **22:24:17** — 2h19m *after* the bake. The still is genuinely newer than the only clip.
- Committed `scenePrompt` is 3129 chars and `scene_spec.render_prompt(sceneSpec)` reproduces it **byte-identically** (`p == a['scenePrompt']` → True). The spec is the live source of the committed art.
- The pre-feedback snapshot (`scenario.json.bak_20260913_220146_lucas_feedback`) carries an **1834-char** prompt, `rigid: None`, and a lighter described as "lying close to the viewer and la[rge]". So ri20 animates the superseded panorama with the oversized lighter and no rigid escalation — materially different art.
- `exp_art_prompt.py:98` does trip on the `rigid` string; the motion prompt it builds reads "…the panelled walls and their mouldings … are rigid and fixed — they do not warp, drift, breathe…", which is the direct fix for the breathing-wall note. The source comment at that line names a_opera's wall as the bug that made the escalation reachable.

**Against the reject list:** no settings change (3072×1024 / end guide 0.70 is what `params.json` already records as standard, not a proposed lever); one bounded mover (`swag`, box mouth, left) not a frame-filler; the 0.13 return is never used as proof of death — the argument is staleness, not deadness; no clip accepted and nothing written to committed art or hotspots; the prompt is rendered from the spec, not hand-written; and it is RENDER, not AUTHOR_MOVER.

The decision is sound: this art has never been rendered, and judging the mover without a clip of the current still would be guessing.

VERDICT: PASS