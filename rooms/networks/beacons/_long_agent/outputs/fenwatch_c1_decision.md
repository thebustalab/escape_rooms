Read all four. Here's what I found.

**The spec is already right, and the art already carries it.** I rendered the two mover regions out of the committed still (rooms/networks/beacons/fenwatch/scene.png, 3072x1024) and looked at them:

- **chimney_smoke** — a broad dense plume rolling out low and heavy over the slate roof, close at hand, occupying maybe a quarter of the frame width. Bounded, and chimney smoke is on the ledger's confirmed-mover list.
- **river_mist** — a distinct low band lying along the braided river, left of centre, well under the peaks. I went in expecting hood's frame-filling failure; it isn't that. It's a strip, not a sea.

Both carry authored vigour in their `desc`, and both carry `motion.{moves,vigour,phrase}`, so `_has_authored_mover` sees them.

**One thing in the brief is stale.** The motion prompt quoted to me ("The white woodsmoke rises from the chimney…") is the legacy `art_prompt_motion/beacons/fenwatch.txt` fallback. Since the spec declares movers, the renderer resolves from the spec instead, and that gives a clean 44-word two-mover prompt:

> locked-off static camera, zero camera movement. The low band of river mist drifting slowly down the valley and tearing open in slow patches over the gravel bars; the broad near chimney plume rolling out heavily over the slate roof and leaning away downwind. Only those move; everything else stays perfectly still. Seamless natural loop.

Separate movers, separate phrases, joined with "; " — the fenwatch/anvil/crown duplicate-sentence bug is not present.

The old "fenwatch is dead" evidence is all 1536 probe work (`compare_scr70_fenwatch.mp4`, the 16-seed cluster), which the pipeline forbids deciding on, and the ledger's own counterweight is that fenwatch produced two accepted clips under the `living` template. Nothing here justifies spending a generation on new art before a single 3072 render has been tried.

DECISION: RENDER
WHY: The spec carries two bounded movers with authored vigour, the committed still visibly depicts both, the spec-derived motion prompt is correct and correctly de-duplicated, and no clip exists at deployment resolution yet — so the one render at the default is the next step, not re-authoring.