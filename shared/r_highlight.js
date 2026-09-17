/*
 * r_highlight.js — a small R tokenizer, and the syntax highlighting built on it.
 *
 * Editing this file? Read integrated_bioanalytics/_agent_reference/webr_surfaces.md first — the design decisions, the failure histories and the anti-"improvement" guards live there.
 *
 * WHY WE HAVE OUR OWN. The book colours its code with **downlit**, which runs inside R at render time
 * (it even links function names to their docs). It cannot run in a browser, so the sandbox — where the
 * code is typed, not rendered — needs its own tokenizer.
 *
 * It emits **downlit's class names** (`fu`/`va`/`st`/`op`/`co`/`fl`/`cn`/`cf`) rather than inventing its
 * own, so the sandbox and the book describe the same things the same way. The *colours* differ and must:
 * downlit's palette is built for a white page (`va` is navy `#19177c`), and the sandbox editor is dark.
 * `sandbox.html` maps these classes to lifted versions of the same hues — functions blue, strings green,
 * numbers pink, comments grey — so the two read as the same scheme without being illegible.
 *
 * PURE ON PURPOSE — no DOM, no CDN import, no WebR. That is what makes it testable in Node without a
 * browser or a ~40 s WebR boot (`tests/r_highlight.test.mjs`), the pattern this book's AGENTS.md already
 * calls out for `webr_view.js`. Keep it that way: the DOM half lives in `sandbox.html`.
 *
 * The token stream is deliberately CONTIGUOUS and carries offsets — every character of the input belongs
 * to exactly one token, including whitespace. Two things depend on that: `highlightHTML()` can simply
 * concatenate, and a future bracket/quote checker can walk the same stream and know which `(` are real
 * code and which are inside a string or a comment (the whole reason a naive bracket count is wrong).
 */

// Control flow and function definition. `in` belongs here: it only ever appears in `for (x in y)`.
const CF = new Set(["if", "else", "for", "while", "repeat", "function", "return", "break", "next", "in"]);

// Reserved constants. `T`/`F` are included because R accepts them as TRUE/FALSE — colouring them as
// constants is honest about what they are, which is also a nudge that they are not ordinary variables.
const CN = new Set([
  "TRUE", "FALSE", "T", "F", "NULL", "NA", "Inf", "NaN",
  "NA_integer_", "NA_real_", "NA_character_", "NA_complex_",
]);

const isDigit = c => c >= "0" && c <= "9";
const isIdStart = c => /[A-Za-z._]/.test(c);
const isIdChar = c => /[A-Za-z0-9._]/.test(c);

/*
 * Tokenize R source. Returns [{type, value, start, end}], contiguous and in order.
 *
 * type: co comment · st string · cn constant · cf control-flow · fu function call · va name
 *       fl number · op operator/punctuation · ws whitespace
 *
 * Unterminated strings are not an error here — the student is mid-typing most of the time, and a
 * tokenizer that throws would blank the highlight on every other keystroke. The token is returned with
 * `unterminated: true` instead, so a checker can report it and the colouring stays stable meanwhile.
 */
export function tokenizeR(src) {
  const out = [];
  const n = src.length;
  let i = 0;
  const push = (type, start, extra) => {
    const t = { type, value: src.slice(start, i), start, end: i };
    if (extra) Object.assign(t, extra);
    out.push(t);
  };

  while (i < n) {
    const c = src[i];
    const start = i;

    // whitespace
    if (c === " " || c === "\t" || c === "\n" || c === "\r") {
      while (i < n && /\s/.test(src[i])) i++;
      push("ws", start);
      continue;
    }

    // comment to end of line
    if (c === "#") {
      while (i < n && src[i] !== "\n") i++;
      push("co", start);
      continue;
    }

    // string, single or double quoted, with backslash escapes
    if (c === '"' || c === "'") {
      i++;
      let closed = false;
      while (i < n) {
        if (src[i] === "\\") { i += 2; continue; }
        if (src[i] === c) { i++; closed = true; break; }
        i++;
      }
      push("st", start, closed ? null : { unterminated: true, quote: c });
      continue;
    }

    // backtick-quoted name — `my column`
    if (c === "`") {
      i++;
      let closed = false;
      while (i < n) {
        if (src[i] === "`") { i++; closed = true; break; }
        i++;
      }
      push("va", start, closed ? null : { unterminated: true, quote: "`" });
      continue;
    }

    // number — 1, 1.5, .5, 1e-3, 0x1f, 10L, 2i
    if (isDigit(c) || (c === "." && isDigit(src[i + 1]))) {
      if (c === "0" && (src[i + 1] === "x" || src[i + 1] === "X")) {
        i += 2;
        while (i < n && /[0-9a-fA-F]/.test(src[i])) i++;
      } else {
        while (i < n && isDigit(src[i])) i++;
        if (src[i] === ".") { i++; while (i < n && isDigit(src[i])) i++; }
        if (src[i] === "e" || src[i] === "E") {
          const save = i;
          i++;
          if (src[i] === "+" || src[i] === "-") i++;
          if (isDigit(src[i])) { while (i < n && isDigit(src[i])) i++; } else { i = save; }
        }
      }
      if (src[i] === "L" || src[i] === "i") i++;
      push("fl", start);
      continue;
    }

    // %in%, %>%, %%, %/% — a special operator runs to its closing %
    //
    // A missing closing % is FLAGGED rather than silently absorbed. `algae_data %> filter(x > 1)` — the
    // pipe typed with one % — otherwise tokenizes as a single operator swallowing the whole rest of the
    // line, which has two bad effects downstream: the hint reads "your code ends with
    // `%> filter(x > 1)`", which is gibberish to a student, and every bracket inside the swallowed text
    // becomes invisible to the bracket checker. The token TYPE is unchanged, so the colouring is the
    // same as before; only the flag is new. (`unterminatedOp` rather than the strings' `unterminated`
    // +`quote` pair, so structuralProblems can word the two cases differently.)
    if (c === "%") {
      i++;
      while (i < n && src[i] !== "%" && src[i] !== "\n") i++;
      const closedPct = src[i] === "%";
      if (closedPct) i++;
      push("op", start, closedPct ? null : { unterminatedOp: true });
      continue;
    }

    // identifier / keyword / constant / function call
    if (isIdStart(c)) {
      while (i < n && isIdChar(src[i])) i++;
      const word = src.slice(start, i);
      // A call is an identifier followed by `(`, whitespace allowed between — same rule downlit uses.
      let j = i;
      while (j < n && /\s/.test(src[j])) j++;
      let type;
      if (CF.has(word)) type = "cf";
      else if (CN.has(word)) type = "cn";
      else if (src[j] === "(") type = "fu";
      else type = "va";
      push(type, start);
      continue;
    }

    // multi-character operators, longest first
    const three = src.substr(i, 3);
    const two = src.substr(i, 2);
    if (three === "<<-" || three === "->>" || three === ":::") i += 3;
    else if (["<-", "->", "<=", ">=", "==", "!=", "&&", "||", "::", "|>"].includes(two)) i += 2;
    else i += 1;
    push("op", start);
  }

  return out;
}

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };
export const escapeHTML = s => s.replace(/[&<>]/g, ch => ESC[ch]);

/*
 * Render source as HTML with one <span class="…"> per coloured token.
 *
 * Whitespace is emitted bare rather than wrapped — fewer nodes, and nothing to colour. The caller is
 * responsible for putting this inside a `white-space: pre-wrap` element.
 */
export function highlightHTML(src) {
  let html = "";
  for (const t of tokenizeR(src)) {
    const text = escapeHTML(t.value);
    html += t.type === "ws" ? text : `<span class="${t.type}">${text}</span>`;
  }
  return html;
}
