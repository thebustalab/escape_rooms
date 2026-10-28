/*
 * live_solo.js — a ONE-PLAYER, SERVERLESS copy of the live-class session (bathhouse, Lucas 2026-10-27).
 *
 * A live scenario that carries `scenario.solo` (only basic_math/bathhouse) can be played on its own from the
 * public site: no class server, no join code. The player picks the duration, the herb-bundle goal and how many
 * small baths to fill, and this module answers the same calls live_session.js makes of the server
 * (state, deal, answer, deliver, backpack, skip), with the same shapes and the same rules:
 * tiers and tracks, carry caps per item (raised by a backpack), the overflow refusal, second items and sinks,
 * the two-part win, the wrong-answer cooldown, the clock, and the sewing table's stitch / ribbon checks.
 * It MIRRORS authoring_v2/live_class/live_server.py; tests/live_solo.test.mjs pins the shared rules, so a change
 * to one side should be made to both.
 *
 * The solo pool is a published file (rooms/<scenario>/solo/pool.json, written by the pool builder) and so carries
 * its answers in the clear: fine for an ungraded one-player practice game. The class server refuses to serve it.
 */

export const WRONG_COOLDOWN_S = 8;      // live_server.WRONG_COOLDOWN_S
const MAX_SEW_LEN = 64;

const plural = (n, unit) => `${n} ${n === 1 ? unit[0] : unit[1]}`;
const trackOf = p => p.track || "";
const itemOf = p => p.item || "";
const pointsOf = p => parseInt(p.points || p.tier, 10);
const randId = () => Math.random().toString(36).slice(2, 12);

export function stitchKey(counts, total) {
  return counts.filter(c => c).join(",") + "|" + total;
}
export function parseStitch(choice, grid) {
  if (choice.length > MAX_SEW_LEN) return null;
  const i = choice.indexOf("|");
  if (i < 0) return null;
  const rows = choice.slice(0, i), total = choice.slice(i + 1);
  if (!/^[0-9]{1,3}$/.test(total)) return null;
  const counts = rows ? rows.split(",") : [];
  if (counts.some(c => !/^-?[0-9]+$/.test(c.trim()))) return null;
  const n = counts.map(c => parseInt(c, 10));
  if (n.length > grid[0] || n.some(c => c < 0 || c > grid[1])) return null;
  return stitchKey(n, parseInt(total, 10));
}

export function poolPayouts(pool) {
  const rows = new Map();
  for (const p of pool.puzzles || []) {
    const k = JSON.stringify([p.tier, trackOf(p), itemOf(p)]), pts = pointsOf(p);
    const [lo, hi] = rows.get(k) || [pts, pts];
    rows.set(k, [Math.min(lo, pts), Math.max(hi, pts)]);
  }
  return [...rows.entries()].sort().map(([k, [lo, hi]]) => {
    const [tier, track, item] = JSON.parse(k);
    return { tier, track, item, min: lo, max: hi };
  });
}

// The restaurant (bathhouse, 2026-10-28): the menu entry whose track this is, else null (live_server.menu_dish).
export function menuDish(pool, track) {
  return ((pool.menu || {}).dishes || []).find(d => d.track === track) || null;
}
// The train tickets: are stops a and b joined by the ridden links, directly or through a chain (live_server.linked)?
export function linked(links, a, b) {
  const seen = new Set([a]), todo = [a];
  while (todo.length) {
    const x = todo.pop();
    for (const [p, q] of links) for (const [u, v] of [[p, q], [q, p]])
      if (u === x && !seen.has(v)) { seen.add(v); todo.push(v); }
  }
  return seen.has(b);
}

function publicPuzzle(p, dealId, order) {
  const out = { deal_id: dealId, tier: p.tier, kind: p.kind || "mcq", title: p.title, flavour: p.flavour || "",
                question: p.question, image: p.image || null, starter_code: p.starter_code || null, hint: p.hint || null };
  if (out.kind === "stitch") Object.assign(out, { rows: p.rows, per_row: p.per_row, grid: [...p.grid] });
  else if (out.kind === "ribbon") Object.assign(out, { length: p.length, cut: p.cut, tape: p.tape });
  else {
    const opts = Object.fromEntries(p.options.map(o => [o.id, o]));
    out.options = order.map(id => ({ id, text: opts[id].text }));
  }
  return out;
}

/*
 * new SoloSession(pool, {minutes, goal, baths}, now?) — `now` (ms) is injectable for the tests.
 * handle(path, body) -> {ok, status, j}, the shape live_session.js's api() returns from fetch.
 */
export class SoloSession {
  constructor(pool, { minutes, goal, baths }, now = () => Date.now()) {
    this.pool = pool;
    this.now = now;
    this.byId = Object.fromEntries(pool.puzzles.map(p => [p.id, p]));
    this.durationS = Math.round(minutes * 60);
    this.goal = goal;
    const sinks = pool.sinks || [];
    this.winSinks = Math.max(0, Math.min(sinks.length, baths | 0));
    this.startedAt = now();
    this.endedAt = null;
    this.phase = "running";
    this.total = 0;
    this.filled = [];
    this.served = [];                 // restaurant dishes sold out (live_server Session.served)
    this.feed = [];
    this.tierCounts = { 1: 0, 2: 0, 3: 0 };
    this.deal = null;                 // {id, puzzleId, order}
    this.pl = { callsign: "You", points: 0, solved: new Set(), cooldownUntil: 0, carrying: 0, held: {}, backpack: false, links: [] };
  }

  // ---- the clock and the win (Session.tick / maybe_win) ----
  elapsed() { return ((this.endedAt != null ? this.endedAt : this.now()) - this.startedAt) / 1000; }
  remaining() { return Math.max(0, this.durationS - this.elapsed()); }
  tick() {
    if (this.phase === "running" && this.remaining() <= 0) {
      this.phase = "timeup"; this.endedAt = this.startedAt + this.durationS * 1000;
    }
  }
  sinksNeeded() { return Math.max(0, this.winSinks - this.filled.length); }
  maybeWin() {
    if (this.total >= this.goal && !this.sinksNeeded() && this.phase === "running") {
      this.phase = "won"; this.endedAt = this.now();
    }
  }

  // ---- carry caps (item_cfg / player_cap / carry_full) ----
  itemCfg(item) {
    const P = this.pool;
    if (!item) return { unit: P.unit || ["load", "loads"], carry_max: P.carry_max, deliver_to: P.deliver_to || "the canoe",
                        carry_block_text: P.carry_block_text };
    return (P.items || {})[item] || {};
  }
  cap(item = "") {
    let cap = this.itemCfg(item).carry_max;
    const bp = this.pool.backpack || {};
    if (this.pl.backpack && bp.carry_max && item in bp.carry_max) cap = bp.carry_max[item];
    return cap;
  }
  blockText(item = "") {
    const bp = this.pool.backpack || {};
    if (this.pl.backpack && bp.carry_block_text && item in bp.carry_block_text) return bp.carry_block_text[item];
    return this.itemCfg(item).carry_block_text;
  }
  held(item = "") { return item ? (this.pl.held[item] || 0) : this.pl.carrying; }
  carryFull(item = "") {
    const cap = this.cap(item), n = this.held(item);
    return cap ? n >= cap : !!n;
  }
  tracks() { return [...new Set(this.pool.puzzles.map(trackOf))].filter(Boolean).sort(); }

  state() {
    this.tick();                       // the clock first, however the state is read
    const P = this.pool, pl = this.pl;
    return {
      phase: this.phase, remaining_s: Math.round(this.remaining()), duration_s: this.durationS,
      total: this.total, goal: this.goal, players: 1, feed: this.feed.slice(-8), tier_counts: { ...this.tierCounts },
      blackout: false, exp: null, filled: [...this.filled], served: [...this.served],
      me: { callsign: pl.callsign, points: pl.points, solved: pl.solved.size,
            cooldown_s: Math.max(0, Math.round((pl.cooldownUntil - this.now()) / 1000)),
            carrying: pl.carrying, held: { ...pl.held }, backpack: pl.backpack, links: pl.links.map(l => [...l]),
            caps: Object.fromEntries(["", ...Object.keys(P.items || {})].map(it => [it, this.cap(it)])), cast: false },
      goal_label: P.goal_label, unit: P.unit, carry_back: !!P.carry_back, carry_max: P.carry_max,
      deliver_to: P.deliver_to, deliver_verb: P.deliver_verb,
      items: Object.fromEntries(Object.entries(P.items || {}).map(([k, v]) =>
        [k, { unit: v.unit, carry_max: v.carry_max, deliver_to: v.deliver_to }])),
      sinks: (P.sinks || []).map(s => ({ id: s.id, label: s.label, item: s.item, cost: s.cost })),
      win_sinks: this.winSinks, payouts: poolPayouts(P), backpack: !!P.backpack, won_text: P.won_text || null,
      rides: P.rides || null,
      menu: P.menu ? { seconds: P.menu.seconds, dishes: P.menu.dishes.map(d => ({ track: d.track, label: d.label })) } : null,
      solo: true,
    };
  }

  handle(path, body) {
    const route = String(path).split("?")[0];
    const res = (j, status = 200) => ({ ok: status < 400, status, j });
    this.tick();
    if (route === "state") return res(this.state());
    if (route === "join") return res({ pid: "solo", callsign: this.pl.callsign });
    const P = this.pool, pl = this.pl;
    body = body || {};

    if (route === "deal") {
      if (this.phase !== "running") return res({ error: "The day is over." }, 409);
      const tier = parseInt(body.tier, 10);
      if (![1, 2, 3].includes(tier)) return res({ error: "bad tier" }, 400);
      const track = body.track || "";
      if (track && !this.tracks().includes(track)) return res({ error: "bad track" }, 400);
      const here = P.puzzles.filter(p => p.tier === tier && trackOf(p) === track);
      const dish = track ? menuDish(P, track) : null;          // the restaurant: pays time, never a carry
      if (dish && this.served.includes(track))
        return res({ error: `The kitchen has run out of ${dish.label.toLowerCase()}.`, served: [...this.served] }, 409);
      const carry = !!P.carry_back && !dish;
      const itemsHere = here.length ? [...new Set(here.map(itemOf))] : [""];
      if (carry && itemsHere.every(it => this.carryFull(it))) {
        const it = [...itemsHere].sort()[0];
        return res({ error: this.blockText(it) || "Deliver what you're carrying first.", carrying: this.held(it) }, 409);
      }
      this.deal = null;
      const choices = here.filter(p => !pl.solved.has(p.id) && !(carry && this.carryFull(itemOf(p))));
      if (!here.length) return res({ error: `This station has no level ${tier} tasks in this game.` }, 409);
      if (!choices.length) {
        const where = this.tracks().length ? " here — try another level or another station" : " — try another level";
        return res({ error: `You've cleared every level ${tier} task${where}.` }, 409);
      }
      const p = choices[Math.floor(Math.random() * choices.length)];
      const cfg = this.itemCfg(itemOf(p)), cap = this.cap(itemOf(p));
      if (cap && carry && this.held(itemOf(p)) + pointsOf(p) > cap) {
        const room = cap - this.held(itemOf(p)), unit = cfg.unit || ["load", "loads"];
        return res({ error: `This one is worth ${plural(pointsOf(p), unit)} and you only have room for ${room} more. ` +
                            `Take your ${unit[1]} to ${cfg.deliver_to || "the canoe"} first.`,
                     carrying: this.held(itemOf(p)) }, 409);
      }
      let order = null;
      if ((p.kind || "mcq") === "mcq") {
        order = p.options.map(o => o.id);
        if (!p.ordered) for (let i = order.length - 1; i > 0; i--) {
          const k = Math.floor(Math.random() * (i + 1)); [order[i], order[k]] = [order[k], order[i]];
        }
      }
      this.deal = { id: randId(), puzzleId: p.id, order };
      return res(publicPuzzle(p, this.deal.id, order));
    }

    if (route === "answer") {
      const d = this.deal;
      if (!d || d.id !== body.deal_id) return res({ error: "That task has expired — try the station again." }, 409);
      if (this.phase !== "running") return res({ error: "The day is over." }, 409);
      const now = this.now();
      if (now < pl.cooldownUntil)
        return res({ correct: false, cooldown_s: Math.round((pl.cooldownUntil - now) / 1000),
                     feedback: "Hold on — cooling down after the last try." });
      const p = this.byId[d.puzzleId], kind = p.kind || "mcq";
      let choice = String(body.choice == null ? "" : body.choice), right;
      if (kind === "stitch") {
        const key = parseStitch(choice.trim(), p.grid);
        if (key == null) return res({ error: "bad choice" }, 400);
        right = key === p.answer;
      } else if (kind === "ribbon") {
        choice = choice.trim();
        if (!/^[0-9]{1,3}$/.test(choice) || parseInt(choice, 10) > p.tape) return res({ error: "bad choice" }, 400);
        right = parseInt(choice, 10) === parseInt(p.answer, 10);
      } else {
        if (!d.order.includes(choice)) return res({ error: "bad choice" }, 400);
        right = choice === p.answer;
      }
      if (!right) {
        pl.cooldownUntil = now + WRONG_COOLDOWN_S * 1000;
        return res({ correct: false, cooldown_s: WRONG_COOLDOWN_S, feedback: p.wrong_feedback || "Not that one. Look again." });
      }
      const pts = pointsOf(p), it = itemOf(p);
      pl.solved.add(p.id);
      this.deal = null;
      this.tierCounts[p.tier] += 1;
      const dish = menuDish(P, trackOf(p));
      if (dish) {                       // the restaurant: a right answer buys time (Session.serve_dish)
        if (this.served.includes(dish.track))
          return res({ correct: true, points: 0, served_out: true, served: [...this.served],
                       feedback: `Right! But someone else just ate the last of the ${dish.label.toLowerCase()}, so no extra time this time.` });
        const secs = parseInt(P.menu.seconds, 10);
        this.durationS += secs;
        this.served.push(dish.track);
        return res({ correct: true, points: 0, time_added: secs, served: [...this.served],
                     remaining_s: Math.round(this.remaining()), feedback: p.right_feedback || "Delicious!" });
      }
      if (it) pl.held[it] = (pl.held[it] || 0) + pts; else pl.carrying += pts;
      return res({ correct: true, points: pts, carrying: this.held(it), carry_full: this.carryFull(it), total: this.total,
                   ...(it ? { item: it } : {}), feedback: p.right_feedback || null });
    }

    if (route === "deliver") {
      if (this.phase !== "running") return res({ error: "The day is over." }, 409);
      const sinkId = body.sink;
      if (sinkId) {
        const sink = (P.sinks || []).find(s => s.id === sinkId);
        if (!sink) return res({ error: "bad sink" }, 400);
        const unit = this.itemCfg(sink.item).unit;
        if (this.filled.includes(sinkId)) return res({ error: `${sink.label} is already full.`, filled: [...this.filled] }, 409);
        const have = this.held(sink.item);
        if (have < sink.cost)
          return res({ error: `${sink.label} needs ${plural(sink.cost, unit)} and you have ${have}. Solve more to earn ${unit[1]}.`,
                       carrying: have }, 409);
        pl.held[sink.item] -= sink.cost;
        pl.points += sink.cost;
        this.filled.push(sinkId);
        this.maybeWin();
        return res({ filled: sinkId, cost: sink.cost, carrying: this.held(sink.item), item: sink.item,
                     filled_all: [...this.filled], total: this.total, sinks_needed: this.sinksNeeded(), phase: this.phase });
      }
      const n = pl.carrying;
      if (!n) {
        const extra = Object.keys(pl.held).filter(k => pl.held[k]);
        if (extra.length) {
          const main = this.itemCfg(""), cfg = this.itemCfg(extra[0]);
          return res({ error: `${main.deliver_to[0].toUpperCase() + main.deliver_to.slice(1)} needs ${main.unit[1]}. ` +
                              `Your ${cfg.unit[1]} go in ${cfg.deliver_to}.`, delivered: 0 }, 409);
        }
        return res({ error: "You aren't carrying anything yet.", delivered: 0 }, 409);
      }
      pl.carrying = 0;
      this.total += n;
      pl.points += n;
      this.maybeWin();
      return res({ delivered: n, total: this.total, phase: this.phase });
    }

    if (route === "backpack") {
      if (!P.backpack) return res({ error: "not found" }, 404);
      pl.backpack = true;
      return res({ backpack: true, callsign: pl.callsign,
                   caps: Object.fromEntries(Object.keys(P.backpack.carry_max).map(it => [it, this.cap(it)])) });
    }
    if (route === "ride") {           // the lake train: a ticket links two stops for good (live_server /api/ride)
      const R = P.rides;
      if (!R) return res({ error: "not found" }, 404);
      const a = body.from, b = body.to, stops = R.stops;
      if (typeof a !== "string" || typeof b !== "string" || !(a in stops) || !(b in stops) || a === b)
        return res({ error: "bad stop" }, 400);
      const links = () => pl.links.map(l => [...l]);
      if (linked(pl.links, a, b)) return res({ ok: true, spent: 0, links: links() });
      if (this.held(R.item) < 1) {
        const unit = this.itemCfg(R.item).unit;
        return res({ error: `You need ${plural(1, unit)} to ride from ${stops[a]} to ${stops[b]}. ` +
                            "Solve a puzzle at a ticket window to earn one.", links: links() }, 409);
      }
      pl.held[R.item] -= 1;
      pl.links.push([a, b]);
      return res({ ok: true, spent: 1, item: R.item, carrying: this.held(R.item), links: links() });
    }
    if (route === "skip") { this.deal = null; return res({ ok: true }); }
    return res({ error: "not found" }, 404);
  }
}
