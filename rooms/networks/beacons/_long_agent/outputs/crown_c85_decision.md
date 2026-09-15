Everything the pipeline requires is already in place, and the still confirms it.

**What I checked:**
- **The spec declares a bounded mover with authored vigour.** `dispatch_pennant` carries a full `motion` block (`moves`/`vigour`/`phrase`), so `_has_authored_mover` sees it — it is not one of the legacy `animate`-only elements.
- **The still is fresh and depicts that mover.** `rooms/networks/beacons/crown/scene.png` is dated today 02:30, after the spec edit (scenario.json 02:31 is the same authoring pass), and the crop at the pennant's authored position shows exactly what was written: a rust-orange pennant on a varnished staff stepped into the summit cairn, streaming out level and taut with the free end curling over. Bounded — a narrow upright slice near the viewer, not frame-filling.
- **The motion prompt resolves from the spec, not the stale `.txt`.** `render_motion_prompt` returns a 33-word, one-mover prompt in the house form. The `art_prompt_motion/beacons/crown.txt` fallback still says "guyed mast", which contradicts the spec's own negatives (no rigging or guy-lines) — but it is unreachable now that the spec declares a mover, so it is inert, not a fault to fix here.
- **The existing `cine_base.mp4` is from Sep 7**, i.e. the pre-re-authoring still. Consistent with the empty gate report: no clip exists for this art.
- The ledger records crown's pennant as one of the three re-authoring successes ("Ochre and crown worked"), so this is a room whose expected outcome is known.

No fix is warranted before a clip exists: `SOFTEN_PROMPT` and `PIN_NON_MOVERS` both need a rendered clip as evidence, and re-touching `vigour` would discard a panorama that already depicts the intended initial condition.

DECISION: RENDER
WHY: The still is freshly generated from the current spec and depicts the bounded dispatch pennant at its authored vigour, the spec-derived motion prompt names that one mover in 33 words, and no clip exists for this art yet.