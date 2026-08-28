// Deduction ledger (#9) — the CONFIRMATION RULE, extracted so it can be tested without a browser.
//
// The ledger never confirms a single row. It confirms a whole GROUP, and only when the set of rows
// currently assigned to that group EXACTLY equals its true membership: every real member present AND
// nothing else claiming to be one. That is what stops the player fishing cell by cell for a green tick,
// and it is why the mechanic teaches clustering — a cluster is "right" when its members belong together,
// not one at a time.
//
// Groups are DERIVED from the rows' own answers, so there is no separate group config to drift out of
// sync with the data. Rows left unassigned simply never satisfy anything.

/** Map of verdict -> Set(rowId), derived from each row's `answer`. */
export function trueGroups(rows) {
  const t = new Map();
  for (const r of rows || []) {
    if (!t.has(r.answer)) t.set(r.answer, new Set());
    t.get(r.answer).add(r.id);
  }
  return t;
}

/** Map of verdict -> Set(rowId), derived from what the player currently has selected.
 *  `assignment` is a plain object or Map of rowId -> verdict; falsy verdicts mean "unassigned". */
export function assignedGroups(assignment) {
  const get = (assignment instanceof Map)
    ? Array.from(assignment.entries())
    : Object.entries(assignment || {});
  const a = new Map();
  for (const [rowId, verdict] of get) {
    if (!verdict) continue;
    if (!a.has(verdict)) a.set(verdict, new Set());
    a.get(verdict).add(rowId);
  }
  return a;
}

/**
 * Evaluate one press of "Check".
 * @param rows       [{id, label, answer}]
 * @param assignment rowId -> verdict (object or Map)
 * @param locked     Set of verdicts already confirmed on an earlier press (optional)
 * @returns {{locked:Set, newly:string[], groupCount:number, complete:boolean}}
 *          `locked` is a NEW Set — the caller decides whether to adopt it.
 */
export function confirmGroups(rows, assignment, locked) {
  const truth = trueGroups(rows);
  const mine = assignedGroups(assignment);
  const out = new Set(locked || []);
  const newly = [];
  for (const [verdict, members] of truth) {
    if (out.has(verdict)) continue;                 // already confirmed; never re-reported
    const got = mine.get(verdict) || new Set();
    const exact = got.size === members.size && Array.from(members).every(id => got.has(id));
    if (exact) { out.add(verdict); newly.push(verdict); }
  }
  return { locked: out, newly, groupCount: truth.size, complete: out.size === truth.size };
}
