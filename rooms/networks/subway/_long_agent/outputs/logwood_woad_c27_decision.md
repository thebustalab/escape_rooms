I've read all four. The evidence settles this one without a new experiment.

**The gate report is a clean sweep with one known-ambiguous flag:**

| gate | reading | threshold | verdict |
|---|---|---|---|
| camera | `still` | — | pass |
| glitch | breadth 0.104 / normalised 0.042 | reject at ≥0.70 on **both** | pass, by a wide margin |
| dead | ratio 7.83, peak 6.84 | reject below 1.75 / 0.45 | pass, ~4.5x clear |
| return | 0.00 | never rejects — escalates | the flag |

The zero return is the one thing outstanding, and this room is the textbook case for it. `logwood_verdigris` — the sibling platform in this same station, reached by the spiral stair in this very spec — is one of the two labelled rooms that defined the correction: water flow, return 0.00 at both 0.70 and 0.65, and Lucas's own verdict that *"their movements are not an out-and-back thing, their movements are a cyclic thing with one full cycle per loop."* `woad`'s mover is the same mover: sheets of water sliding down a wall into a channel. A flowing mover never returns to its starting configuration pixel-wise.

The peak-amplitude tell — the four-point separator recorded in the ledger — agrees. Live cyclic movers measured 8.06–9.35; genuinely dead hood high-pin clips sat at 5.1–5.2. This clip peaks at 7.57, in the live band, and the dead gate independently reads 7.83 wander ratio against a 1.75 floor. Two separate measures say motion is present; only the one that was never designed to detect motion says nothing happened.

Re-authoring the art here would be acting on the exact false reading the ledger records as retracted. The clip is not accepted — no metric may do that — it goes to the eye.

```
DECISION: HOLD
WHY: The clip cleared camera, glitch and dead gates outright, and its 0.00 return is the known cyclic-flow ambiguity — the same water mover and the same score as sibling logwood_verdigris, which Lucas judged alive with a good loop — corroborated by a live-band peak of 7.57 and a dead-gate wander ratio of 7.83, so it goes to his eye rather than back to the art.
```