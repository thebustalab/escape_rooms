// The grid gate's answer check, pure so it can be tested (tests/grid_check.test.mjs).
// Default: every item in exactly the keyed bucket. With `partition` (h.partition:true) the buckets are
// unlabelled groups, so only WHICH ITEMS SHARE A BUCKET matters: a grouping and its mirror (or any
// relabelling of the buckets) are the same answer. Built for anova/cellars' passage door, where the player
// finds a two-group split on the variance meter and either orientation of it is correct.
export function gridMatches(items, sel, answer, partition = false) {
  const keys = items.map(it => it.key);
  if (!partition) return keys.every(k => sel[k] === answer[k]);
  // Same partition iff the bucket relation agrees on every pair of items.
  for (let i = 0; i < keys.length; i++)
    for (let j = i + 1; j < keys.length; j++)
      if ((sel[keys[i]] === sel[keys[j]]) !== (answer[keys[i]] === answer[keys[j]])) return false;
  return keys.every(k => sel[k] !== undefined);
}
