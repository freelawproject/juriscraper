"""Tests for ASP.NET postback helpers."""

import base64
import re
import unittest

from juriscraper.lib.aspnet_utils import (
    WAF_SQLI_HEX_LITERAL_RE,
    breakup_hex_substrings,
)

# What a WAF's SQLi rule matches: "0x", either case, plus three or more hex
# digits. Verified against the live gateway in front of TAMES: "0x1a" passes,
# while "0x1a2" and "0X1a2" are both a 403.
SIGNATURE_RE = re.compile(r"0[xX][0-9a-fA-F]{3}")


class DefangWafSqliSignatureTest(unittest.TestCase):
    def test_hex_literal_runs_are_split(self):
        form = {"__VIEWSTATE": "abc0x1a2def"}

        defanged = breakup_hex_substrings(form)

        self.assertEqual(defanged["__VIEWSTATE"], "abc0\nx1a2def")
        self.assertIsNone(SIGNATURE_RE.search(defanged["__VIEWSTATE"]))

    def test_every_run_is_split(self):
        form = {"__VIEWSTATE": "0xdeadbeef mid 0XABC tail 0x123"}

        defanged = breakup_hex_substrings(form)

        self.assertIsNone(SIGNATURE_RE.search(defanged["__VIEWSTATE"]))

    def test_shorter_hex_runs_are_left_alone(self):
        """Fewer than three hex digits after the 0x doesn't trip the rule."""
        form = {"__VIEWSTATE": "0x1 and 0xab and 0xgg"}

        self.assertEqual(
            breakup_hex_substrings(form)["__VIEWSTATE"],
            "0x1 and 0xab and 0xgg",
        )

    def test_event_validation_is_defanged_too(self):
        form = {"__EVENTVALIDATION": "0x1a2"}

        self.assertEqual(
            breakup_hex_substrings(form)["__EVENTVALIDATION"], "0\nx1a2"
        )

    def test_decoded_viewstate_is_unchanged(self):
        """Base64 decoding ignores whitespace, so the ViewState MAC still
        validates after the rewrite.
        """
        # Valid Base64 that happens to carry the signature, which is exactly
        # how it turns up in a real ViewState: by coincidence, not by content.
        view_state = "AAA0x1a2AAAA"
        self.assertIsNotNone(SIGNATURE_RE.search(view_state))

        defanged = breakup_hex_substrings({"__VIEWSTATE": view_state})

        self.assertIsNone(SIGNATURE_RE.search(defanged["__VIEWSTATE"]))
        self.assertEqual(
            base64.b64decode(defanged["__VIEWSTATE"]),
            base64.b64decode(view_state),
        )

    def test_other_fields_are_left_untouched(self):
        """Non-Base64 fields can't take whitespace, so they're only logged."""
        form = {"__VIEWSTATE": "0x1a2", "ctl00$q": "0xdeadbeef"}

        defanged = breakup_hex_substrings(form)

        self.assertEqual(defanged["ctl00$q"], "0xdeadbeef")

    def test_input_is_not_mutated(self):
        form = {"__VIEWSTATE": "0x1a2"}

        breakup_hex_substrings(form)

        self.assertEqual(form["__VIEWSTATE"], "0x1a2")

    def test_clean_and_empty_bodies_survive(self):
        self.assertEqual(breakup_hex_substrings({}), {})
        self.assertEqual(
            breakup_hex_substrings({"__VIEWSTATE": "", "a": "b"}),
            {"__VIEWSTATE": "", "a": "b"},
        )
        clean = {"__VIEWSTATE": "no hex literals here"}
        self.assertEqual(breakup_hex_substrings(clean), clean)

    def test_regex_boundaries(self):
        self.assertIsNone(WAF_SQLI_HEX_LITERAL_RE.search("0x1a"))
        self.assertIsNotNone(WAF_SQLI_HEX_LITERAL_RE.search("0x1a2"))
        self.assertIsNotNone(WAF_SQLI_HEX_LITERAL_RE.search("0X1a2"))

    def test_uppercase_x_is_defanged_and_its_case_kept(self):
        """The gateway blocks "0X1a2" just as readily as "0x1a2"."""
        form = {"__VIEWSTATE": "0X1a2"}

        self.assertEqual(
            breakup_hex_substrings(form)["__VIEWSTATE"], "0\nX1a2"
        )


if __name__ == "__main__":
    unittest.main()
