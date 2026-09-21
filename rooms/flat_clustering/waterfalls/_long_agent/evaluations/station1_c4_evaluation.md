The runner should render. I checked the still and the spec myself rather than relying on the worker's account.

- **Still:** `station1/scene.png` was regenerated at 08:27 today at 3072×1024. It shows the current night spec: cressets lit and no daylight. Both curtains of water are there and each stays inside its own frame: one falls through the gap over the down-ladder, just left of centre, and the other falls through the rope bridge on the right. Neither fills the frame.
- **Spec:** in `scenario.json`, only `down_ladder` and `across_bridge` have `motion` blocks, and each has `moves: true`, `vigour` and `phrase`. The other three elements have no motion, so there is nothing to author before rendering.
- **No earlier clip for this still:** the only station1 clip (`base__ri8`, from 00:01) was made from the old daylight still, before the night respec. These movers have never been rendered on the current still.
- **Nothing on the reject list:** the decision changes no settings, adds no frame-filling mover, doesn't rely on a zero return, accepts nothing, writes nothing into committed art or hotspots, and hand-writes no prompt.

"Motion prompt: NONE" is the same display gap catwalk's held clip showed. It's worth a look when the clip comes back, but it doesn't block the render.

VERDICT: PASS