I verified the decision against disk rather than the write-up.

**What I checked myself:**

- **The mover, from `scenario.json`** — `logwood_verdigris`'s spec carries exactly one element with a `motion` block: `drip_tarp`, `just right of centre, close beside the viewer`, with an authored `vigour` and its own `phrase`. No other element has motion. One mover, closed-vocabulary position.
- **The prompt the renderer will actually use** — I called `exp_art_prompt.motion_prompt('subway', 'logwood_verdigris', rec)` live: it returns *"…The loose canvas sheet billowing gently and slowly in the draught from the tunnel, swelling and falling back. Only that moves…"* The stale `art_prompt_motion/subway/logwood_verdigris.txt` on disk still holds this room's historic drift case (the ceiling water) and is **not** what resolves. The worker attributes that to a hard-coded `SPEC_SCENARIOS` list; the test's own docstring says the discriminator is "does this spec declare movers." Same outcome here, so it doesn't move the verdict.
- **The still** — `scene.png`, 3072x1024, written 15:55 today. I looked at it. The tarp is plainly there: a pale oiled canvas sheet hung from a roof pipe just right of centre, hanging free of the wall with a loose hem, occupying roughly 7% of the frame width (the worker said a sixth — it's tighter than that, which only helps). It is a bounded mover, not frame-filling, and it hangs slack in a way that can billow at the authored register.
- **Freshness** — the same `drip_tarp` element and the identical phrase are already present in `scenario.json.bak` (15:55), so the still was rendered from a spec that carried this mover. No clip animating a stale still.
- **State** — `_long_agent/state.json` has `rooms.logwood_verdigris = {"art_generated": 1}`: no attempts, no history, no clip. Gate report empty because nothing has rendered.
- **Settings** — `plan.json` sets `end_guide: "0.70"`, and 3072x1024 is the still's own size. The worker is naming the configured defaults, not proposing a lever.

None of the rejection conditions hold: no settings change, the mover is bounded and depicted, no zero-return reasoning is in play (there is no clip), nothing is accepted or written into committed art or hotspots, the prompt comes from the spec rather than a hand-written string, and this is not `AUTHOR_MOVER` on an unrendered mover — it's the first render of one.

VERDICT: PASS