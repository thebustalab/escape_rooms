Read the four evidence files, then checked the render rather than the report.

**One thing in the cycle header is a red herring.** The "Current motion prompt" shown is the cloud-river sentence from `cinemagraph_tools/art_prompt_motion/beacons/sisters.txt` — the *fallback*. The runner's `fmt_vars` reads that `.txt` unconditionally (`long_agent.py:4088`), but the renderer resolves spec-first (`exp_art_prompt.py:86-105`). The spec actually emits:

> locked-off static camera, zero camera movement. The row of marker flags on their cord lifting and running along the line, the nearest ones snapping. Only that moves; everything else stays perfectly still. Seamless natural loop.

So ri35 was driven by the flag line, not the cloud. The stale `.txt` is display-only (sisters' mover was authored by the batch re-author, not by an AUTHOR_MOVER decision, so nothing ever rewrote it).

**Where the motion actually is.** Per-column/per-tile temporal std over the raw render:

| | |
|---|---|
| peak tile | x=0.19, y=0.69 — the `marker_line` position (`at: "to the left"` → 0.20), low and near |
| peak : frame median | **25.2x** (rams_head, held, was 13.2x) |
| extent | x∈[0.06,0.30], y∈[0.55,0.95] — bounded, not frame-filling |
| x≥0.33, incl. col_cloud at 0.64 | flat at the 0.16–0.21 noise floor |

The old frame-filling cloud river is not what moved; the authored bounded mover is, and nothing else is above noise. The committed still (22:00, newer than the clip) genuinely depicts the flag line — near, large, two iron stakes, faded red and bone white.

All three gates cleared: camera still; glitch breadth 0.167 raw / 0.083 normalised, both far under the 0.70-on-both threshold; return 0.03 is the ambiguous flag only. A wave running *along* a flag line never returns pixel-wise — the same cyclic-flow signature as rams_head (0.02) and b_casino's smoke (0.00), and peak 10.36 sits with spindle's 10.78 and rams_head's 10.18, both held.

```
DECISION: HOLD
WHY: The clip cleared all three reject-only gates and its motion is bounded and confined to the authored marker-flag line at 25.2x the frame median with every other region — including the old cloud river — at the noise floor, so the 0.03 return is the documented cyclic-flow signature of a wave travelling along a line and there is nothing left for the loop to fix.
```

Two things for your eye when the page comes over, neither a loop action: the flags in the still hang slacker than the authored vigour asked for (it animated anyway, so I did not spend a regeneration correcting it), and that stale `sisters.txt` fallback is worth deleting or rewriting so a future cycle isn't shown a prompt the renderer will never use.