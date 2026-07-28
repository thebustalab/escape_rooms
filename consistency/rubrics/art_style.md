# Rubric: art-style consistency

You are auditing ONE escape-room scenario for consistency with the shared house art style. Read the
target `scenario.json`. Inspect every room's `authoring.scenePrompt` and `authoring.doorPrompt` (these
text prompts are the source of truth for the generated scene art). Judge each against the house style
below and report ONLY genuine drift.

## House art style (the invariant)
- Time/mood: dusk or night, quiet, cinematic, atmospheric.
- Palette: deep teal + icy blue with ONE warm amber light source. No other dominant colours.
- Rendering: painterly but clean, film grain, richly detailed.
- STRICTLY: no people, no lettering, no text, no captions, no logos anywhere in the scene.
- 360 framing: "centre-and-around" — a view from the centre of the room wrapping continuously so the
  left and right edges meet seamlessly, objects placed with viewpoint-relative anchors (Ahead / To one
  side / Opposite / Set into one wall). NOT a flat left-to-right "four zones / far LEFT ... far RIGHT"
  banner (that seams when wrapped).
- Each scene contains a CLOSED door (the swap portal); a mid-series room also shows an OPEN passage back.

## What to flag (drift)
- Daytime / bright / non-atmospheric lighting; a palette that isn't teal-and-amber; several warm sources.
- Any people described in the prompt.
- **Legible** text: readable words, signage, a poster or sign with stated words, captions, labels,
  equations, UI text, or logos (e.g. `a poster reading "WELCOME"`, `a whiteboard of equations`).
- Flat left-to-right / "zones" framing instead of centre-and-around (seam risk).
- A missing closed door, or door state inconsistent with the room's position in the series.
- Style words clashing with "painterly, film grain" (e.g. "photorealistic 4k render", "cartoon").

## Not drift (do NOT flag)
- **Paper props with no specified readable content** — "notes", "field notes", "handwritten notes",
  "notebooks", "a chart", "a map", "a poster" with no stated words. The generator renders these as
  illegible, which is intended and fine. Only flag text when the prompt specifies content that would
  be *readable* (words, a legible sign, equations). (Lucas's call, 2026-07-18: open notes on a table
  are acceptable.)
- Stylistic variety that stays within the house style. Only report real, defensible drift.

## OUTPUT CONTRACT (strict)
Return ONLY a JSON array, nothing else (no prose, no code fence). Each element:
{
  "check_id": "art-style-consistency",
  "severity": "warn",
  "targets": ["<the scenario relpath you were given>"],
  "locator": "$.rooms[<key>].authoring.scenePrompt",
  "message": "<what drifts and why it breaks the house style>",
  "suggestion": "<the concrete prompt fix>"
}
If there is no drift, return exactly: []
