I verified the worker's diagnosis independently, and then checked what the runner would actually do with the fragment.

**The diagnosis is right.** I measured the raw render myself rather than trusting either the gate note or the worker:

- Temporal-std map, 64 px blocks, bottom two rows excluded: kiln peaks at **1.6× median**. The same measurement on live siblings — shears 9.3×, rams_head 7.8×, anvil 7.5×, whistlegate 6.3×. An order of magnitude apart.
- The plume region itself reads **0.89× median** — below the noise floor, below even bare rock at 1.16×.
- By eye at native crop, frames 0 / 36 / 72 hold the same forks, the same kink, the same gap between lobes. Three seconds of smoke would have reorganised.

Dead, not cyclic. The worker did not lean on the zero return, and AUTHOR_MOVER is the right verb — the mover was genuinely rendered at cycle 75.

**But the SPEC fragment is keyed wrong, and the runner's merge is defective on it.** `long_agent.py:4183` matches the fragment to an element by `at` **alone**, taking the first hit. Two elements in the kiln spec carry `at: "to the left"`, and the door comes first:

```
1 'to the left' | id= path_broken_tooth | door= broken_tooth
2 'to the left' | id= juniper_smudge     | motion= True
```

I applied the fragment through that code path against the live `rooms/networks/beacons/scenario.json` and rendered both prompts. The result:

- **The motion prompt names two movers** — "The dense column of juniper smoke … ; the rope of juniper smoke climbing and rolling from the smouldering dish". The old wisp survives untouched at index 2 because the merge landed on index 1. That is precisely the failure mode the re-author exists to avoid.
- **The art prompt loses the path north to The Broken Tooth.** "Broken Tooth" and "north along the easy crest" no longer appear anywhere — the door element's `desc` was overwritten by the smoke text while its `label` and `door` survived. The art prompt now describes two juniper dishes and no north path.
- `render_prompt` changed, so `needs_still` fires and the committed still gets regenerated from that corrupted spec — with a live door that nothing in the frame depicts.

The worker's claim to have "verified both prompts build from the edited spec" can't have gone through the runner's merge; it must have tested a spec edited directly.

The fix is small — the fragment should carry the full `elements` list (which takes the wholesale-replace branch at line 4180) or otherwise disambiguate, since `at` is not unique here. But the action **as handed to the runner** damages committed authoring, so it must not be acted on this cycle.

VERDICT: FAIL