I've read the four authority documents. Now checking this cycle's gate report against them.

**Gate-by-gate:**

- **camera: "still"** — passes. No drift.
- **glitch:** raw breadth **0.167**, normalised 0.896. The rule (pipeline §4, re-derived 2026-09-13) is reject only when **BOTH** readings ≥ 0.70. Raw is 0.167, far below. This is the `whistlegate` signature exactly — an accept that jumps sharply under brightness normalisation — which is the documented reason normalised-alone is not safe to gate on. `spike` 4.38 is reported, never enforced. **Passes.**
- **dead:** ratio 20.5 against a 1.75 floor, peak tile 19.36 against 0.45. Not remotely close. **Passes.**
- **return: 0.23** — non-zero, so the ambiguous-zero escalation doesn't fire. And 0.23 is the literal shipping precedent: `market_price` returns 0.23 and ships.

**Amount of motion:** peak 9.56 sits on this room's own measured vigour ladder (ledger, 2026-09-13: ochre_hall canvas slack 5.62 / gentle 9.91 / gale 13.44) right at the **gentle** rung. That is what the spec authored — "stirring only gently in the draught... slack rather than taut and never snapping" — and what the motion prompt asks for, "no more than a slow soft breathing of the cloth". The render matches the authored intent, so there is nothing to soften and nothing to re-author. `ochre_hall` is also one of the three rooms the re-authoring experiment woke, so an authored-mover clip landing in its known-good band is the expected outcome, not a surprise.

Nothing here warrants touching the art, the vigour, the phrase, or a rigid clause — and per the rules, a passing clip is never mine to accept.

DECISION: HOLD
WHY: The clip cleared every reject-only gate — camera still, glitch raw breadth 0.167 well under the both-readings 0.70 rule, dead gate comfortably alive, return 0.23 at market_price's shipping level — and its peak of 9.56 lands on the gentle rung of ochre_hall's own measured vigour ladder, exactly the register the spec and motion prompt authored, so it goes to Lucas's eye rather than back to the art.