"""Washington metadata from original source HTML, not synthetic transcripts."""

import re
import unittest
from pathlib import Path

from lxml import html

from juriscraper.opinions.united_states.attorney_general.washag import Site

FIXTURES = (
    Path(__file__).parents[1]
    / "examples/opinions/united_states/washag_metadata"
)


class WashingtonMetadataTest(unittest.TestCase):
    def test_original_minified_and_cleaned(self):
        expected = {
            "modern": (
                "Nick Brown",
                "1. If a county’s health benefit plan",
                "prohibited.",
            ),
            "1949": (
                "Smith Troy",
                "An officer appointed by the State",
                "parole violation.",
            ),
            "2011": (
                "Rob McKenna",
                "Cities, counties, and special districts",
                "to do so.",
            ),
            "aglo": ("Slade Gorton", None, None),
            "1975": (
                "Slade Gorton",
                "(1) Neither the superintendent",
                "noncomplying school districts.",
            ),
        }
        for name, (judge, start, end) in expected.items():
            original = (FIXTURES / f"washag-{name}.html").read_bytes()
            for content in (
                original.decode(),
                re.sub(r">\s+<", "><", original.decode()),
                Site.cleanup_content(original).decode(),
            ):
                with self.subTest(name=name, minified="\n" not in content):
                    result = Site().extract_from_text(content)[
                        "OpinionCluster"
                    ]
                    self.assertEqual(
                        result["judges"], f"Attorney General {judge}"
                    )
                    if start:
                        self.assertTrue(result["summary"].startswith(start))
                        self.assertTrue(result["summary"].endswith(end))
                        self.assertNotIn("Dear ", result["summary"])
                        self.assertNotIn("Cite As", result["summary"])
                    else:
                        self.assertNotIn("summary", result)

    def test_cleanup_retains_opinion_and_removes_navigation(self):
        original = (FIXTURES / "washag-modern.html").read_bytes()
        cleaned = Site.cleanup_content(original)
        tree = html.fromstring(cleaned)
        self.assertEqual(tree.get("id"), "block-atg-content")
        self.assertIn("Dear Prosecutor Sant", tree.text_content())
        self.assertFalse(tree.xpath("//header | //footer | //nav"))

    def test_missing_content_is_not_guessed(self):
        for text in ("", "plain text", "<p>Attorney General Somebody</p>"):
            self.assertEqual(Site().extract_from_text(text), {})
        with self.assertRaises(ValueError):
            Site.cleanup_content(b"<p>Not an opinion</p>")

    def test_missing_date_does_not_swallow_body_into_summary(self):
        original = (FIXTURES / "washag-modern.html").read_text()
        original = original.replace("April 9, 2025", "Date unavailable")
        result = Site().extract_from_text(original)["OpinionCluster"]
        self.assertNotIn("summary", result)
