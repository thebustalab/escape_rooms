I've read the pipeline, the report, the ledger sections that bear on fenwatch and the return metric, and `render_prompt` — plus the cycle-1 decision, the render log, and the frame strip the render already produced.

**What the evidence says.** The clip cleared every gate that may reject: camera `still` (frame0_corr 0.908, landmark drift 0 px, loop jump 2.72), and glitch breadth 0.104 on both readings against a threshold of 0.70 — nowhere near. The only flag is `return 0.00`, which the ledger is explicit about: it is a **monotone-drift detector, not a liveness test**, it is ambiguous between dead and cyclic flow, and it has already been wrong about three good clips. Both of fenwatch's movers are flow-type — mist drifting down-valley, a plume rolling out and leaning downwind — and a flowing mover never returns to its starting configuration pixel-wise, so 0.00 is what b_casino's smoke and logwood_verdigris's water measure while looping perfectly.

The frame strip resolves the ambiguity in the direction the gate could not: the chimney plume is a different shape in all three frames — a tall puff at frame 0, thinned and leaning right mid-loop, re-formed by the last — and the mist band over the river visibly spreads and re-settles. That is depicted motion, one cycle per loop, not a one-way creep. Peak 8.09 is uninformative on its own (alive fenwatch measured 8.7, dead 9.3 at 1536), so I'm not leaning on it.

Nothing here justifies re-authoring art, and nothing justifies a softening pass — the fix ladder's "too lively" rung is an eye judgement and no gate raised it.

```
DECISION: HOLD
WHY: The clip cleared the camera and glitch gates outright and the only flag is a 0.00 return, which the ledger defines as ambiguous rather than fatal — and the render's own frame strip shows the plume changing shape and the river mist spreading and re-settling across the loop, which is the cyclic-flow case that measures 0.00 by construction, so this is a question for Lucas's eye, not a reason to spend art or a render.
```

**Note for the handover:** the motion prompt quoted in this cycle's brief ("The white woodsmoke rises from the chimney…") is still the legacy `art_prompt_motion/beacons/fenwatch.txt` fallback text. The render resolved from the spec, as it should — the two-mover, correctly de-duplicated prompt. The stale `.txt` is harmless but worth deleting so it stops being quoted as if it were live.