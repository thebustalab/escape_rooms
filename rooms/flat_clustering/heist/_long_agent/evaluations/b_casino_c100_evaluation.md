I checked the worker's claims rather than taking them on trust. Everything material holds.

**Independent measurement** (my own per-pixel temporal std, 1536×512, same method, both clips):

| | ri84 (held) | ri98 (this clip) |
|---|---|---|
| peak col-std | 7.67 at **x=0.076** | 3.56 at **x=0.498** |
| contrast over median | 3.83× | 2.61× |
| half-max band width | **0.076** | **0.863** |
| max pixel-std | 68.8 | 25.2 |

The heatmaps settle it visually. ri84 shows one bright plume rising from the ashtray at far left and nothing else — a textbook bounded mover. ri98 has the energy smeared across the whole frame: chandelier crystals, chip stacks on every table, carpet edging, the cage grille all shimmering, with the peak sitting dead centre on the cashier's cage, where the spec declares nothing moves. The ashtray carries no more energy than the ambient twinkle. That is a global high-frequency flicker, not a mover.

**Against each rejection criterion:**

- **Settings** — not proposed. I diffed the two `params.json`: seed 4242, end_guide 0.70, steps 8, cfg 2.0, 73 frames, identical in both. The change is spec text only.
- **Zero return as proof** — not the basis. The worker explicitly set the 0.00 return aside as the documented ambiguous case and argued from spatial evidence, which I reproduced.
- **Frame-filling mover** — the opposite. The proposal confines the smoke to "one narrow column of air directly above the ashtray" with explicit exclusions on room haze. It is essentially re-specifying the geometry that worked in ri84.
- **Mover never rendered** — it has been. Still committed 14:26, ri98 rendered 14:53, and ri84 rendered the same element on the prior art.
- **Accepting a clip / writing committed art or hotspots** — no; it authors the sceneSpec element only.
- **Hand-written art prompt** — no; it emits the spec element and lets both consumers resolve.

I also confirmed the diff claim myself: between `scenario.json` and `scenario.json.bak_20260914_140023_casino_seam`, the **only** sceneSpec field that changed is `seam`, and the `smoke` element compares byte-identical. So the mover's authoring is exonerated and the redraw is the cause. The proposed element parses, keeps the exact key shape, and its 23-word phrase is in range.

Two things worth carrying forward, neither of them grounds to reject: the desc grows 11 → 74 words, which is heavy for a single element, and the worker's own note about `atmosphere` still reading "dense smoke" is a genuine co-cause that a single-element decision cannot reach. If the next draw still hazes the mid-ground, that field is the next lever.

VERDICT: PASS