I read the four evidence files, then checked whether kiln's zero return was the dead reading or the cyclic-flow reading, since that measure has been wrong three times.

**The clip is dead.** Measured on the raw render `kiln_motion_ri75.mp4` (which does derive from today's still — frame 0 matches `scene.png`):

- Native-resolution temporal std in the juniper plume box: **5.11**, against bare-rock controls at **6.02** and **5.22**, and a frame-wide mean of **5.13**. The authored mover is *less* active than stone that cannot move.
- The smoke mask holds 0.90+ IoU with frame 0 all the way to frame 72, area varies 2.6%, centroid travels 1.8 px.
- A 7-frame contact sheet of the plume at native scale shows the same filaments in the same places in every frame; the amplified diff map is uniform speckle over the rock with the plume region *darker* than its surroundings.
- Calibration against `spindle`, held earlier in this same run: its cloth tile reads 41.0 against a 5.4 frame mean, ratio 7.6. kiln's best tile ratio is 1.65 and sits on rock, not on the mover.

So this is not the b_casino/logwood cyclic case — it is a frozen frame, and per step 6.3 a dead room goes back to the art rather than to any setting.

The still does depict the smudge dish, but it renders the authored "thick slow rope" as a thin translucent veil of pale grey wisps spread over a tall area of high-frequency red rock — very low contrast, and diffuse in the way `hood`'s cloud sea was, rather than bounded and legible. Cloth is the substrate this pipeline has actually woken rooms with (dust sheet, tarpaulin, spindle's signal cloth), gpt-image-2.5 follows depicted vigour on it, and the setting already calls this "the flagged platform" while carrying no flag — so the mover is native to the room, not an invention. The wind it needs is already established by the banner cloud streaming off the crest and the wind-scoured chimney mouth, and the platform's own flagstaff does not violate the "only signal post in the view" negative, which scopes to the far ridges.

Authoring it at full vigour deliberately: intensity language works downward only, so a too-lively result is a cheap phrase softening, whereas a too-quiet one costs another panorama.

```
DECISION: AUTHOR_MOVER
SPEC: {"id": "signal_flag", "at": "to the left", "desc": "a tall weathered timber signal staff planted in a cairn of red stones on the flags at the platform edge close beside the viewer, carrying one large plain unmarked flag of heavy bleached-white and slate-grey signal bunting that flies out clear of the dome's flank against the open cobalt sky", "motion": {"moves": true, "vigour": "cracking out rigid and dead horizontal in the hard wind coming over the dome, its trailing edge whipped and frayed and the halyard bowed tight against the staff", "phrase": "the big white and slate signal flag snapping and rippling hard on its staff"}}
WHY: The clip is dead, not cyclic — the juniper plume's temporal activity (5.11) is below that of bare rock (6.02) and its shape is identical across all 73 frames — because the still renders the authored thick rope as a faint diffuse veil, so the room needs a high-contrast bounded cloth mover, which the "flagged platform" setting already implies and the established wind already justifies.
```