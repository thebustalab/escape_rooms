## Independent verification

**The frames back the worker, not the gate report.** I pulled frames 0/18/36/72 from the raw render myself:

- **Frame 0** — the clean committed panorama: city on the left, eyewall and ring-current right, the derelict glider (the intended mover) a small dark winged shape at right, and the viewer's own two pale translucent foreground wings in the bottom-left and bottom-right corners.
- **Frame 18** — a gridded ochre sailcloth already spans the full 3072 px, rooted in exactly those two foreground wings.
- **Frame 36** — it has swallowed the right half: eyewall, ring-current and the derelict itself are gone behind it.
- **Frame 72** — clean again.

That arrival-and-departure is precisely why `return 0.69` reads healthy and `glitch.breadth 0.125` caught only the onset edge — the gates are blind to this by construction, not by accident. The camera genuinely is still, so "camera: one object moving" is also not wrong, just insufficient.

**The mechanics check out.** `scene_spec.py:458` takes `rigid` as an authored **string** on the spec (`spec["rigid"]`, line 481), and `state_spec` treats `rigid` as a first-class key (line 683). Running it with the proposed payload:

- motion prompt → **57 words** (vs 29 bare), well inside the safe register
- `render_prompt(spec)` → **byte-identical**, so no committed art is at risk
- spec on disk still has no `rigid`, confirming cycle 28 never landed

**Scope is right.** The intended mover is `derelict` — "the derelict glider's torn membrane wing flapping and billowing in the wind". The video model is applying that to the viewer's own frame-filling membrane wings, which share the description. Naming those wings alone is the scalpel; the dash and nose are static across all four frames, so adding them would be the inventory-creep that broke `a_opera`.

None of the reject conditions fire: no settings change, no new mover, no zero-return argument, no writes to committed art or hotspots, no hand-written art prompt.

VERDICT: PASS