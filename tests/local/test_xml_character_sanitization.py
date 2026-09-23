#!/usr/bin/env python
"""Tests for XML character sanitization in PACER parsers.

This addresses Issue #348: Invalid XML characters break docket parsers.
"""

import unittest

from lxml.etree import XMLSyntaxError
from lxml.html import fromstring

from juriscraper.lib.html_utils import clean_html, strip_bad_html_tags_insecure


class XmlCharacterSanitizationTest(unittest.TestCase):
    """Test that invalid XML characters are properly handled."""

    def test_escape_character_in_html(self):
        """Test that ESC character (\x1b) is removed from HTML."""
        # This is the problematic character from Issue #348
        html_with_esc = "<html><body><p>Test\x1bString</p></body></html>"

        # clean_html should remove the invalid character
        cleaned = clean_html(html_with_esc)
        self.assertNotIn("\x1b", cleaned)
        self.assertIn("TestString", cleaned)

        # Should be parseable without error
        try:
            tree = fromstring(cleaned)
            text = tree.text_content()
            self.assertIn("TestString", text)
        except XMLSyntaxError:
            self.fail("XMLSyntaxError raised even after cleaning")

    def test_various_invalid_xml_characters(self):
        """Test that various invalid XML characters are removed."""
        invalid_chars = [
            ("\x00", "NULL"),
            ("\x01", "SOH"),
            ("\x02", "STX"),
            ("\x08", "BS"),
            ("\x0b", "VT"),
            ("\x0c", "FF"),
            ("\x0e", "SO"),
            ("\x1b", "ESC"),
            ("\x1f", "US"),
        ]

        for char, name in invalid_chars:
            with self.subTest(char=name):
                html = f"<html><body><p>Before{char}After</p></body></html>"
                cleaned = clean_html(html)
                self.assertNotIn(
                    char, cleaned, f"{name} character should be removed"
                )
                self.assertIn("BeforeAfter", cleaned)

    def test_valid_xml_characters_preserved(self):
        """Test that valid XML characters are preserved."""
        # Tab, newline, and carriage return are valid
        html = "<html><body><p>Line1\tTab\nLine2\rLine3</p></body></html>"
        cleaned = clean_html(html)
        self.assertIn("\t", cleaned)
        self.assertIn("\n", cleaned)
        self.assertIn("\r", cleaned)

    def test_strip_bad_html_tags_with_invalid_chars(self):
        """Test that strip_bad_html_tags_insecure handles invalid chars."""
        html_with_esc = "<html><body><p>Test\x1bString</p></body></html>"

        # First clean, then strip bad tags
        cleaned = clean_html(html_with_esc)

        try:
            tree = strip_bad_html_tags_insecure(cleaned)
            text = tree.text_content()
            self.assertIn("TestString", text)
            self.assertNotIn("\x1b", text)
        except XMLSyntaxError:
            self.fail("XMLSyntaxError raised in strip_bad_html_tags_insecure")

    def test_html_entities_for_invalid_chars(self):
        """Test that HTML entities for invalid chars are removed."""
        # Some systems might encode invalid chars as HTML entities
        html_with_entity = "<html><body><p>Test&#27;String</p></body></html>"
        cleaned = clean_html(html_with_entity)

        # The entity should be removed
        self.assertNotIn("&#27;", cleaned)
        self.assertNotIn("\x1b", cleaned)

        # Should be parseable
        try:
            tree = fromstring(cleaned)
            text = tree.text_content()
            self.assertIn("TestString", text)
        except XMLSyntaxError:
            self.fail("XMLSyntaxError raised with HTML entity")

    def test_real_world_docket_text(self):
        """Test with a more realistic docket entry containing invalid chars."""
        # Simulate a docket entry that might have escape sequences
        html = """
        <html>
        <body>
        <table>
            <tr>
                <td>01/15/2020</td>
                <td>MOTION for Summary Judgment by \x1bDefendant</td>
            </tr>
        </table>
        </body>
        </html>
        """

        cleaned = clean_html(html)
        self.assertNotIn("\x1b", cleaned)

        try:
            tree = fromstring(cleaned)
            text = tree.text_content()
            self.assertIn("Defendant", text)
        except XMLSyntaxError:
            self.fail("XMLSyntaxError raised with docket-like HTML")


if __name__ == "__main__":
    unittest.main()
