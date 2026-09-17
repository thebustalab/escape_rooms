I checked the clip myself rather than relying on the worker's summary.

**Frames (ri14, 73 frames, 3072×1024, still camera):** frames 0, 36 and 72 are compositionally identical — no pan, no crawl, no structural collapse. The station reads correctly against the spec: one road, one tunnel mouth at the left, buffer stops and red lamp at the right, the green unit sitting level with the platform edge.

**The mover is genuinely alive.** A 9-sample montage of the seep region (crop 560×340 at x=2150, y=560) shows the sheet of water falling off the ledge into the channel changing shape frame to frame across the whole clip — it is running, not frozen. The dead reading is a false alarm, as the gate note warned it might be.

**On the zero return:** measured mean |fᵢ − f₀| climbs 0 → 1.91 → 2.44 → 2.78 and never comes back, with consecutive-frame diff averaging only 0.31. That is the signature the return metric cannot disambiguate — a slow global settle plus a flowing mover that never re-enters its starting configuration. The worker read it correctly and did not treat it as proof of death.

One thing the worker didn't note, and worth flagging for whoever looks: the seep box carries only 8.1% of total motion energy against a 6.1% area share, so most of the frame-to-frame change is diffuse rather than concentrated in the authored mover. That's a reason for a human to look carefully at the loop, not a reason to re-author — the mover is bounded, rendered and moving.

Against the reject list: no settings change, no frame-filling mover, no zero-return-means-dead inference, no acceptance and no write to scenario.json, no hand-written prompt, no AUTHOR_MOVER on an unrendered mover. Every reject-only gate passed and nothing is left to author or soften, so parking it for Lucas's eye is the correct terminal action for this cycle.

VERDICT: PASS