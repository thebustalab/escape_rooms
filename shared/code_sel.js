/*
 * code_sel.js — "run the highlighted bit, or all of it" for a code textarea.
 *
 * RStudio behaviour, adapted: if the student has highlighted part of their code, run only that; if not,
 * run the whole editor. (RStudio's actual no-selection behaviour is "run the current line and advance";
 * we deliberately run EVERYTHING instead — in a teaching sandbox the whole-editor fallback is what a
 * student expects from a "Run" button, and there is no cursor-advance to make line-stepping useful.)
 *
 * Pure, so it can be unit-tested in Node — the console that consumes it cannot be (it imports the WebR
 * runtime from a CDN URL). See tests/code_sel.test.mjs.
 */

/*
 * Decide what to execute.
 *   value            the textarea's full contents
 *   selStart/selEnd  textarea.selectionStart / .selectionEnd
 * Returns { code, isSelection, lines, totalLines }.
 *
 * A WHITESPACE-ONLY selection counts as no selection. Without that, dragging across a blank line — easy
 * to do by accident, and invisible once the textarea loses focus — runs an empty string and the console
 * just says "(no output)", which reads as the Run button being broken.
 */
export function codeToRun(value, selStart, selEnd) {
  const all = value == null ? "" : String(value);
  const totalLines = countLines(all);
  const s = Number(selStart), e = Number(selEnd);
  const hasRange = Number.isFinite(s) && Number.isFinite(e) && e > s;
  const picked = hasRange ? all.slice(s, e) : "";
  if (!picked.trim()) return { code: all, isSelection: false, lines: totalLines, totalLines };
  return { code: picked, isSelection: true, lines: countLines(picked), totalLines };
}

// Lines actually occupied by a chunk of code, ignoring a trailing newline (selecting a whole line by
// dragging to the start of the next one is 1 line, not 2) and treating "" as 0.
export function countLines(text) {
  const t = text == null ? "" : String(text);
  if (!t.length) return 0;
  return t.replace(/\n$/, "").split("\n").length;
}

// The muted line shown above the output so a student can tell that only part of their code ran —
// our console does not echo the code the way RStudio's does, so without this a forgotten selection
// looks like the console silently ignoring most of the editor.
export function selectionNote(r) {
  if (!r || !r.isSelection) return null;
  const n = r.lines, total = r.totalLines;
  return `▸ ran the highlighted selection (${n} of ${total} ${total === 1 ? "line" : "lines"})`;
}
