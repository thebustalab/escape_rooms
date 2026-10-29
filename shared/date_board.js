// DATE BOARD — a `lock` with `mode:"date"` (built 2026-10-28, first consumer regression/dunes' departure board).
//
// Two slide-levers, a day and a month, on a plain board. Nothing to type and no prompt: the player sets a date
// and pulls the board's handle. It opens when the date set is one of the `accept` list, so a puzzle with a short
// run of right days (dunes: 7, 8 or 9 December) needs no single magic code. Ungraded, never in the codec, and it
// reports { answer:1 } on a match exactly like the text lock.
//
// Schema: { type:"lock", mode:"date", accept:[[day, month], ...], year?, start?:[day, month],
//           submitLabel?, feedback?:{correct, wrong} }
//   accept  — the right dates as [day, month] pairs (month 1-12). The one record of the answer.
//   year    — only decides February's length (default: no leap day check, Feb has 29 slots).
//   start   — where the levers sit when the board first opens (default the first of January).
//
// DOM-free so tests/date_board.test.mjs can pin it; pano-player.js builds the card.

export const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                       "October", "November", "December"];

/** Days in a month. With no year February gets 29, so no date the author might want is unreachable. */
export function daysIn(month, year) {
  if (month === 2) {
    if (!Number.isInteger(year)) return 29;
    return (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)) ? 29 : 28;
  }
  return [4, 6, 9, 11].includes(month) ? 30 : 31;
}

/** Keep the day lever inside the chosen month (31 → 30 when the month lever moves to November). */
export function clampDay(day, month, year) {
  return Math.max(1, Math.min(Math.round(day), daysIn(month, year)));
}

/** Mis-authoring, listed. A date lock with problems fails CLOSED: it never opens. */
export function lockProblems(h) {
  const out = [];
  const acc = h && h.accept;
  if (!Array.isArray(acc) || !acc.length) { out.push("accept must be a non-empty list of [day, month]"); return out; }
  acc.forEach((p, i) => {
    if (!Array.isArray(p) || p.length !== 2 || !p.every(Number.isInteger)) { out.push(`accept[${i}] is not [day, month]`); return; }
    const [d, m] = p;
    if (m < 1 || m > 12) out.push(`accept[${i}] month ${m} is out of range`);
    else if (d < 1 || d > daysIn(m, h.year)) out.push(`accept[${i}] day ${d} does not exist in ${MONTHS[m - 1]}`);
  });
  return out;
}

/** Does the set date open the board? */
export function accepts(h, day, month) {
  if (lockProblems(h).length) return false;
  return h.accept.some(([d, m]) => d === day && m === month);
}

/** Where the levers start: `start` if valid, else 1 January. */
export function startDate(h) {
  const s = h && h.start;
  if (Array.isArray(s) && s.length === 2 && s.every(Number.isInteger) && s[1] >= 1 && s[1] <= 12)
    return { day: clampDay(s[0], s[1], h.year), month: s[1] };
  return { day: 1, month: 1 };
}

export function dateLabel(day, month) {
  return `${day} ${MONTHS[month - 1]}`;
}
