Read the pipeline, report, ledger and `render_prompt`; then went to the evidence rather than re-running anything.

**What I found.** The clip `whistlegate_motion_ri65.mp4` (seed 4242, eg 0.70, 73 frames, 3072x1024) cleared all three reject-only gates: camera still, glitch breadth 0.146 raw / 0.083 normalised against a 0.70-on-both threshold. The only flag is the ambiguous zero return.

A tile map of temporal std on the **raw** render (median tile std 1.651) resolves the ambiguity:

- **11.4x / 10.6x / 7.1x / 6.0x median** in one contiguous vertical column at **x 0.29–0.33, y 0.00–0.62** — that is exactly the big black kettle at a hard boil and its plume, the spec's `hearth_kettle` mover. I confirmed it against the committed still.
- A second, weaker column at x 0.54–0.58 (2.3–3.3x) — the *other* hearth's plume.
- Everything else at the noise floor: the top-20 tile list runs out at 1.7x. Table, dispatch sacks, ledgers, desk, walls, both doorways and both seam edges are all still.

The per-frame diff curve rises to ~2.9 by frame 13 and then plateaus with small oscillation to 3.13 at the end — a rising plume, not one-way drift. That is the documented cyclic-flow zero, the same reading `rams_head`, `hood` and `ladder` were held on in this run.

Two things worth recording for the eye rather than acting on:

- The "current motion prompt" on the table is the **stale `.txt` fallback**, not what rendered. `exp_art_prompt.py:86` prefers the spec, and the spec renders *"…the plume of steam standing up from the boiling kettle over the hearth fire, and the flames working under it. Only that moves…"*. The tile map agrees — the strongest motion is the kettle plume the spec names, not the flue smoke the `.txt` names.
- The still depicts **two** hearths, each with a kettle and a plume: the authored `hearth_kettle` and the older `hearth` element, which still carries only a legacy `animate` block. Both plumes move. Nothing that should be still is moving, so this is not a `rigid` case — but it is a scene-coherence question for Lucas, not a gate failure.

Peak 7.93 is the lowest in the beacons set (the others run 9.0–13.9) and sits just under the known-live cyclic band's 8.06, though well clear of the 5.1–5.2 dead band. The tile ratio is the stronger signal and it is unambiguous.

DECISION: HOLD
WHY: The clip cleared all three reject-only gates and its motion is bounded and confined to the authored kettle plume at 11.4x the frame median with every non-mover at the noise floor, so the zero return is the cyclic-flow signature of rising steam rather than death and nothing is left for the loop to fix.