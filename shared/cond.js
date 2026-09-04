// Gate conditions (`unlockedWhen` / `availableWhen` / variant `when`), extracted pure so they can be
// tested without a browser. The player's `condOK` is a thin wrapper that passes its own globals in.
//
// Grammar — each clause is one test, except the two composers:
//   true | false | undefined      always / never / always
//   {solved: roomKey}             that room's primary gate is solved
//   {allSolved: [roomKey, ...]}   all of them are
//   {gte: [stateKey, n]}          a counter has reached n
//   {eq:  [stateKey, value]}      state equality (dials, world-state variants)
//   {ne:  [stateKey, value]}      state inequality
//   {all: [cond, ...]}            every sub-condition holds
//   {any: [cond, ...]}            at least one does
//
// WHY `all`/`any` EXIST (2026-09-02). Every other clause is a single test, so a gate that genuinely
// depends on two things could not be expressed. The first real case was `networks/beacons`' escape,
// which opens only when the BOSS is solved AND all nine survey tiles are collected. Without composition
// the only encoding was to have both feed one counter and gate on `{gte:[k,10]}` — a magic number whose
// meaning is unrecoverable a month later. An unreadable gate is a bug waiting to be "simplified" wrongly.
//
// Unknown shapes return FALSE (fail closed): a gate nobody can evaluate should stay shut rather than
// silently opening the world.

/**
 * @param cond the condition
 * @param ctx  {solved: Set<string>, state: object}
 */
export function condHolds(cond, ctx) {
  const solved = (ctx && ctx.solved) || new Set();
  const state = (ctx && ctx.state) || {};
  if (cond === undefined || cond === true) return true;
  if (cond === false) return false;
  if (cond && typeof cond === "object") {
    if ("solved" in cond) return solved.has(cond.solved);
    if ("allSolved" in cond) return (cond.allSolved || []).every(k => solved.has(k));
    if ("gte" in cond) { const g = cond.gte || []; return (Number(state[g[0]]) || 0) >= Number(g[1]); }
    if ("eq" in cond) { const e = cond.eq || []; return String(state[e[0]]) === String(e[1]); }
    if ("ne" in cond) { const e = cond.ne || []; return String(state[e[0]]) !== String(e[1]); }
    if ("all" in cond) return (cond.all || []).every(c => condHolds(c, ctx));
    if ("any" in cond) return (cond.any || []).some(c => condHolds(c, ctx));
  }
  return false;
}
