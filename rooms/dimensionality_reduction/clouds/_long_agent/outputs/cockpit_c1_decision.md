I read the four authority documents, then checked the room against them.

**What I found:**

- **Bounded mover: present and authored.** The `sampler` element carries a full `motion` block — `moves: true`, vigour "slow and calm, a gentle drift and pulse", phrase "the captured cloud-garden bloom drifting, turning and pulsing slowly inside its glass sampler globe". That's the only element with one, so `_has_authored_mover` resolves and the room isn't invisible to the loop.
- **The still actually depicts it.** I looked at the committed `cockpit/scene.png` at native 3072×1024. The glass globe sits on the dash just left of centre, holding a distinct glowing white-gold bloom — roughly 1.4% of the frame. That is squarely inside the range egypt's accepted clips proved alive (deck_lamp at 0.78%, quay's boats at 6.76%). Bounded, not frame-filling; the storm and the city are big but nothing names them.
- **The still is not stale.** `scene_spec.render_prompt` on the current sceneSpec is byte-identical to the committed `scenePrompt` (10,352 chars both), and the spec is unchanged from `scenario.json.bak`. No clip would be animating art that predates its own motion prompt.
- **The motion prompt resolves from the spec.** "Current motion prompt: NONE" just means no fallback `.txt` — the spec is the source of truth and renders: *"locked-off static camera, zero camera movement. The captured cloud-garden bloom drifting, turning and pulsing slowly inside its glass sampler globe. Only that moves; everything else stays perfectly still. Seamless natural loop."* 32 words, house form, one mover, purely oscillatory — drifting/turning/pulsing inside a globe has no net path, so the no-travel rule is satisfied.
- All seven `at` values map cleanly through `_x_from_at` (0.08 → 0.92), none falls through.

Nothing needs re-authoring, softening or pinning. The spec is right, the prompt is right, the art carries the mover, and no clip exists yet.

DECISION: RENDER
WHY: The sceneSpec already carries one bounded mover with authored vigour — the sampler globe's bloom — the committed still depicts it at a size proven to animate, the spec-derived motion prompt is well-formed and travel-free, and no clip has been rendered yet, so the next step is the single render.