I read the four evidence documents, then verified the room's actual state rather than trusting the summary.

**What I found:**

- `movers(spec)` resolves to `['drapes']` — the spec carries a full `motion: {moves, vigour, phrase}` block, so `_has_authored_mover` can see it (heist is on the migrated list).
- `render_motion_prompt` produces a clean, house-form, single-mover prompt from the spec: *"locked-off static camera, zero camera movement. The silk drapes lifting and falling steadily in the dawn breeze. Only that moves; everything else stays perfectly still. Seamless natural loop."* The "Current motion prompt: NONE" in the brief just means no `art_prompt_motion/` fallback file exists — which is correct, the spec is the source of truth now.
- The committed `scene.png` (3072×1024) **depicts the mover**: I opened the left third. Long sheer silk drapes and swagged gold-fringed bunting rigged along the deckhouse, occupying roughly the left quarter of the frame — bounded, not frame-filling, and hanging cloth is the strongest confirmed mover category in the ledger (p95 to 76.8). The cached prompt already carried the vigour clause, so the still was generated from the authored vigour, not retrofitted.
- No clip exists, gate report is empty, nothing has been tried.

One thing I'm noting but deliberately not acting on: `authoring.scenePrompt` is one of the **stale cached prompts missing the EQUIRECT clause** (and the style/edge-discipline blocks). Regenerating is the expensive lever, reserved for a dead clip — and this still passed a native-resolution human-grade seam evaluation on 2026-09-05. Burning it before a single render would be tuning the art against a problem that hasn't appeared.

DECISION: RENDER
WHY: The spec declares one bounded mover (`drapes`) whose vigour is authored, the committed 3072 still visibly depicts it as hanging silk cloth on the left quarter of the frame, and `render_motion_prompt` yields a correct single-mover house-form prompt — so the spec and prompt are right and no clip exists yet.