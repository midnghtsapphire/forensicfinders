# ══════════════════════════════════════════════════════════════════════════════════════════
# Who:  Claude Code (claude-opus-5), for Audrey Evans (midnghtsapphire)
# When: 2026-11-04
# Why:  Audit item 4: nothing in this repository enforced VISITING_AGENTS.md section 1.
#       The Anti-Scaffolding Enforcer lives in revvel-standards and runs on pull requests
#       there; forensicfinders inherits the standard by convention and checked none of it.
#       PR #8 added a scan over blue-ocean-sar/multi_proxy/ and said plainly why it stopped
#       there: at that moment the same vocabulary hit lines in other files, and widening the
#       scan would have made main red for defects the scan was added to REPORT rather than
#       ones it introduced, which GREEN_MAIN_STANDARD.md forbids. Those lines are resolved
#       as of this change, so the scan can now cover the whole repository, which is the
#       form the standard is actually about.
# What: NEW FILE, purely additive. Nothing else was changed by it. The vocabulary and the
#       matching live in language_scan.py so that this guard and PR #8's narrower one share
#       one implementation instead of two copies of the same patterns.
#       Registered as component 1000 in registry.json -- without that, test_registry_
#       coverage.py (component 995) fails this file as an orphan, correctly: a test no
#       component runs is not coverage.
# What Worked: 203 .py files scanned, zero flagged lines in live code. Every assertion here
#       was run, not asserted. The 16 lines that were outstanding when PR #8 shipped are
#       accounted for exactly: 11 are exempted by the two shape rules in language_scan.py
#       (4 identifier-context, 7 fake-secret-prefix) and 5 were fixed, all five comment-only
#       with the previous text preserved per RVS-AGENT-001.
# Notes: Four anti-decoration properties, per RVS-VERIFY-001 section 5.3 -- "a marker is a
#       claim; if nothing checks the claim, the marker is decoration":
#       (1) The matcher self-tests. Every word and phrase is asserted to fire on a synthetic
#           line before the repository result is trusted, so a matcher broken by a later
#           edit fails loudly instead of reporting a clean repository.
#       (2) Finding no files is a FAILURE. A walk that matched nothing would otherwise pass
#           every assertion below while reading nothing at all.
#       (3) Both exemption RULES are tested from both sides -- a case each rule must exempt
#           and a case it must NOT. An exemption that quietly widened would hide real
#           defects, and that is the only way this guard can fail silently.
#       (4) Unbalanced region delimiters are a FAILURE. One unterminated delimiter would
#           swallow the rest of a file, so the guard would scan less than it claims to.
#       There is NO file-level exemption list, and this file needs none for itself: the
#       vocabulary is assembled from fragments in language_scan.py, so neither that module
#       nor this guard matches itself. A guard that exempts itself teaches the next reader
#       that exemptions are normal.
#       NOT checked here, deliberately: prose quality. This finds a fixed vocabulary, which
#       is what the enforcer finds. A function that silently returns the wrong answer
#       without using any of these words is a defect no pattern catches, and one such case
#       is reported untouched in coldtrace/backend/services/sentinel.py -- its docstring
#       promises DataArrays and the function returns bytes. Pattern checks are a floor, not
#       a ceiling, and pretending otherwise would be the same mistake as trusting a marker.
# ══════════════════════════════════════════════════════════════════════════════════════════
"""No live line in this repository may carry the vocabulary of deferred work."""
import os
import sys
import unittest

SAR_ROOT = os.path.dirname(os.path.abspath(__file__))
if SAR_ROOT not in sys.path:
    sys.path.insert(0, SAR_ROOT)

import language_scan as scan  # noqa: E402


class VocabularyMatcherWorks(unittest.TestCase):
    """The matcher must be proven to fire before a clean result from it means anything."""

    def test_every_word_is_matched(self):
        for word in scan.ALL_WORDS:
            line = "x = 1  # " + word + " finish this"
            self.assertIn(
                word, scan.hits(line),
                f"the matcher no longer fires on {word!r}. Until that is fixed, a clean "
                f"repository result from this guard means nothing.")

    def test_every_phrase_is_matched(self):
        for phrase in scan.PHRASES:
            line = "# shipping " + phrase + " of the work"
            self.assertIn(phrase, scan.hits(line), f"the matcher no longer fires on {phrase!r}")

    def test_case_sensitivity_matches_the_enforcer(self):
        """The two markers are case-sensitive and the two words are not, as the workflow greps them."""
        for word in scan.CASE_SENSITIVE_WORDS:
            self.assertEqual((), scan.hits("# " + word.lower() + " handler"),
                             f"{word!r} must be matched case-sensitively, as the enforcer greps it")
        for word in scan.CASE_INSENSITIVE_WORDS:
            self.assertIn(word, scan.hits("# " + word.upper() + " here"),
                          f"{word!r} must be matched case-insensitively, as the enforcer greps it")

    def test_a_clean_line_is_not_flagged(self):
        self.assertEqual((), scan.hits("    return np.asarray(band), meta"))


class ExemptionsAreRulesNotAllowlists(unittest.TestCase):
    """Each exemption is tested from both sides. A widened exemption hides real defects."""

    def test_enforcer_exemptions_are_honoured(self):
        for word, subs in scan.ENFORCER_EXEMPT.items():
            for sub in subs:
                self.assertEqual(
                    (), scan.hits("    value = " + sub + "  # fine"),
                    f"the enforcer exempts a line containing {sub!r} for {word!r}; this "
                    f"repository must fail for the same reasons that workflow does, not "
                    f"different ones.")

    def test_rule_1_exempts_a_longer_identifier(self):
        """`_placeholders(path)` names URI-template slots; the word is not deferring work."""
        self.assertEqual((), scan.hits("    for p in _" + scan.WORD_STANDIN + "s(path):"))

    def test_rule_1_does_not_exempt_the_plain_english_plural(self):
        """One-sided on purpose: a trailing word character would exempt ordinary prose."""
        line = "        # these values were " + scan.WORD_STANDIN + "s that nobody replaced"
        self.assertIn(
            scan.WORD_STANDIN, scan.hits(line),
            "rule 1 must test the character BEFORE the match only. Exempting a trailing "
            "word character would exempt the plural, which is exactly the prose this "
            "guard exists to find.")

    def test_rule_1_does_not_exempt_the_deferral_markers(self):
        """The markers are not English words, so one inside an identifier is still a marker."""
        for word in scan.CASE_SENSITIVE_WORDS:
            self.assertIn(word, scan.hits("    my_" + word + "_list = []"))

    def test_rule_2_exempts_a_quoted_fake_secret_prefix(self):
        line = '    SECRET = "' + scan.WORD_STANDIN + '-" + "secret" * 3'
        self.assertEqual((), scan.hits(line))

    def test_rule_2_requires_the_quote_and_the_hyphen(self):
        """Without the string-literal shape it is ordinary prose and must still be flagged."""
        for line in ("    # a " + scan.WORD_STANDIN + "-shaped value goes here",
                     '    name = "' + scan.WORD_STANDIN + ' arrays"'):
            self.assertIn(
                scan.WORD_STANDIN, scan.hits(line),
                f"rule 2 must only exempt a quoted literal opening with the word and a "
                f"hyphen; it widened and now exempts {line!r}")


class SkippedRegionsAreDelimitedAndNarrow(unittest.TestCase):
    """Two machine-delimited regions are skipped. Live code gets no exceptions at all."""

    def test_a_preserved_block_is_skipped_and_the_line_after_it_is_not(self):
        text = "\n".join([
            "live_one = 1",
            "# " + scan.DISABLED_OPEN + " AGENT: x | STATUS: REPLACED",
            "# REASON: the replaced line has to be quotable.",
            "#     raise NotImplementedError  # " + scan.MARKER_DEFER + " wire this up",
            "# " + scan.DISABLED_END,
            "after = 2  # " + scan.MARKER_DEFER + " still live",
        ])
        parsed = scan.scan_text(text)
        numbers = [n for n, _ in parsed.lines]
        self.assertEqual([1, 6], numbers, "the block's own lines must not be scanned")
        flagged = [n for n, line in parsed.lines if scan.hits(line)]
        self.assertEqual(
            [6], flagged,
            "a line after the block's end must be scanned. If it is not, one unterminated "
            "block hides the rest of the file.")

    def test_a_header_box_is_skipped_and_the_code_after_it_is_not(self):
        rule = "# " + "═" * 40
        text = "\n".join([
            rule,
            "# Why: it replaced a line reading " + scan.MARKER_DEFER + ": real path",
            rule,
            "live = 3  # " + scan.WORD_STANDIN + " left behind",
        ])
        parsed = scan.scan_text(text)
        self.assertEqual([4], [n for n, _ in parsed.lines])
        self.assertEqual(1, len([1 for _, line in parsed.lines if scan.hits(line)]))

    def test_an_unterminated_block_is_visible_to_the_caller(self):
        text = "# " + scan.DISABLED_OPEN + " AGENT: x\n# REASON: y\nlive = 1\n"
        parsed = scan.scan_text(text)
        self.assertTrue(parsed.in_block_at_eof)
        self.assertNotEqual(parsed.disabled_opens, parsed.disabled_ends)


class RepositoryHasNoDeferredWorkLanguage(unittest.TestCase):
    """The assertion this file exists for."""

    @classmethod
    def setUpClass(cls):
        cls.files = scan.python_files(SAR_ROOT)
        cls.flagged = []
        cls.broken = []
        for path in cls.files:
            found, parsed = scan.scan_file(path)
            rel = os.path.relpath(path, SAR_ROOT).replace(os.sep, "/")
            if parsed.disabled_opens != parsed.disabled_ends or parsed.in_block_at_eof:
                cls.broken.append(f"{rel}: {parsed.disabled_opens} opened, {parsed.disabled_ends} ended")
            elif parsed.in_box_at_eof:
                cls.broken.append(f"{rel}: a header box is never closed ({parsed.header_rules} rules)")
            for number, line, words in found:
                cls.flagged.append(f"{rel}:{number}: {','.join(words)}: {line.strip()[:90]}")

    def test_the_scan_actually_read_the_repository(self):
        """A walk that matched nothing would pass every other assertion while reading nothing."""
        self.assertGreater(
            len(self.files), 150,
            f"only {len(self.files)} .py files found under {SAR_ROOT}. The walk is wrong, or "
            f"language_scan.SKIP_DIRS now excludes real code. This guard proves nothing "
            f"until that is explained. 203 files existed when it was written.")

    def test_region_delimiters_balance_in_every_file(self):
        self.assertEqual(
            [], self.broken,
            "these files have an unbalanced skipped region, so this guard silently scanned "
            "less of them than it reports:\n    " + "\n    ".join(self.broken) +
            "\nClose the delimiter -- do NOT loosen scan_text().")

    def test_no_live_line_carries_the_vocabulary(self):
        self.assertEqual(
            [], self.flagged,
            "VISITING_AGENTS.md section 1: \"Ship working code, not plans.\" These live "
            "lines carry the vocabulary revvel-standards' anti-scaffolding-enforcer.yml "
            "flags:\n    " + "\n    ".join(self.flagged) +
            "\nFinish the work, or -- if the word is genuinely naming something rather "
            "than deferring something -- add a RULE to language_scan.py describing the "
            "shape, with its reason, the way the two rules there do. Do not add the file "
            "to an exemption list; there is no exemption list, and the first one would "
            "teach the next reader that exemptions are normal.")


if __name__ == "__main__":
    unittest.main()
