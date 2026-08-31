// Every authoring editor's TYPES whitelist must cover every type the PLAYER ENGINE dispatches on,
// and no editor may silently rewrite an authored type.
//
// WHAT BROKE (2026-08-27 -> 2026-08-29). `ui/hotspots_edit.html` kept a TYPES whitelist and coerced any
// type absent from it to "puzzle" on load, then saved that back. `ledger` and `elevmap` were absent, so
// a single box-editor round-trip silently retyped them. Temple's escape (`register_gods`, a `ledger`)
// became an unclickable `puzzle`: as a puzzle with no `question`/`check` the click threw inside
// buildQuestion and Pannellum swallows handler throws, so there was no error anywhere. Worse, a `ledger`
// is the UNGRADED escape, so a coerced one becomes an extra GRADED room in the codec — temple went to
// five graded rooms against a four-entry decode_codes.R key, which would have mis-decoded every student
// submission. It also breaks `_attach_planned_content`, which matches on (type, slug(label)), so the
// hotspot silently stops receiving its authored content.
//
// WHY THIS TEST EXISTS RATHER THAN A NOTE. The first fix (2026-08-29) patched hotspots_edit.html only —
// and MISSED `ui/reproject_test.html`, which has its own copy of the same list and the same coercion, and
// is the editor the build_world console's "edit hotspots" button actually opens. The bug was still fully
// live after being declared fixed; a canon_slim panel caught it. Two copies means a third is possible, so
// the invariant is asserted across ALL editors by globbing, not by naming the two we know about.
const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const ENGINE = path.join(ROOT, "shared", "pano-player.js");
const EDITOR_DIRS = [path.join(ROOT, "authoring_v2", "ui")];   // z_authoring_v1 is retired history — excluded

// The engine's own dispatch list, read from source so the test can't drift from it.
function engineTypes() {
  const src = fs.readFileSync(ENGINE, "utf8");
  const found = new Set([...src.matchAll(/h\.type === "([a-z]+)"/g)].map(m => m[1]));
  found.add("ambient");            // rendered as decor: no dispatch branch, but a legal authored type
  return found;
}

function editors() {
  return EDITOR_DIRS.flatMap(d => fs.existsSync(d)
    ? fs.readdirSync(d).filter(f => f.endsWith(".html")).map(f => path.join(d, f))
    : []).filter(f => /const TYPES\s*=/.test(fs.readFileSync(f, "utf8")));
}

test("every editor's TYPES covers every engine-dispatched hotspot type", () => {
  const expected = engineTypes();
  const found = editors();
  assert.ok(found.length >= 2, `expected to find the editors, got ${found.length}`);
  for (const file of found) {
    const src = fs.readFileSync(file, "utf8");
    const list = src.match(/const TYPES\s*=\s*\[([^\]]*)\]/)[1];
    const declared = new Set([...list.matchAll(/"([a-z]+)"/g)].map(m => m[1]));
    for (const t of expected) {
      assert.ok(declared.has(t),
        `${path.basename(file)} TYPES is missing "${t}" — an absent type is silently retyped, ` +
        `which kills the hotspot in play and breaks _attach_planned_content's (type,label) match`);
    }
  }
});

test("no editor silently rewrites an authored hotspot type", () => {
  for (const file of editors()) {
    const src = fs.readFileSync(file, "utf8");
    assert.ok(!/TYPES\.includes\([^)]*\)\s*\?[^:]*:\s*"puzzle"/.test(src),
      `${path.basename(file)} still coerces an unknown type to "puzzle" — preserve it and console.warn instead`);
  }
});
