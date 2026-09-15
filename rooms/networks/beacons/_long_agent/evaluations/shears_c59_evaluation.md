I checked the frames and the spec directly. The worker's plumbing claims check out; its read of the clip does not.

**Verified correct:** the motion prompt does resolve from the live `sceneSpec` (not the stale `art_prompt_motion/beacons/shears.txt`) — 38 words, naming only the spout, `rigid=False`. `exp_art_prompt.py:86` does prefer the spec. The committed still is clean and does depict the authored mover.

**Refuted — the claim the decision rests on:** the worker states the hot tiles "form one vertical column at x≈0.10–0.20 … That is the spout, the fall and the basin, and nothing else," and that the only secondary mover is the braided river.

Frame 0 shows a brass spyglass on its tripod over the valley. By frame 15 a second, enormous water jet has erupted **from the muzzle of the spyglass**, arcing down across the valley and onto the platform. It is present through frames 15/30/45 and absent at frame 0, and it is not in the committed still.

Tile map over 61 frames (median tile std 1.381):
- left spout column, x 0.08–0.21 — 16–27x median ✔ the authored mover
- **x 0.60–0.62, y 0.62–0.75 — 11.2–13.4x median** ✘ the invented jet, ranking 20th/21st/24th of all tiles
- braided river, x 0.38–0.58 y 0.60–0.90 — **1.1x**, i.e. at the noise floor, not 4.5

So the secondary mover is misidentified on both counts: the river is essentially static, and the real secondary mover is a hallucinated duplicate of the authored spout grafted onto a different object. This is the exact failure class the pipeline's own comments name (verdigris' ceiling water, alum_madder's invented drops) — the model applied the "jetting… arcing down" phrase a second time, and `rigid=False` means no pins were active to stop it.

It also lands on content that matters: `spyglass` is a `clue: true` hotspot, and the arc occludes the nine villages of `valley_view`.

HOLD would leave this standing as "survived gates — needs Lucas's eye," presenting a clip with a water cannon coming out of the telescope as a candidate. The gate report's own warning was about calling good clips dead; here the eye finds the opposite problem — the clip is not dead, it is wrong.

The runner should not act on HOLD. The remedy is a re-render with the spyglass pinned (a `still_as` on `spyglass`, which also switches `rigid` on), not an accept and not a settings change — but that is the worker's next proposal to make, not mine.

VERDICT: FAIL