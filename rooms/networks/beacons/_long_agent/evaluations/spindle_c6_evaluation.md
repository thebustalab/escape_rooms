I pulled the raw render myself rather than take the write-up on trust.

**What the frames show.** Cropping the needle across frames 0/18/36/54/72, the spindrift plume genuinely restructures — a broad wash at the start, distinct torn banners mid-clip, different again at the end. That is real, visible, structured flow, and it stays skirted to the one slender rock feature the spec names. Bounded, not frame-filling.

**The static furniture holds.** The iron fire-basket and the drystone platform are stable frame to frame; their numerically high per-pixel change is fine-detail shimmer, not geometry morph — which is the exact perceptual point in the calibration note.

**The numbers check out.** I verified the glitch rule in `cine_room.py:44,77` rather than accepting the worker's figure: rejection fires on `min(raw, normalised) >= 0.70`, and this clip is `min(0.500, 0.458) = 0.458`. Clears with room. And `cine_return_check.py`'s own docstring names the cyclic-flow case explicitly — b_casino's smoke and logwood_verdigris's water, both 0.00 and both alive. Spindrift is that same flowing mover; it never returns to its start configuration pixel-wise.

The decision is HOLD — park it for your eye. It accepts nothing, writes nothing to scenario.json, changes no settings, and doesn't re-author a mover on a metric the ledger has already retracted three times.

VERDICT: PASS