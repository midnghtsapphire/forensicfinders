# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  VISITING_AGENTS.md section 1 forbids shipping deferred work dressed as finished
#       work. revvel-standards enforces it with .github/workflows/anti-scaffolding-
#       enforcer.yml, which greps ADDED lines in a pull request for a fixed vocabulary.
#       That workflow lives in revvel-standards. forensicfinders inherits the standard by
#       convention and, until 2026-11-04, enforced none of it -- which is how four flagged
#       lines sat in blue-ocean-sar/multi_proxy/ untouched from 2026-10-24.
#       PR #8 added a scan over multi_proxy/ only. This module exists so that the
#       repository-wide guard does not become a second copy of that word list:
#       VISITING_AGENTS.md section 2 -- "Do not re-scaffold existing tooling ... Extend
#       them; don't clone them under a new name" -- applies to my own code too.
# What: NEW FILE, purely additive. Nothing else was changed by it. It is a library, not a
#       test: test_language_scan.py is the guard that uses it, and
#       multi_proxy/test_loader_and_fetcher.py now imports it instead of carrying its own
#       copy of the same patterns.
# What Worked: the word list and the per-word exemptions below were transcribed from the
#       enforcer workflow and then checked by running them over this repository and
#       comparing the result against a line-by-line hand inventory. They agree exactly:
#       16 flagged lines outside multi_proxy across 8 files, which is the number this
#       module reproduces. An earlier count of "22 across 10 files" was wrong -- it came
#       from a loose `grep -i` of my own that matched four lowercase local variables named
#       after the deferral marker (the enforcer greps that one case-sensitively) and two
#       Streamlit attributes the enforcer explicitly exempts.
# Notes: Two exemptions here are MINE, not the enforcer's, and each is a rule about shape
#       rather than a list of forgiven files. There is no file-level exemption, not even
#       for this module or its guard: every word below is assembled from fragments at
#       import time so that this file does not match itself. That is deliberate. A guard
#       that exempts itself teaches the next reader that exemptions are normal.
#       The shape of an exemption matters more than its existence. "This file is allowed
#       to say the word" cannot be reasoned about by the next person; "the word is part of
#       a longer identifier, so it is naming something rather than deferring something"
#       can be, and is wrong in a way that shows up as a missed defect rather than as
#       silence.
# ══════════════════════════════════════════════════════════════════════════════════════════
"""Matcher for the unfinished-work vocabulary VISITING_AGENTS.md section 1 forbids.

The vocabulary, the per-word exemptions, and the case sensitivity of each are taken from
revvel-standards/.github/workflows/anti-scaffolding-enforcer.yml so that this repository
fails for the same reasons that workflow would fail, and not for different ones.

Every word and phrase is built by concatenating fragments. Written out whole they would
make this module, and the guard that imports it, match themselves on every run.
"""
import collections
import os
import re

# ── The vocabulary ────────────────────────────────────────────────────────────────────────
# Assembled from fragments; see the module docstring for why.

# Matched case-sensitively, exactly as the enforcer greps them. These two are not English
# words. They exist only as deferral markers, so unlike the two below they are flagged even
# when they appear inside a longer identifier.
MARKER_DEFER = "TO" + "DO"
MARKER_BROKEN = "FIX" + "ME"
CASE_SENSITIVE_WORDS = (MARKER_DEFER, MARKER_BROKEN)

# Matched case-insensitively, exactly as the enforcer greps them. Both are ordinary English
# words with legitimate uses, which is why the two shape exemptions below exist.
WORD_FRAME = "scaff" + "old"
WORD_STANDIN = "place" + "holder"
CASE_INSENSITIVE_WORDS = (WORD_FRAME, WORD_STANDIN)

ALL_WORDS = CASE_SENSITIVE_WORDS + CASE_INSENSITIVE_WORDS

# Matched case-insensitively. The enforcer greps these as one alternation.
PHRASES = (
    "phase " + "1",
    "phase " + "2",
    "mvp " + "first",
    "coming " + "soon",
    "not yet " + "implemented",
)

# ── The enforcer's own exemptions, transcribed ────────────────────────────────────────────
# A line containing any of these substrings is not flagged for that word. The enforcer
# applies them with `grep -v`, i.e. to the whole line, not to the match -- so these are
# line-level substring tests here too, on purpose.
ENFORCER_EXEMPT = {
    MARKER_DEFER: (MARKER_DEFER + ": See issue #",),
    WORD_FRAME: (
        "scaff" + "olding tools like npm init",
        "anti-" + WORD_FRAME,
        "anti_" + WORD_FRAME,
    ),
    WORD_STANDIN: (
        WORD_STANDIN + "=",
        "::" + WORD_STANDIN,
        WORD_STANDIN + " values",
        'alt="' + WORD_STANDIN + '"',
        "search projects",
    ),
}

# The enforcer also drops a deferral marker on a line that links a tracking issue.
_ISSUE_LINK = re.compile(r"github\.com.*issues")

# ── Exemptions added here, each a rule about shape ────────────────────────────────────────
# RULE 1, identifier context. A match whose preceding character is a word character is part
# of a longer Python identifier, so the word is naming a thing rather than deferring work.
# The case that forced this: opendata/records_adapter.py defines `_placeholders(path)` and
# calls it three times. In a URI template the variable slots ARE called that -- it is the
# vocabulary of RFC 6570, not a promise of future work. Only the two case-insensitive words
# get this exemption, for the reason given beside their definition.
#
# Deliberately one-sided: the preceding character only, never the following one. Allowing a
# trailing word character would exempt the plain English plural, and prose like "these were
# only stand-ins" is exactly what this guard is for.

# RULE 2, deliberately low-entropy fake secrets. A string literal opening with the stand-in
# word followed by a hyphen is one of the opendata tests' fake credentials. Those values are
# built to look unmistakably fake so that secret scanners do not trip on them -- and
# GitGuardian is the one check that actually runs on this repository's pull requests, since
# the billing lock blocks GitHub Actions. Renaming them would either reintroduce
# random-looking values or invent a second convention for the same thing. Seven lines across
# four opendata test files rely on this.
_FAKE_SECRET = re.compile("[\"']" + WORD_STANDIN + "-", re.IGNORECASE)

# ── Delimited regions that are skipped ────────────────────────────────────────────────────
# Two regions, both machine-delimited, and nothing else.
#
# A REVVEL-DISABLED block, which RVS-AGENT-001 (COMMENT-DONT-DELETE) requires to hold the
# replaced code verbatim, and a section 2.2 header box, which SELF_HEALING_STANDARDS.md
# requires to say what changed and why. Both have to be able to name the thing that was
# removed; a standard that orders you to quote the old line cannot also forbid quoting it.
#
# This is not an allowlist of violations. Nothing is forgiven inside these regions because
# nothing live is inside them -- that is what makes them regions. An unbalanced delimiter
# would silently swallow the rest of a file, so scan_text() counts them and the guard
# asserts they balance.
DISABLED_OPEN = "REVVEL-" + "DISABLED |"
DISABLED_END = "REVVEL-" + "DISABLED-END"
HEADER_RULE = re.compile("^\\s*#\\s*[═]{20,}")

SKIP_DIRS = frozenset({".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"})

ScanText = collections.namedtuple(
    "ScanText", "lines disabled_opens disabled_ends header_rules in_block_at_eof in_box_at_eof")


def _plain_find_all(haystack, needle):
    """Every start offset of needle in haystack."""
    out, i = [], haystack.find(needle)
    while i != -1:
        out.append(i)
        i = haystack.find(needle, i + 1)
    return out


def _is_identifier_char(ch):
    return ch.isalnum() or ch == "_"


def exempt(line, word, start):
    """True when this match of `word` at `start` in `line` is not a violation.

    Reasons are documented beside each rule above. Returns the reason as a truthy string so
    a caller can report WHY a line was passed over, rather than only that it was.
    """
    low = line.lower()
    for sub in ENFORCER_EXEMPT.get(word, ()):
        if word in CASE_SENSITIVE_WORDS:
            if sub in line:
                return "enforcer exemption: " + sub
        elif sub.lower() in low:
            return "enforcer exemption: " + sub
    if word == MARKER_DEFER and _ISSUE_LINK.search(line):
        return "enforcer exemption: links a tracking issue"
    if word in CASE_INSENSITIVE_WORDS and start > 0 and _is_identifier_char(line[start - 1]):
        return "rule 1: part of a longer identifier"
    if word == WORD_STANDIN and _FAKE_SECRET.search(line):
        return "rule 2: deliberately low-entropy fake secret"
    return ""


def hits(line):
    """The words and phrases this line is flagged for, after every exemption.

    One entry per distinct word, not per occurrence: the enforcer reports lines, not counts.
    """
    found = []
    low = line.lower()
    for word in CASE_SENSITIVE_WORDS:
        for start in _plain_find_all(line, word):
            if not exempt(line, word, start):
                found.append(word)
                break
    for word in CASE_INSENSITIVE_WORDS:
        for start in _plain_find_all(low, word.lower()):
            if not exempt(line, word, start):
                found.append(word)
                break
    for phrase in PHRASES:
        if phrase in low:
            found.append(phrase)
    return tuple(found)


def scan_text(text):
    """Split `text` into the lines that are live code and the delimiter bookkeeping.

    `lines` is a list of (1-based line number, line) outside both skipped regions. The
    remaining fields exist so a caller can refuse to trust a file whose delimiters do not
    balance, rather than quietly scanning less of it than it thinks.
    """
    lines = []
    opens = ends = rules = 0
    in_block = in_box = False
    for number, line in enumerate(text.splitlines(), 1):
        if DISABLED_OPEN in line:
            opens += 1
            in_block = True
            continue
        if DISABLED_END in line:
            ends += 1
            in_block = False
            continue
        if in_block:
            continue
        if HEADER_RULE.match(line):
            rules += 1
            in_box = not in_box
            continue
        if in_box:
            continue
        lines.append((number, line))
    return ScanText(lines, opens, ends, rules, in_block, in_box)


def scan_file(path):
    """(list of (line number, line, words), ScanText) for one file."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    parsed = scan_text(text)
    flagged = []
    for number, line in parsed.lines:
        words = hits(line)
        if words:
            flagged.append((number, line, words))
    return flagged, parsed


def python_files(root):
    """Every .py file under `root`, skipping SKIP_DIRS. Sorted, so reports are stable."""
    found = []
    for folder, subdirs, names in os.walk(root):
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
        for name in names:
            if name.endswith(".py"):
                found.append(os.path.join(folder, name))
    return sorted(found)
