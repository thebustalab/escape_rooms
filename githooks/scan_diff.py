#!/usr/bin/env python3
"""
scan_diff.py — read a unified diff on stdin, flag added lines that look like a
credential or a private path/hostname. Exits 1 (and prints findings) if anything
matches, exits 0 on a clean diff. Only ADDED lines are scanned ('+' lines, not the
'+++ b/path' header) — this is a scan of what would actually leave the working
tree, not the whole file.

Findings are printed with the offending literal partly redacted, so a genuine hit
does not paste the real secret into the terminal / a CI log.

TWO TIERS.  PATTERNS (always on) is the credential / private-path core.  IDENTITY_PATTERNS
is opt-in via `--identity` and covers the personal-contact half of public_tools/AGENTS.md's
one rule that matters ("no personal-email defaults") and its pre-publish checklist grep
(`/home/bustalab|/Users/bust0037|d.umn.edu|umn.edu|@gmail`, escaped in the checklist).  It is opt-in because the
callers differ: a public TOOL repo must never carry a personal address, while the academic
WEBSITE repo may legitimately publish a contact one, and a gate that fires on that gets
disabled.  public_tools' pre-push hooks pass `--identity`; the website ones do not.  This
file stays byte-identical in every repo that carries it — the scope lives in the caller, not
in a forked copy.

The identity tier matches EMAIL-SHAPED strings, not the checklist's bare `umn.edu` domain
grep: a bare-domain hit needs a human to look at it, which is what the checklist is for, and
a link to a umn.edu page is not a leak.  Run the checklist; this is the backstop.
"""
import re
import sys

PATTERNS = [
    (r"sk-[A-Za-z0-9_-]{20,}", "OpenAI/Anthropic-style secret key (sk-...)"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub personal access token (ghp_...)"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub fine-grained PAT (github_pat_...)"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key ID (AKIA...)"),
    (r"AIza[0-9A-Za-z_\-]{30,}", "Google API key (AIza...)"),
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token (xox...)"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "PEM private key block"),
    (r"export\s+\w*_API_KEY\w*\s*=\s*\S", "shell export of an *_API_KEY value"),
    (r"export\s+\w*_TOKEN\w*\s*=\s*\S", "shell export of an *_TOKEN value"),
    (r"\bACCESS_TOKEN\w*\s*=\s*[\"']", 'ACCESS_TOKEN = "..." literal'),
    (r"\b\w*API_KEY\w*\s*=\s*[\"']", 'API_KEY = "..." literal'),
    (r"[\"'][A-Fa-f0-9]{32,}[\"']", "long hex literal (32+ chars), token-shaped"),
    (r"[\"'][A-Za-z0-9+/]{40,}={0,2}[\"']", "long base64-shaped literal (40+ chars)"),
    (r"/home/bustalab\b", "private path (/home/bustalab)"),
    (r"/Users/bust0037\b", "private path (/Users/bust0037)"),
    (r"\bbustalab-desktop\b", "internal hostname (host2)"),
    (r"\bsystem76-pc(\.localdomain)?\b", "internal hostname (host1)"),
    (r"\bspark-e5b5\b", "internal hostname (dgx)"),
    (r"\bbustalab\.d\.umn\.edu\b", "internal hostname (host1)"),
    (r"\b131\.212\.57\.\d{1,3}\b", "internal lab IP (131.212.57.0/24)"),
]
COMPILED = [(re.compile(p), label) for p, label in PATTERNS]

# The four assignment-shaped rules above match `NAME = <anything>`, so they also match a
# DOCUMENTED placeholder — `export CANVAS_TOKEN="…"` in canvas-assignments' README was a
# standing false positive that would have blocked a fresh-branch push. Only these four are
# placeholder-suppressible; a `sk-`/`ghp_`/PEM prefix match never is, because those shapes
# cannot be a placeholder.
PLACEHOLDER_SUPPRESSIBLE = {
    "shell export of an *_API_KEY value",
    "shell export of an *_TOKEN value",
    'ACCESS_TOKEN = "..." literal',
    'API_KEY = "..." literal',
}
_VALUE_RE = re.compile(r"""=\s*["'`]?([^"'`\n]*)""")
_PLACEHOLDER_PREFIX = ("REPLACE", "YOUR", "INSERT", "PASTE", "XXX", "CHANGEME", "TODO", "EXAMPLE")


def is_placeholder_value(tail: str) -> bool:
    """True when the value assigned in `tail` is an obvious stand-in, not a real secret."""
    m = _VALUE_RE.search(tail)
    if not m:
        return False
    v = m.group(1).strip()
    if not v or v in ("…", "...", "<...>"):
        return True
    if v[0] in "<${":
        return True
    if v.upper().startswith(_PLACEHOLDER_PREFIX):
        return True
    return set(v.upper()) <= {"X", "*", ".", "-", "_", "…"}

# Opt-in tier (`--identity`), for the public TOOL repos. See the module docstring.
IDENTITY_PATTERNS = [
    (r"[A-Za-z0-9._%+-]*@[A-Za-z0-9.-]*\bumn\.edu\b", "personal/institutional email address (umn.edu)"),
    (r"[A-Za-z0-9._%+-]*@gmail\.com\b", "personal email address (@gmail)"),
    (r"\bbust0037\b", "Lucas's x500 (bust0037)"),
    (r"\blucasbusta\d*@", "Lucas's personal email local-part"),
]
COMPILED_IDENTITY = [(re.compile(p, re.IGNORECASE), label) for p, label in IDENTITY_PATTERNS]


def redact(literal: str) -> str:
    if len(literal) <= 10:
        return literal[0] + "..." + literal[-1] if len(literal) > 2 else "***"
    return literal[:4] + "…redacted…" + literal[-4:]


# The scanner's own source IS a list of the patterns it looks for, so a diff that adds or
# edits `githooks/` trips every rule in it. That is not hypothetical — it blocked the very
# first commit of a freshly scaffolded tool, and public_tools/AGENTS.md requires the pair to
# be COMMITTED into each repo. So the scanner's own directory is skipped. Accepted blind
# spot: a secret hidden inside githooks/ would not be caught here.
SELF_DIR = "githooks/"


def added_lines(diff_text: str):
    """Yield added lines, skipping the scanner's own `githooks/` sources."""
    current = ""
    for raw in diff_text.splitlines():
        if raw.startswith("+++"):
            path = raw[4:].strip()
            if path.startswith(("a/", "b/")):
                path = path[2:]
            current = path
            continue
        if raw.startswith("---") or raw.startswith("diff --git"):
            continue
        if raw.startswith("+"):
            if current.startswith(SELF_DIR) or "/" + SELF_DIR in current:
                continue
            yield raw[1:]


def scan(diff_text: str, identity: bool = False):
    compiled = COMPILED + (COMPILED_IDENTITY if identity else [])
    findings = []
    for line in added_lines(diff_text):
        for regex, label in compiled:
            m = regex.search(line)
            if not m:
                continue
            if label in PLACEHOLDER_SUPPRESSIBLE and is_placeholder_value(line[m.start():]):
                continue
            findings.append((label, redact(m.group(0))))
    return findings


def main():
    identity = "--identity" in sys.argv[1:]
    diff_text = sys.stdin.read()
    findings = scan(diff_text, identity=identity)
    if not findings:
        return 0
    print("", file=sys.stderr)
    print("pre-push: BLOCKED — the outgoing diff looks like it contains a credential", file=sys.stderr)
    print("or a private path/hostname:", file=sys.stderr)
    for label, sample in findings:
        print(f"  {label}: {sample}", file=sys.stderr)
    print("", file=sys.stderr)
    print("If every hit above is a false positive, bypass with SKIP_SECRET_SCAN=1 git push.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
