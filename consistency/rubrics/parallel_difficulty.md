# Rubric: parallel difficulty across a chapter's two scenarios

You are auditing a PAIR of escape-room scenarios that belong to the same book chapter. In the study
they are used as an encounter/review pair, so they MUST be parallel in difficulty. Read BOTH target
`scenario.json` files. Compare them room-by-room and overall.

## The invariant
- Same technique taught at each corresponding step (e.g. both teach filter->count, then filter->rank).
- Comparable number of analytic steps per room and overall.
- Comparable distractor subtlety in the MCQs (wrong options similarly tempting and data-derived).
- Comparable cognitive load (data shape, threshold reasoning, misdirection).
- Same room count and same boss structure.

## What to flag
- One scenario is clearly harder/easier (more steps, subtler distractors, an extra twist the other lacks).
- A technique present in one member's room but absent from the other's corresponding room.
- Different room counts, or a boss in one but not the other.

## OUTPUT CONTRACT (strict)
Return ONLY a JSON array, nothing else (no prose, no code fence). Each element:
{
  "check_id": "pair-parallel-difficulty",
  "severity": "warn",
  "targets": ["<relpath A>", "<relpath B>"],
  "locator": "<room key or 'overall'>",
  "message": "<the difficulty divergence>",
  "suggestion": "<how to re-balance>"
}
If the pair is well-matched, return exactly: []
If only one member is built (the other is a stub with no built rooms), return exactly: [] (cannot compare yet).
