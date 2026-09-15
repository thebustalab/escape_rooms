I checked each load-bearing claim against the files rather than the writeup.

**Verified**

- **The stale `.txt` vs. the real prompt.** `art_prompt_motion/beacons/sisters.txt` does still hold the old cloud sentence — but I resolved the actual render path myself: `cine_room.py:137` invokes `exp_art_prompt.py --arms motion`, and `exp_art_prompt.py:319` feeds that arm `motion_prompt(scenario, room, room_rec)`. Running it on the live record returns exactly *"locked-off static camera, zero camera movement. The row of marker flags on their cord lifting and running along the line, the nearest ones snapping. Only that moves; everything else stays perfectly still. Seamless natural loop."* — 35 words, one mover. The spec-wins precedence is a deliberate 2026-09-13 change with a test pinning it.
- **The negatives trap.** This was the claim most worth breaking, because `cine_stage.render_state:40` — the *shipping* path — calls `MS.render_negative(spec)`, and sisters' `motionSpec.negatives` does ban "flags, pennants, bunting". But that feeds `arms["spec"]`, and this loop requests `--arms motion`, whose negative (`exp_art_prompt.py:169`) is camera/quality terms only. The mover is not suppressed on the path that will actually run.
- **The art.** I opened the committed `scene.png` (3072×1024, written 22:00) and cropped the lower left at native scale. The flag line is genuinely there and near — weathered red and bone cloth on a cord between iron stakes, the nearest flag large in frame, bounded to roughly the left quarter of the width and well short of frame-filling. Fire-basket is cold and unlit, cloud river and spyglass intact. The worker's "~15% of frame width" is a little conservative; nearer 25%, which is still bounded.
- **No clip for this art.** The `_art_prompt_exp/beacons` sisters clips are all Sep 10 under `cal50`/`cal60` tags, and the room's `cine_base.mp4` is Sep 7 — all predate the Sep 14 22:00 still. `art` is `{}`.
- **No settings lever.** 0.70 is `cine_room.py`'s own default end guide, not a change.

Nothing on the reject list holds: no settings change, no frame-filling mover, no zero-return reasoning, no clip acceptance or writes to committed art, no hand-written prompt, and the mover has never been rendered so AUTHOR_MOVER would have been wrong.

VERDICT: PASS