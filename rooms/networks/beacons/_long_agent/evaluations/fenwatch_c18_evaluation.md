**The reasoning is right. The payload is wrong, and it fails silently.**

I re-measured the raw clip myself rather than trusting the table, and the worker's diagnosis holds:

| region | peak | peak at | return |
|---|---|---|---|
| pour + butt | 19.24 | **f35** | **0.13** |
| centre office | 9.33 | f72 | 0.00 |
| right seam wall | 9.96 | f72 | 0.00 |
| left seam wall | 7.62 | f72 | 0.00 |
| sky | 1.21 | — | 0.00 |
| whole frame | 8.58 | f70 | 0.00 |

The mover is genuinely alive and cyclic, peaking mid-clip. Every stone region peaks on the final frame and never returns, while the smooth sky stays quiet — a non-rigid warp on textured surfaces, not an exposure shift. `PIN_NON_MOVERS` is the correct decision, it is not on any reject list, and the mover has been rendered (cycle 16 → `ri16`).

**But the SPEC will not do what it says.** The runner (`long_agent.py:4170`) recognises the rigid list only as a **bare JSON string or a list** — its own comment says so: *"a list or a bare string is that, not an element."* A dict falls through to the element branch. I ran the runner's exact apply logic against this spec:

- `at` resolves to `None`, no element matches, so `{"rigid": "..."}` is **inserted into `spec["elements"]` as a junk 10th element** with no `at` and no `desc`, and that corrupted spec is written back to `scenario.json`.
- `spec["rigid"]` is **never set**. The re-rendered motion prompt comes out byte-identical to the current one — no rigid clause at all.
- The art prompt is unchanged, so the runner logs *"PIN_NON_MOVERS applied"* and burns a full DGX render reproducing the same clip.

The same input as a bare JSON string applies cleanly: elements untouched, art prompt unchanged, and the motion prompt gains `"The drystone yard walls and cobbles, and the slate roof of the office range are rigid and fixed — they do not warp, drift, breathe, shimmer or change shape."` — which is precisely the two-item, ~68-word register the worker argued for.

The fix is one line on the retry: `SPEC: "the drystone yard walls and cobbles, and the slate roof of the office range"` (or a JSON array of the two items). Keep the decision and the reasoning; change only the wrapper.

VERDICT: FAIL