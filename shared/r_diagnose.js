/*
 * r_diagnose.js — turn R's error output into something a student can act on.
 *
 * Editing this file? Read integrated_bioanalytics/_agent_reference/webr_surfaces.md first — the design decisions, the failure histories and the anti-"improvement" guards live there.
 *
 * WHY THIS EXISTS. WebR hands back only the FIRST LINE of an R error. R itself produced more: for a
 * mistyped column name, R said "Problem while computing aesthetics." AND "Caused by error: object
 * 'watertemp' not found" — and webR drops the second half, which is the half naming the actual mistake.
 * The clean fixes (a global calling handler, rlang::global_entrace) are both refused by webR, because its
 * capture machinery already has handlers on the stack. So instead of recovering R's text we reconstruct
 * the MEANING from the headline, which survives intact and is a reliable signpost.
 *
 * Two independent halves:
 *   structuralProblems(src)  — parse-level faults found by walking our own token stream: unclosed
 *                              brackets, unterminated strings, a line left dangling on %>% or +. This
 *                              beats R's parse error, which reports where the parser GAVE UP rather than
 *                              where the mistake is: leave a `(` open on line 1 of a 20-line script and R
 *                              points at line 20. We can point at line 1.
 *   explainError(text, ctx)  — a plain-English gloss of a runtime error, plus the next thing to TYPE.
 *
 * The house style for a hint: say what R meant, then name a command that moves the student forward. Never
 * rewrite their code for them — pointing at `colnames(d)` teaches a habit, pasting the right column name
 * does not.
 *
 * SHARED (moved here 2026-09-17). This module used to live in the book repo and was wired into
 * sandbox.html alone, so the rooms — the HOMEWORK for the very chapters the sandbox demonstrates in
 * class — showed students a raw, misleading parse error while the sandbox explained it. It now sits
 * beside the console that produces those errors and is applied by `webr-console.js` itself, so all
 * three surfaces get hints at once and cannot drift apart again. Same reasoning as the 2026-09-04
 * console consolidation; see webr-cell.js's header.
 *
 * Because it is shared, the wording must not assume the sandbox. There is no Environment pane in a
 * room and the package set differs per scenario, so anything surface-specific comes in through `ctx`
 * ({source, objects, packages, envLabel}) and has a neutral fallback.
 *
 * PURE — no DOM, no WebR. Tested in Node (`tests/r_diagnose.test.mjs`).
 */
import { tokenizeR } from "./r_highlight.js?v=104";

const OPENERS = { "(": ")", "[": "]", "{": "}" };
const CLOSERS = { ")": "(", "]": "[", "}": "{" };

// 1-based line number of a character offset.
export function lineAt(src, offset) {
  let line = 1;
  for (let i = 0; i < offset && i < src.length; i++) if (src[i] === "\n") line++;
  return line;
}

/*
 * Structural faults, most-useful-first. Returns [] for code that is structurally fine — which includes
 * plenty of code that will still fail at runtime; this half only knows about shape.
 *
 * Only the FIRST bracket fault is reported. One missing bracket cascades into a pile of downstream
 * complaints, and a student handed five problems does not know which one is real.
 */
export function structuralProblems(src) {
  const problems = [];
  const tokens = tokenizeR(src);

  /*
   * THE FILL-IN-THE-BLANK PLACEHOLDER. Checked before anything else, because in this book it is the
   * single most common thing a student runs by accident — six of the seven cells in the wrangling
   * chapter ship with a `____` in them, and "I pressed Run before filling it in" is not an error about
   * R at all. Without this it is actively misleading: `____` is a LEGAL R identifier, so the student is
   * told to check their spelling or that no such function exists, as though they had typed something.
   *
   * It surfaces in three different ways depending on where the blank sits — `____(data)` is a missing
   * function, `names_to = ____` is a missing object, and a blank in operator position is a parse error —
   * so it is handled here AND in the two explainError matchers, not in one place.
   */
  const blank = src.match(/(?:^|[^\w.])(_{3,})(?![\w.])/);
  if (blank) {
    const ln = lineAt(src, blank.index + blank[0].indexOf("_"));
    problems.push({
      kind: "unfilled-blank",
      line: ln,
      message: `Line ${ln} still has the blank (${blank[1]}) in it — that is the part you are meant to ` +
               `replace. R treats it as an ordinary name, so it cannot tell you what was supposed to go ` +
               `there; work it out from the sentence above the cell.`,
    });
    return problems;
  }

  /*
   * CURLY QUOTES. Checked early, because when they are present they are essentially always the cause and
   * every other symptom is downstream noise. R only accepts the straight ' and ", so a quote autocorrected
   * by Word, Google Docs or a PDF copy is not a quote at all — R reads the text as a name, and its own
   * message (`unexpected input`) never mentions the character. Students paste from the book and from each
   * other constantly, so this arrives often and is invisible on screen at 13px.
   *
   * Scanned over the RAW SOURCE rather than the token stream on purpose: the whole problem is that the
   * tokenizer does not recognise these as quotes, so there is no token to look for.
   *
   * But it must SKIP strings and comments, where a curly quote is perfectly legal R and usually
   * deliberate — `labs(title = "Lucas’s lakes")` and `# don’t panic` are both fine, and this book's
   * captions are exactly the sort of prose that carries a typographic apostrophe. Flagging those would
   * send a student to "fix" working code, which is the failure this module exists to avoid.
   */
  const quoted = tokens.filter(t => t.type === "st" || t.type === "co" || (t.type === "va" && t.quote));
  const inQuoted = idx => quoted.some(t => idx >= t.start && idx < t.end);
  let curly = null;
  for (const m of src.matchAll(/[\u2018\u2019\u201C\u201D]/g)) {
    if (!inQuoted(m.index)) { curly = m; break; }
  }
  if (curly) {
    const ln = lineAt(src, curly.index);
    problems.push({
      kind: "curly-quote",
      line: ln,
      message: `Line ${ln} has a curly quote (${curly[0]}) where R needs a straight one. This usually comes ` +
               `from pasting out of a document or a PDF, which silently swaps them. Retype the quotes ` +
               `around that text by hand — R only accepts " and '.`,
    });
    return problems;
  }

  // An unterminated string swallows the rest of the file, so everything after it is noise — report it
  // alone and stop.
  const openString = tokens.find(t => t.unterminated);
  if (openString) {
    const q = openString.quote === "`" ? "backtick" : `${openString.quote} quote`;
    problems.push({
      kind: "unterminated-string",
      line: lineAt(src, openString.start),
      message: openString.quote === "`"
        ? `The backtick name starting on line ${lineAt(src, openString.start)} is never closed.`
        : `The text starting on line ${lineAt(src, openString.start)} is never closed — it needs a matching ${q}.`,
    });
    return problems;
  }

  /*
   * A `%...%` operator with no closing % — nearly always the pipe typed with one % (`%>`), or a stray %
   * left behind while editing. R's own message for it is `unexpected input`, which says nothing.
   *
   * Checked BEFORE the brackets, because an unterminated operator swallows the rest of its line into one
   * token: the brackets inside it are invisible to the loop below, so a bracket fault reported from here
   * would be reported against a half-seen line. Checked AFTER the string check, because a string
   * swallows more still (everything to the end of the source, not just the line).
   */
  const openOp = tokens.find(t => t.unterminatedOp);
  if (openOp) {
    const ln = lineAt(src, openOp.start);
    problems.push({
      kind: "unterminated-operator",
      line: ln,
      message: `The % operator on line ${ln} is never closed, so R reads the rest of that line as part of ` +
               `it. Operators of this kind need a % at BOTH ends — the pipe is %>%, and there is also ` +
               `%in%.`,
    });
    return problems;
  }

  const stack = [];
  for (const t of tokens) {
    if (t.type !== "op") continue;           // brackets inside strings/comments are not brackets
    const v = t.value;
    if (OPENERS[v]) { stack.push(t); continue; }
    if (!CLOSERS[v]) continue;
    const open = stack.pop();
    if (!open) {
      problems.push({
        kind: "unexpected-close",
        line: lineAt(src, t.start),
        message: `There is a ${v} on line ${lineAt(src, t.start)} with no matching ${CLOSERS[v]} before it.`,
      });
      return problems;
    }
    if (OPENERS[open.value] !== v) {
      problems.push({
        kind: "mismatched-bracket",
        line: lineAt(src, open.start),
        message: `The ${open.value} opened on line ${lineAt(src, open.start)} is closed by a ${v} on line ${lineAt(src, t.start)}.`,
      });
      return problems;
    }
  }
  if (stack.length) {
    const open = stack[0];
    /*
     * The commonest ggplot bracket slip gets named precisely: `ggplot(d, aes(x = a, y = b) +` — the
     * ) that should close ggplot( is missing, so the + and every layer after it end up INSIDE ggplot's
     * brackets. "The ( on line 5 is never closed" is true but sends the student to count brackets across
     * the whole plot; pointing at the + tells them where the ) belongs.
     */
    const at = tokens.indexOf(open);
    const before = tokens.slice(0, at).filter(t => t.type !== "ws" && t.type !== "co").pop();
    if (open.value === "(" && before && before.value === "ggplot") {
      let depth = 0, plus = null;
      for (const t of tokens.slice(at + 1)) {
        if (t.type !== "op") continue;
        if (OPENERS[t.value]) depth++;
        else if (CLOSERS[t.value]) depth--;
        else if (t.value === "+" && depth === 0) { plus = t; break; }
      }
      if (plus) {
        const lo = lineAt(src, open.start), lp = lineAt(src, plus.start);
        problems.push({
          kind: "unclosed-ggplot",
          line: lo,
          message: `The ( after ggplot on line ${lo} is never closed, so the + on line ${lp} has ended up ` +
                   `inside ggplot's brackets. Close ggplot( … ) with a ) just before that +.`,
        });
        return problems;
      }
    }
    problems.push({
      kind: "unclosed-bracket",
      line: lineAt(src, open.start),
      message: `The ${open.value} opened on line ${lineAt(src, open.start)} is never closed — it needs a ${OPENERS[open.value]}.`,
    });
    return problems;
  }

  /*
   * Everything from here down runs on code whose strings and brackets are SOUND, so any fault left is
   * about how the pieces are joined rather than about shape. Each check below answers a parse error that
   * R reports only as "unexpected symbol" / "unexpected ','" / "unexpected input" — true, and useless.
   *
   * `enclosing` is the innermost open bracket at each token, which is what makes these safe. A comma is
   * an error at the top level but correct inside `(`; two names side by side are an error inside `(` but
   * correct inside `{`, where they are simply two statements. Without the distinction each check would
   * fire on valid code, and a wrong hint is worse than no hint.
   */
  const code = tokens.filter(t => t.type !== "ws" && t.type !== "co");
  const enclosing = [];
  {
    const open = [];
    for (const t of code) {
      if (t.type === "op" && CLOSERS[t.value]) open.pop();
      enclosing.push(open.length ? open[open.length - 1].value : null);
      if (t.type === "op" && OPENERS[t.value]) open.push(t);
    }
  }
  const isValue = t => ["va", "fl", "st", "cn", "fu"].includes(t.type);

  /*
   * An operator at the START of a line, outside any brackets — `+ geom_point()` or `%>% filter(...)`
   * written under the previous line instead of at the end of it. The data-vis chapter teaches exactly
   * this ("just make sure the + sign is at the end of the top line"), which is a good sign of how often
   * it goes wrong. R parses the line above as a complete expression and then meets an operator with
   * nothing on its left.
   */
  for (let i = 1; i < code.length; i++) {
    const t = code[i];
    if (enclosing[i] !== null) continue;                     // inside brackets a leading operator is fine
    if (t.type !== "op" || OPENERS[t.value] || CLOSERS[t.value]) continue;
    const ln = lineAt(src, t.start);
    if (lineAt(src, code[i - 1].start) === ln) continue;     // not at the start of its line
    if (!/^[+\-*\/]$|^%.*%$/.test(t.value)) continue;          // only the joiners students actually misplace
    problems.push({
      kind: "leading-operator",
      line: ln,
      message: `Line ${ln} begins with ${t.value}, so R has already finished the line above it and has ` +
               `nothing to join on to. ${t.value} goes at the END of the previous line, not at the start ` +
               `of this one.`,
    });
    return problems;
  }

  /*
   * A comma outside every bracket. Always wrong in R, and the usual cause here is joining two ggplot
   * layers with a comma instead of a +, or ending a line with a comma that was meant to be inside the
   * call above it.
   */
  for (let i = 0; i < code.length; i++) {
    if (code[i].value !== "," || enclosing[i] !== null) continue;
    const ln = lineAt(src, code[i].start);
    problems.push({
      kind: "top-level-comma",
      line: ln,
      message: `The comma on line ${ln} is outside any brackets, where R does not expect one. Commas ` +
               `separate arguments INSIDE a function's brackets; plot layers are joined with +, and ` +
               `steps in a pipeline with %>%.`,
    });
    return problems;
  }

  /*
   * An operator with nothing after it before the bracket closes — `filter(pH ==)`, `facet_grid(lake~)`,
   * `summarize(m = )`. Common in this book because so many cells are fill-in-the-blank: deleting the
   * blank without replacing it leaves exactly this.
   */
  for (let i = 0; i < code.length - 1; i++) {
    const t = code[i], next = code[i + 1];
    if (t.type !== "op" || OPENERS[t.value] || CLOSERS[t.value] || t.value === ",") continue;
    if (!(next.type === "op" && CLOSERS[next.value])) continue;
    const ln = lineAt(src, t.start);
    problems.push({
      kind: "empty-operand",
      line: ln,
      message: `On line ${ln} there is a ${t.value} with nothing after it before the bracket closes. ` +
               `Whatever ${t.value} was going to work on is missing.`,
    });
    return problems;
  }

  /*
   * Two values side by side inside a call, with no comma or operator between them — `ggplot(algae_data
   * aes(x = a))`, `c(1 2)`. The commonest single slip in the nested `geom_point(aes(...), size = 5)`
   * shape this book teaches. Restricted to `(` and `[`: inside `{` two names in a row are just two
   * statements, which is perfectly legal.
   */
  for (let i = 0; i < code.length - 1; i++) {
    if (enclosing[i] !== "(" && enclosing[i] !== "[") continue;
    if (!isValue(code[i]) || !isValue(code[i + 1])) continue;
    const ln = lineAt(src, code[i + 1].start);
    problems.push({
      kind: "missing-separator",
      line: ln,
      message: `On line ${ln}, ${code[i].value} and ${code[i + 1].value} sit side by side with nothing ` +
               `between them. Arguments inside brackets need a comma between them.`,
    });
    return problems;
  }

  // Code that ends mid-expression. R's "unexpected end of input" is the same symptom as an unclosed
  // bracket, and students hit this constantly by leaving a trailing %>% or + on the last line.
  const meaningful = tokens.filter(t => t.type !== "ws" && t.type !== "co");
  const last = meaningful[meaningful.length - 1];
  if (last && last.type === "op" && !CLOSERS[last.value] && ![")", "]", "}"].includes(last.value)) {
    problems.push({
      kind: "dangling-operator",
      line: lineAt(src, last.start),
      message: `Your code ends with ${last.value} on line ${lineAt(src, last.start)}, so R is still waiting for what comes next.`,
    });
  }
  return problems;
}

// Edit distance, capped — only used to ask "did you mean this existing name?".
function distance(a, b) {
  if (Math.abs(a.length - b.length) > 3) return 99;
  const prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let carry = prev[0];
    prev[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const tmp = prev[j];
      prev[j] = Math.min(prev[j] + 1, prev[j - 1] + 1, carry + (a[i - 1] === b[j - 1] ? 0 : 1));
      carry = tmp;
    }
  }
  return prev[b.length];
}

/*
 * The closest known name, if one is close enough to be worth suggesting. Case-insensitive, because
 * `View`/`view` and `TRUE`/`True` are exactly the sort of slip this should catch.
 */
export function didYouMean(name, candidates) {
  let best = null, bestD = Infinity;
  for (const c of candidates || []) {
    const d = distance(name.toLowerCase(), c.toLowerCase());
    if (d < bestD) { bestD = d; best = c; }
  }
  // Allow 1 edit for short names, 2 for longer ones — enough for a typo, not enough to guess wildly.
  const limit = name.length <= 4 ? 1 : 2;
  return bestD <= limit ? best : null;
}

/*
 * The packages a surface actually loaded, as English. The sandbox has a fixed set; a room loads whatever
 * its scenario declares, so a hardcoded list would be a lie there. Falls back to the common core.
 */
/*
 * Is this R's PARSER complaining, rather than something that ran and failed?
 *
 * Deliberately broader than it first was. The original test enumerated four "unexpected X" phrasings and
 * silently missed R's long tail — `unexpected numeric constant` (mean(1 2)), `unexpected input`,
 * `unexpected SPECIAL` — so those fell through every matcher and the student got NO hint for a plain
 * syntax error, even though structuralProblems() had the answer. The two leading alternatives are the
 * reliable ones: webR always reports a parse failure through `parse(text = expr)`, and R always stamps
 * the position as `<text>:LINE:COL:`. Matching those is specific to the parser, not a guess.
 *
 * Breadth is safe HERE in a way it would not be for the runtime matchers below. Those name a cause, so a
 * wrong match misleads; this branch only ever says "R could not read this" or reports a structural fault
 * we found ourselves in the source — both of which hold for any parse error at all.
 */
const PARSE_ERROR = /parse\(text|<text>:\d+:\d+:|unexpected (end of input|symbol|string constant|numeric constant|input|SPECIAL|INCOMPLETE|'.*')/i;

/*
 * Names worth offering as "did you mean". Drawn from what the book's chapters actually teach —
 * `3_datavis_1`, `4_datavis_2` and `6_wrangling_summaries` — because a near-miss is only useful if the
 * right answer is in the list, and the original 19 names covered the dplyr verbs while missing every
 * geom, scale, theme and facet function those chapters spend most of their pages on.
 *
 * It is a FIXED list rather than R's loaded namespaces because webR cannot cheaply enumerate them, and
 * a surface can extend it through `ctx.functions`. Both spellings of summarise/summarize are here: the
 * wrangling chapter uses the z, dplyr accepts both, and a student who half-remembers one wants the
 * other suggested rather than a shrug.
 */
const KNOWN_FUNCTIONS = [
  // dplyr / tidyr
  "filter", "select", "mutate", "summarise", "summarize", "group_by", "arrange", "desc", "slice",
  "pull", "rename", "distinct", "count", "n", "pivot_longer", "pivot_wider",
  // base + stats a student meets here
  "mean", "median", "sd", "sum", "min", "max", "length", "nrow", "ncol", "colnames", "head", "str",
  "seq", "factor", "library", "view",
  // ggplot core, geoms, facets, scales, themes
  "ggplot", "aes", "labs", "ggtitle", "guides", "coord_flip",
  "geom_point", "geom_bar", "geom_col", "geom_line", "geom_boxplot", "geom_violin", "geom_smooth",
  "geom_tile", "geom_text", "geom_text_repel", "geom_jitter", "geom_pointrange", "geom_errorbar",
  "facet_grid", "facet_wrap",
  "scale_fill_gradient", "scale_fill_brewer", "scale_x_continuous", "scale_y_continuous",
  "theme", "theme_bw", "theme_classic", "theme_dark", "theme_void", "element_text",
  // cowplot / stringr, loaded in some chapters only
  "plot_grid", "str_wrap",
];

const DEFAULT_PACKAGES = ["dplyr", "ggplot2", "tidyr", "readr", "stringr"];
function packageList(packages) {
  const p = (packages && packages.length ? packages : DEFAULT_PACKAGES).slice();
  if (p.length === 1) return p[0];
  return p.slice(0, -1).join(", ") + " and " + p[p.length - 1];
}

/*
 * Explain a runtime error. `text` is what the console rendered; `ctx` is {source, objects, packages}.
 * Returns {message, try} or null when we have nothing useful to add — and saying nothing is the right
 * answer more often than it looks. A wrong hint is worse than no hint: it sends the student off to fix
 * something that was never broken.
 */
export function explainError(text, ctx) {
  const c = ctx || {};
  const objects = c.objects || [];
  const src = c.source || "";
  const hint = (message, tryThis) => ({ message, try: tryThis || null });

  // Parse errors: our own structural analysis is strictly better than R's position, so prefer it.
  if (PARSE_ERROR.test(text)) {
    const problems = structuralProblems(src);
    if (problems.length) return hint(problems[0].message);
    return hint("R could not read your code as written — the usual causes are a missing comma, a missing operator between two things, or a bracket in the wrong place.");
  }

  /*
   * The blank again, this time as a RUNTIME error. `____` is a legal R identifier, so a cell run with the
   * blank still in it reports a missing object or a missing function — and the ordinary hints for those
   * ("check the spelling", "did you mean…") are worse than useless here, because the student did not
   * mistype anything. Matched on the error text rather than the source so it fires even when the blank
   * sits in code the student pasted from elsewhere.
   */
  const blankName = text.match(/(?:object '(_{3,})' not found|could not find function "(_{3,})")/);
  if (blankName) {
    return hint("That is the blank in the exercise — you have run the cell before filling it in. Replace " +
                "the underscores with what the question is asking for, then run it again.");
  }

  let m = text.match(/object '([^']+)' not found/);
  if (m) {
    const name = m[1];
    const near = didYouMean(name, objects);
    if (near) return hint(`R has nothing called ${name}. There is one called ${near} — is that the one you meant?`);
    // The sandbox has an Environment pane to point at; a room does not, so `envLabel` gates that half.
    const where = c.envLabel
      ? ` Check the spelling, and check the ${c.envLabel} — if it is not listed there, it does not exist yet.`
      : " Check the spelling — if you have not created it or loaded it yet, it does not exist.";
    // Name a dataset the student actually has in front of them, not the book's example.
    const sets = c.datasets || [];
    const data = sets[0] || "your_data";
    /*
     * When the missing name is nowhere near anything that exists, the likeliest cause in this book is a
     * dataset that simply is not loaded here — the wrangling chapter's prose is built on `ny_trees`,
     * which is 55 MB and deliberately absent from the browser session, so a student pasting those
     * examples gets this error with no near name to suggest. Listing what IS loaded answers that in one
     * line. Capped, because a long list stops being readable.
     */
    const available = sets.length && sets.length <= 8
      ? ` The data loaded here is: ${sets.join(", ")}.`
      : "";
    return hint(
      `R has nothing called ${name}.` + where + available,
      `colnames(${data})  # if ${name} is meant to be a column, it only works inside the data`);
  }

  m = text.match(/could not find function "([^"]+)"/);
  if (m && /^%.*%$/.test(m[1])) {
    // A %...% OPERATOR, not a function — `%<%` is the pipe with its arrow turned round. The generic
    // "check the spelling or it lives in another package" is the wrong advice for this: there is no
    // package, and the student needs the right operator, not a hunt.
    const near = didYouMean(m[1], ["%>%", "%in%"]);
    if (near === "%>%") {
      return hint(`R has no operator called ${m[1]}. The pipe is %>% — its arrow points forward, toward the next step.`);
    }
    if (near) return hint(`R has no operator called ${m[1]}. Did you mean ${near}?`);
    return hint(`R has no operator called ${m[1]}. The ones you will use here are %>% (the pipe) and %in%.`);
  }
  if (m) {
    const near = didYouMean(m[1], KNOWN_FUNCTIONS.concat(c.functions || []));
    if (near) return hint(`R has no function called ${m[1]}. Did you mean ${near}()?`);
    return hint(`R has no function called ${m[1]}. Check the spelling, or it may live in a package that is not loaded here (you have ${packageList(c.packages)}).`);
  }

  m = text.match(/there is no package called ['‘]([^'’]+)['’]/);
  if (m) {
    return hint(`The package ${m[1]} is not available in the browser — packages cannot be installed here. You have ${packageList(c.packages)}.`);
  }

  // The headline webR leaves us when a name in aes() is wrong; R's own "Caused by: object 'x' not
  // found" is the part webR threw away, so reconstruct the meaning instead of the text.
  if (/Problem while computing aesthetics|Problem while mapping/i.test(text)) {
    return hint(
      "One of the names inside aes() does not match a column in your data. R usually names the culprit here, but the browser drops that part of the message — so check the spelling of each name in aes() against the columns.",
      "colnames(your_data)");
  }

  /*
   * `mapping` must be created by `aes()`: the second thing inside ggplot() was not an aes(). By far the
   * commonest route here is piping the data in AND naming it again — `d %>% ggplot(d, aes(...))` — so
   * the pipe supplies d as the data and the written `d` lands in the aes() slot. The thrown error's call
   * shows it as `ggplot(., d, …)`, the dot being the piped-in data; the source check covers a surface
   * whose error text has lost the call.
   */
  if (/`mapping` must be created by `aes\(\)`/.test(text)) {
    const piped = /ggplot\(\s*\.\s*,/.test(text) || /%>%\s*ggplot\(\s*(?!aes\s*\()[\w.]+\s*,/.test(src);
    if (piped) {
      return hint("You piped the data into ggplot() with %>% and ALSO named it inside ggplot(). The pipe " +
                  "already hands ggplot() the data, so the name you wrote lands where aes() should be. " +
                  "Take the data's name out of ggplot( … ).");
    }
    return hint("The second thing inside ggplot() has to be wrapped in aes(): the data first, then " +
                "aes(x = …, y = …).");
  }

  if (/We detected a named input|named argument/i.test(text)) {
    return hint('You used = where R wants ==. Inside filter(), lake == "Lava_Lake" TESTS whether they are equal; lake = "Lava_Lake" tries to ASSIGN, which is not allowed there.');
  }

  if (/Discrete value supplied to a continuous scale/i.test(text)) {
    return hint("That column holds text or categories, but the scale you asked for expects numbers. Either drop the scale_*_continuous() line, or plot a numeric column on that axis.");
  }

  if (/Continuous value supplied to a discrete scale/i.test(text)) {
    return hint("That column holds numbers, but the scale you asked for expects categories.");
  }

  if (/non-numeric argument to binary operator/i.test(text)) {
    return hint("You are doing arithmetic on something that is not a number — often a text column, or a whole data frame where a single column was meant.");
  }

  if (/argument "([^"]+)" is missing, with no default/.test(text)) {
    const arg = text.match(/argument "([^"]+)" is missing/)[1];
    return hint(`The function needs its ${arg} argument and you have not given it one.`);
  }

  if (/\$ operator is invalid for atomic vectors/i.test(text)) {
    return hint("You used $ on something that is not a data frame or list — often a single column that has already been pulled out.");
  }

  if (/undefined columns selected|subscript out of bounds/i.test(text)) {
    return hint("You asked for a column or position that is not there.", "colnames(your_data)");
  }

  // dplyr wraps failures from inside a verb like this, and again webR drops the "Caused by" detail.
  m = text.match(/In argument: `([^`]+)`/);
  if (m) {
    return hint(`Something went wrong inside ${m[1]}. A common cause is a bare word where text was meant — R reads Lava_Lake as the name of an object, while "Lava_Lake" is the text.`);
  }

  return null;
}

/*
 * The silent failure: `ggplot(...)` then `geom_point()` on the next line WITHOUT a trailing +. R runs two
 * separate expressions, prints the internals of the second, and draws nothing. No error at all, which is
 * why it needs its own check — the student sees output and reasonably assumes it worked.
 */
export function looksLikeOrphanLayer(outputText) {
  if (!outputText) return null;
  const t = outputText.trim();
  if (!/^(mapping:|geom_|stat_|position_|<ggproto)/m.test(t)) return null;
  if (!/^(mapping:|geom_|stat_|position_|<ggproto)/.test(t.split("\n")[0])) return null;
  return {
    message: "That looks like a single ggplot layer printed on its own rather than a plot. Check that the line before it ends with a + — every layer has to be joined to the one above.",
  };
}
