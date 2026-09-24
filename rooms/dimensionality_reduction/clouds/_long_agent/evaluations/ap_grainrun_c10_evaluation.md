I verified each claim against the artifacts rather than the worker's write-up.

**Confirmed independently:**

- **Clip is real and complete** — `ap_grainrun_motion_ri8_looped.mp4`, ffprobe: 3072×1024, 24 fps, 61 frames looped / 73 raw. Baked 07:40 from the scene.png committed 07:24.
- **Params are the settled recipe** — `ap_grainrun_motion_ri8.params.json`: seed 4711, end_guide 0.7, cfg 2.0, steps 8, length 73, 3072×1024 — byte-for-byte the same params block as the cockpit run Lucas approved.
- **Motion prompt is spec-derived, not hand-written** — I re-rendered it myself via `exp_art_prompt.motion_prompt()` from the live `scenario.json`: 38 words, and *character-identical* to the cockpit prompt. Contains only the city brightening/dimming and lightning through the storm. No retired hero mover.
- **The glitch-gate reasoning matches the code.** `cine_room.py:76` gates on `min(raw, normalised) >= 0.70`. min(0.521, 0.875) = 0.521 → not glitched. The comment at line 29 names a_vault's light-mover false positive (0.896 raw) as precisely the case the two-reading rule exists to defuse — this room's movers are lights, so the worker's read is the intended one, not a rationalisation. Return 0.65 is far above `RETURN_ALIVE = 0.05`, so the ambiguous zero-return path never fires and is not being misused. Dead false.
- **The still and filmstrip back it up.** The still shows the city low and left receding into distance, the storm wall right, charcoal vapour in front, and the dash sharp with globe, reading-pane and six cells. The ×8 difference panel of the filmstrip puts the motion in the storm wall and the city lights, with the dash reduced to faint edge residue — the movers are bounded, nothing frame-filling.
- **Nothing is being accepted or committed.** `scenario.json` still has `art: None`, no clip key, `seam.accepted: false`, zero hotspots. HOLD stages to the candidate pool only, as the cockpit precedent did.

None of the reject conditions apply: no settings change, no frame-filling mover, no zero-return-as-dead, no acceptance, no hand-written prompt, no AUTHOR_MOVER on an unrendered mover.

VERDICT: PASS