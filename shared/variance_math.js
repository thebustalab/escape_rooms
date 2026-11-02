// The arithmetic behind the variance meter (shared/variance_meter.js, kind "variance_meter", anova/cellars).
// Pure, no DOM, so node can test it against R's aov().
//
// One-way ANOVA sums of squares for a two-or-more-group split of a handful of readings:
//   between = sum over groups of n_g * (mean_g - grand)^2
//   within  = sum over readings of (x - mean_of_its_group)^2
//   share   = between / (between + within)   (eta squared; equals rstatix `ges` for a one-factor design)
// A group with no members contributes nothing. With every reading in one group, between is 0.

export function measure(values, groups) {
  const n = values.length;
  if (!n || groups.length !== n) throw new Error("measure: values and groups must be the same non-zero length");
  const grand = values.reduce((a, b) => a + b, 0) / n;
  const sum = new Map(), count = new Map();
  groups.forEach((g, i) => { sum.set(g, (sum.get(g) || 0) + values[i]); count.set(g, (count.get(g) || 0) + 1); });
  const mean = new Map([...sum].map(([g, s]) => [g, s / count.get(g)]));
  let within = 0;
  const dev = values.map((v, i) => { const d = v - mean.get(groups[i]); within += d * d; return d; });
  let between = 0;
  mean.forEach((m, g) => { between += count.get(g) * (m - grand) * (m - grand); });
  const total = between + within;
  return { grand, mean, count, dev, between, within, total, share: total > 0 ? between / total : 0 };
}

// Every distinct two-group split of n items, as boolean arrays with item 0 always false (a grouping and its
// mirror are the same split). 2^(n-1) - 1 of them: 127 for eight rooms.
export function allSplits(n) {
  const out = [];
  for (let m = 1; m < (1 << (n - 1)); m++) out.push(Array.from({ length: n }, (_, i) => i > 0 && !!(m & (1 << (i - 1)))));
  return out;
}

// The same split regardless of which side is called "left": normalise so item 0 is false.
export function canonical(split) { return split[0] ? split.map(b => !b) : split.slice(); }
