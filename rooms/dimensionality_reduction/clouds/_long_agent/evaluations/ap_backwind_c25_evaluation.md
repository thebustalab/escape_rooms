I checked each claim against the files rather than the worker's summary.

**Verified independently:**

- **Mover exists in spec.** `rooms[6].authoring.sceneSpec` element `derelict`, `at: "to the right"` (closed-vocabulary position), `motion: {moves: true, vigour: "loose and restless, billowing and snapping", phrase: "the derelict glider's torn membrane wing flapping and billowing in the wind"}`. The other six elements carry `motion: null`. One authored mover, as required.
- **Still is in sync with the spec.** `scene_spec.render_prompt(sceneSpec) == authoring.scenePrompt` returns True, and the EQUIRECT clause is present in the rendered prompt.
- **The art actually depicts it.** I cropped the native 3072×1024 panorama at x 0.68–0.92. A second glider rides alongside past the right wing: empty cockpit ring, dulled shell, one membrane wing intact and veined, the other visibly **torn** — holed, eaten-through, ragged trailing edge with lightning showing through the gaps. This is not a worker hallucination.
- **Bounded, not frame-filling.** The derelict spans roughly x 0.72–0.88 — about a sixth of the frame width, well clear of both edges and of the seam. The torn membrane itself is a smaller sub-region still.
- **Motion prompt is compliant.** 29 words, house form, locked-off camera clause, names only the wing. "Flapping and billowing" is oscillatory — no travel verb, so the no-travel rule holds.

**Against the reject list:** no settings change proposed; mover is bounded; no clip exists so no zero-return reasoning is in play; it accepts nothing and writes nothing into committed art or hotspots; the prompt is rendered from the spec, not hand-written; and it proposes RENDER, not AUTHOR_MOVER on an unrendered mover.

One thing for the *next* cycle, not this one: the real risk here is the video model translating the whole derelict glider rather than just flapping its wing. That is precisely what the first clip is for — pinning it pre-emptively is the documented cause of camera drift, so it correctly stays out of this cycle.

VERDICT: PASS