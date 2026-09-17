Every gate cleared, and the numbers sit inside ochre_hall's own documented good band.

**Reading the gate report against the settled thresholds**

- **Camera** — `still`. No drift; nothing to pin.
- **Glitch** — rejection needs `min(raw, normalised) >= 0.70` (`cine_room.py:77`). Here min(0.167, 0.896) = **0.167**, far clear. The high normalised reading with a low raw one is the exact `whistlegate` shape the ledger records as a known false positive of the normalised reading alone — which is why both are required. Not a glitch, and per the loop's rules not mine to re-roll anyway.
- **Dead** — ratio 20.5 against a floor of 1.75, peak tile difference 19.36 against 0.45 (`cine_dead_check.py:32`). Alive by an order of magnitude, not marginal.
- **Return** — 0.23, non-zero, so no dead-or-cyclic escalation. `market_price` returns 0.23 and ships.
- **Peak 9.56** — ochre_hall's own authored-vigour ladder measured 5.62 slack / 9.91 gentle / 13.44 gale, and its intensity ladder 7.15 for "ripples very gently" against 11.64 baseline. 9.56 lands between the gentle and baseline registers, which is exactly where the spec's authored intent ("no more than a slow soft breathing of the cloth") aims. No case for softening, and softening is the only direction that lever works in.

Nothing here supports a spec change. The room has one bounded mover (the short run of dust-sheeting, `lock: true`, with both `vigour` and `phrase` authored), the still was regenerated from that spec last cycle, and the clip that came back is in the register the art asked for. The gates are reject-only and none rejected — which is a question for Lucas's eye, not an answer.

```
DECISION: HOLD
WHY: The clip cleared every reject-only gate — camera still, glitch min(0.167, 0.896) well under the 0.70 both-readings rule, dead gate clear by 20.5x/19.36 against 1.75/0.45, return 0.23 non-zero — and its peak of 9.56 sits inside ochre_hall's measured gentle-to-baseline band, matching the authored vigour, so there is nothing to soften, pin or re-author.
```

A note for whoever reads the verdict file: the 0.896 normalised breadth will look alarming next to a 0.167 raw one, but that pairing is the documented accept signature, not a defect — it should not be re-litigated next cycle.