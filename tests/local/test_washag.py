"""Regression tests using unmodified Washington AG year-index responses."""

import unittest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock

from lxml import html

from juriscraper.lib.exceptions import ParsingException
from juriscraper.opinions.united_states.attorney_general.washag import Site

EXAMPLES = Path(__file__).parents[1] / "examples/opinions/united_states"


def fixture(name):
    return html.fromstring((EXAMPLES / name).read_bytes())


class WashingtonIndexTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.site = Site()
        self.site.today = date(2026, 11, 14)

    async def asyncTearDown(self):
        await self.site.__aexit__(None, None, None)

    def test_current_year_exact_dates_and_titles(self):
        tree = fixture("washag_example.html")
        self.site._read_rows(tree)
        self.assertEqual(len(self.site.cases), 2)
        case = self.site.cases[0]
        self.assertEqual(case["docket"], "AGO 2026 No. 1")
        self.assertEqual(case["date"], "2026-02-25")
        self.assertEqual(
            case["name"], "Washington Attorney General Opinion AGO 2026 No. 1"
        )
        title = tree.xpath('//div[contains(@class,"views-field-title")]//a')[0]
        self.assertEqual(
            case["summary"], " ".join(title.text_content().split())
        )
        self.assertTrue(
            case["url"].startswith("https://www.atg.wa.gov/ago-opinions/")
        )

    def test_letter_and_formal_series_are_distinct(self):
        self.site._read_rows(fixture("washag_example_1975.html"))
        cases = {case["docket"]: case for case in self.site.cases}
        self.assertEqual(len(cases), 10)
        self.assertIn("AGO 1975 No. 1", cases)
        self.assertIn("AGLO 1975 No. 1", cases)
        self.assertNotEqual(
            cases["AGO 1975 No. 1"]["url"], cases["AGLO 1975 No. 1"]["url"]
        )
        self.assertEqual(cases["AGLO 1975 No. 1"]["summary"], "")

    def test_duplicate_docket_retains_both_source_records(self):
        self.site._read_rows(fixture("washag_pagination/1951-23.html"))
        duplicates = [
            case
            for case in self.site.cases
            if case["docket"] == "AGO 1951 No. 446"
        ]
        self.assertEqual(len(self.site.cases), 10)
        self.assertEqual(len(duplicates), 2)
        self.assertEqual({case["date"] for case in duplicates}, {"1951-02-09"})
        self.assertEqual(len({case["url"] for case in duplicates}), 2)

    def test_historical_header_with_date_before_year(self):
        # The series-specific indexes include the month/day before the year.
        tree = fixture("washag_example_1975.html")
        header = tree.xpath(
            '//div[contains(@class,"views-field-field-opinion-date")]/div'
        )[0]
        header.text = "AGO Jan 8 1975 NO. 1 > "
        self.site._read_rows(tree)
        self.assertEqual(self.site.cases[0]["docket"], "AGO 1975 No. 1")

    def test_missing_exact_date_fails_loudly(self):
        tree = fixture("washag_example.html")
        tree.xpath("//time")[0].attrib.pop("datetime")
        with self.assertRaises(ParsingException):
            self.site._read_rows(tree)

    def test_inconsistent_year_fails_loudly(self):
        tree = fixture("washag_example.html")
        tree.xpath("//time")[0].set("datetime", "2025-02-25T12:00:00Z")
        with self.assertRaises(ParsingException):
            self.site._read_rows(tree)

    def test_no_next_link_on_last_page(self):
        self.assertIsNone(
            self.site._next_url(
                fixture("washag_pagination/1975-12.html"),
                self.site._year_url(1975) + "?page=12",
            )
        )

    def test_follows_next_not_last_page_link(self):
        self.assertEqual(
            self.site._next_url(
                fixture("washag_example_1975.html"), self.site._year_url(1975)
            ),
            self.site._year_url(1975) + "?page=1",
        )
        self.assertEqual(
            self.site._next_url(
                fixture("washag_pagination/1975-1.html"),
                self.site._year_url(1975) + "?page=1",
            ),
            self.site._year_url(1975) + "?page=2",
        )

    def test_bad_next_links_rejected(self):
        for target in (
            "?page=0",
            "?page=2",
            "?page=abc",
            "?page=1&page=2",
            "https://example.org/?page=1",
            "/ago-opinions/year/1976?page=1",
        ):
            with self.subTest(target=target):
                tree = fixture("washag_example_1975.html")
                tree.xpath('//a[@rel="next"]')[0].set("href", target)
                with self.assertRaises(ParsingException):
                    self.site._next_url(tree, self.site._year_url(1975))

    async def test_pagination_downloads_and_processes_next_page(self):
        self.site.url = self.site._year_url(1975)
        self.site.html = fixture("washag_example_1975.html")
        second = fixture("washag_pagination/1975-1.html")
        # Stop the mocked two-page sequence without altering fixture bytes.
        second.xpath('//a[@rel="next"]')[0].drop_tree()
        self.site._get_html_tree_by_url = AsyncMock(return_value=second)
        await self.site._process_html()
        self.site._get_html_tree_by_url.assert_awaited_once_with(
            self.site.url + "?page=1"
        )
        self.assertEqual(len(self.site.cases), 20)
        self.assertEqual(len({case["url"] for case in self.site.cases}), 20)
        self.assertIn(
            "AGLO 1975 No. 10", {case["docket"] for case in self.site.cases}
        )

    async def test_january_also_checks_previous_year(self):
        self.site.today = date(2027, 1, 5)
        self.site.url = self.site._year_url(2027)
        self.site.html = html.fromstring("<html><body></body></html>")
        self.site._get_html_tree_by_url = AsyncMock(
            return_value=fixture("washag_example.html")
        )
        await self.site._process_html()
        self.site._get_html_tree_by_url.assert_awaited_once_with(
            self.site._year_url(2026)
        )
        self.assertEqual(len(self.site.cases), 2)

    async def test_non_january_does_not_fetch_previous_year(self):
        self.site.html = fixture("washag_example.html")
        self.site._get_html_tree_by_url = AsyncMock()
        await self.site._process_html()
        self.site._get_html_tree_by_url.assert_not_awaited()

    async def test_backscrape_does_not_apply_january_rollover(self):
        self.site.today = date(2027, 1, 5)
        await self.site._download_backwards(2026)
        self.site.html = fixture("washag_example.html")
        self.site._get_html_tree_by_url = AsyncMock()
        await self.site._process_html()
        self.site._get_html_tree_by_url.assert_not_awaited()
        self.assertEqual(self.site.url, self.site._year_url(2026))
        self.assertEqual(len(self.site.cases), 2)

    def test_default_backscrape_skips_columbia_overlap(self):
        years = self.site.back_scrape_iterable
        self.assertIn(1949, years)
        self.assertIn(1995, years)
        self.assertIn(2012, years)
        self.assertFalse(set(range(1996, 2012)).intersection(years))

    def test_missing_or_offsite_opinion_link_fails_loudly(self):
        for href in (
            None,
            "https://example.org/ago-opinions/test",
            "/contact",
        ):
            with self.subTest(href=href):
                tree = fixture("washag_example.html")
                link = tree.xpath(
                    '//div[contains(@class,"views-field-title")]//a'
                )[0]
                if href is None:
                    link.attrib.pop("href")
                else:
                    link.set("href", href)
                with self.assertRaises(ParsingException):
                    self.site._read_rows(tree)

    async def test_repeated_page_content_fails_loudly(self):
        self.site.url = self.site._year_url(1975)
        self.site.html = fixture("washag_example_1975.html")
        self.site._get_html_tree_by_url = AsyncMock(
            return_value=fixture("washag_example_1975.html")
        )
        with self.assertRaisesRegex(ParsingException, "repeated"):
            await self.site._process_html()
        self.site._get_html_tree_by_url.assert_awaited_once()

    async def test_local_examples_never_fetch_pagination(self):
        self.site.enable_test_mode()
        self.site.url = self.site._year_url(1975)
        self.site.html = fixture("washag_example_1975.html")
        self.site._get_html_tree_by_url = AsyncMock()
        await self.site._process_html()
        self.site._get_html_tree_by_url.assert_not_awaited()
        self.assertEqual(len(self.site.cases), 10)

    async def test_january_previous_year_repeated_page_fails_loudly(self):
        self.site.today = date(1976, 1, 5)
        self.site.url = self.site._year_url(1976)
        self.site.html = html.fromstring("<html><body></body></html>")
        self.site._get_html_tree_by_url = AsyncMock(
            side_effect=[
                fixture("washag_example_1975.html"),
                fixture("washag_example_1975.html"),
            ]
        )
        with self.assertRaisesRegex(ParsingException, "repeated"):
            await self.site._process_html()
        self.assertEqual(
            [
                call.args[0]
                for call in self.site._get_html_tree_by_url.await_args_list
            ],
            [self.site._year_url(1975), self.site._year_url(1975) + "?page=1"],
        )
        self.assertEqual(len(self.site.cases), 10)
