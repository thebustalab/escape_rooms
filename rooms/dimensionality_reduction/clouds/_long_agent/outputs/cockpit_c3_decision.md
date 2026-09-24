I've read the four authority documents and inspected the room. Here is the state I verified:

- **Spec carries two authored movers**, both matching the human guidance exactly: `city` (brightening and dimming in place) and `eyewall` (lightning rippling through the storm). Each has `motion.{moves,vigour,phrase}`; the retired heroes (sampler bloom, drogue kite, etc.) are gone — `sampler` now carries only a `sound` block, no motion.
- **The motion prompt resolves from the spec**, 38 words, house form, both phrases joined, closing on "Only those move": *"locked-off static camera, zero camera movement. The floating city brightening and dimming in place, its lit buildings swelling and fading; lightning rippling slowly through the storm cloud. Only those move; everything else stays perfectly still. Seamless natural loop."* Both movers are purely oscillatory light — the no-travel rule is satisfied by construction.
- **The still is current and depicts both movers.** `scene.png` was committed 07:01 today from the rewritten spec (spec edit 06:59:39), seam-staged clean at band run 0.008. Looking at it: the lit city heap fills the left, white-blue lightning crawls the eyewall on the right, grey palette written in, and the dash/sampler/reading-pane/override sit sharp in the foreground.
- **Seed 4711 and end guide 0.70 are already pinned** in `plan.json`, matching Lucas's approved recipe.
- **No clip exists for this generation** — gate report is `{}`, nothing tried. The `.cine_published.json` entry for cockpit predates today's rewrite.

Both movers are light-modulation, each bounded to its own half of the frame — the same category as `heist/a_vault`'s caged lamp, which Lucas accepted, and not `hood`'s frame-filling drifting cloud sea. Nothing here calls for re-authoring, and the guidance forbids it regardless.

DECISION: RENDER
WHY: The spec carries the two approved light movers with authored vigour, the spec-derived motion prompt renders clean at 38 words with no travel, the still is fresh from this spec and visibly depicts both, and no clip exists yet at the pinned seed 4711 / end guide 0.70.