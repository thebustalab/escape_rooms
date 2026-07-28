# Rubric: narrative voice + clue-style consistency

Audit ONE scenario for narrative-voice consistency. Read the target `scenario.json`. Inspect the
top-level `story`, each room's `entry` interstitial text, and each `clue` hotspot `body`.

## The invariant
- Second-person voice ("you"), present tense, immersive, matching the scenario's `story`.
- Clue bodies carry the SCIENCE (why it matters) and the DATA SHAPE (columns/format/counts) only.
  They must NOT contain code syntax (filter()/aes()/pipelines) and must NOT give away the answer
  (don't name the correct analyte/well/lake, or state the fact that lets a student skip the analysis).
- Entry screens recap the prior finding and set up the next task, without solving it.
- Consistent tone across rooms (no jarring register shifts).

## What to flag
- Voice/register drift (e.g. a clue slipping into third person or a lecture tone).
- A clue containing pipeline/code syntax, or revealing the answer.
- An entry screen that gives away its room's answer.

## OUTPUT CONTRACT (strict)
Return ONLY a JSON array, nothing else (no prose, no code fence). Each element:
{
  "check_id": "narrative-voice",
  "severity": "info",
  "targets": ["<relpath>"],
  "locator": "$.story  OR  $.rooms[<key>].entry  OR  $.rooms[<key>].hotspots[<id>].body",
  "message": "<the drift>",
  "suggestion": "<the fix>"
}
If consistent, return exactly: []
