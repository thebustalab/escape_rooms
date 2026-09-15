I read the pipeline, report and ledger, then checked the clip itself rather than the gate summary alone.

**What the evidence shows for `shears`:**

- The spec-derived motion prompt (`scene_spec.render_motion_prompt` on the live `sceneSpec`) names the spout and nothing else — 38 words. The stale cloud prompt in `art_prompt_motion/beacons/shears.txt` and the legacy `motionSpec` are not on the path `exp_art_prompt.py` takes (it reads `authoring.sceneSpec`, line 86).
- The committed still (23:48) genuinely depicts the mover — a near waterfall pouring off the left blade into a basin — and the clip (00:01) is rendered from it.
- Per-tile temporal std: peak **16.7x the frame median**, and the hot tiles form one vertical column at x≈0.10–0.20 running y 0.31→0.94. That is the spout, the fall and the basin, and nothing else. Same register as the four rooms already held this run (`sisters` 25.2x, `rams_head` 13.2x).
- The spout's own trajectory rises to a plateau in six frames and stays there — the documented cyclic-flow signature of falling water, which is exactly why the whole-frame return reads 0.01 and not because the clip is dead. `rams_head`, also falling water, returned 0.02 and was held.
- The one secondary mover is the braided river (mean 4.5 vs the spout's 11.7). It is an out-and-back — returns 0.51 locally — and its region brightness drifts −0.34 over the loop, so the water **level** is not rising or spreading. That is the thing the scenario's pin actually protects, and it holds. Pinning a river that flows correctly would spend a render and lengthen the prompt, which is the documented cause of camera drift.

Nothing is left for the loop to act on.

```
DECISION: HOLD
WHY: The clip cleared all three reject-only gates and its motion is bounded and confined to the authored blade_spout at 16.7x the frame median with the lens cloud at the noise floor, so the 0.01 return is the documented cyclic-flow signature of falling water rather than a dead clip, and the only secondary mover — the valley river — flows out-and-back at a fixed level and needs no pin.
```