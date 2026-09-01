#!/usr/bin/env python
"""Covers the paginated download of the Florida opinion scrapers.

The flcourts-media search endpoint caps a page at 50 results and reports the
size of the whole set in `totalCount`. See #2150.
"""

import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from juriscraper.opinions.united_states.state import fla, fladistctapp_6

# Enough to need two pages at a page size of 50
TOTAL_COUNT = 51


def make_result(case_number: str) -> dict:
    """Build the part of a search result the scraper reads

    :param case_number: identifies the row
    :return: a search result
    """
    return {
        "content": {
            "id": 1,
            "fields": {
                "case_number": case_number,
                "case_style": f"Doe v. State {case_number}",
                "disposition": "affirmed",
                "note": "",
                "opinion": {"uri": f"/content/download/{case_number}.pdf"},
                "disposition_date": {
                    "date": {"date": "2026-08-25 00:00:00.000000"}
                },
            },
        }
    }


class FakeSource:
    """Answers each request with the slice of results its offset asks for"""

    def __init__(self, total: int = TOTAL_COUNT, page_size: int = 50):
        self.total = total
        self.page_size = page_size
        self.offsets = []

    async def __call__(self, site, request_dict=None):
        query = parse_qs(urlparse(site.url).query)
        offset = int(query["offset"][0])
        limit = int(query["limit"][0])
        self.offsets.append(offset)

        results = [
            make_result(f"2026-{index:04d}")
            for index in range(offset, min(offset + limit, self.total))
        ]
        return {"searchResults": results, "totalCount": self.total}


def patch_downloader(source: FakeSource):
    """Replace the single page downloader the Florida scraper builds on

    :param source: answers the requests
    :return: the patcher, ready to use as a context manager
    """

    async def download(self, request_dict=None):
        return await source(self, request_dict)

    return patch(
        "juriscraper.OpinionSiteLinear.OpinionSiteLinear._download",
        download,
    )


class FloridaPaginationTest(unittest.IsolatedAsyncioTestCase):
    async def test_follows_the_offset_until_the_set_is_complete(self):
        """A 51 result day needs a second page, and must not lose the tail"""
        source = FakeSource()
        site = fla.Site()

        with patch_downloader(source):
            html = await site._download()

        self.assertEqual(source.offsets, [0, 50])
        self.assertEqual(len(html["searchResults"]), TOTAL_COUNT)

    async def test_a_single_page_makes_no_extra_request(self):
        """The common case stays one request"""
        source = FakeSource(total=12)
        site = fla.Site()

        with patch_downloader(source):
            html = await site._download()

        self.assertEqual(source.offsets, [0])
        self.assertEqual(len(html["searchResults"]), 12)

    async def test_every_result_is_parsed(self):
        """The extra pages reach the scraped output, not just the raw html"""
        source = FakeSource()
        site = fladistctapp_6.Site()

        with patch_downloader(source):
            site.html = await site._download()
        site._process_html()

        self.assertEqual(len(site.cases), TOTAL_COUNT)
        # the row that sat beyond the 50 result cap, and was being dropped
        self.assertIn("6D2026-0050", [case["docket"] for case in site.cases])

    async def test_a_runaway_total_count_stops_and_complains(self):
        """A `totalCount` the source cannot deliver must not spin forever"""
        source = FakeSource(total=100_000)
        site = fla.Site()

        with patch_downloader(source), self.assertLogs(level="ERROR") as logs:
            html = await site._download()

        self.assertEqual(len(source.offsets), site.max_pages)
        self.assertEqual(
            len(html["searchResults"]), site.max_pages * site.page_size
        )
        self.assertIn("was not scraped", "".join(logs.output))

    async def test_an_empty_page_stops_and_complains(self):
        """A source that stops answering must not loop on the same offset"""
        source = FakeSource(total=200, page_size=50)
        site = fla.Site()

        # the source claims 200 results but runs dry after the first page
        source.total = 200

        async def one_page_then_empty(site_arg, request_dict=None):
            query = parse_qs(urlparse(site_arg.url).query)
            offset = int(query["offset"][0])
            source.offsets.append(offset)
            results = (
                [make_result(f"2026-{index:04d}") for index in range(50)]
                if offset == 0
                else []
            )
            return {"searchResults": results, "totalCount": 200}

        with (
            patch(
                "juriscraper.OpinionSiteLinear.OpinionSiteLinear._download",
                one_page_then_empty,
            ),
            self.assertLogs(level="ERROR") as logs,
        ):
            html = await site._download()

        self.assertEqual(source.offsets, [0, 50])
        self.assertEqual(len(html["searchResults"]), 50)
        self.assertIn("came back empty", "".join(logs.output))

    def test_the_regular_window_is_short_enough_to_paginate(self):
        """A year long window was always truncated to its newest page"""
        site = fla.Site()
        query = parse_qs(urlparse(site.url).query)

        self.assertEqual(int(query["limit"][0]), site.page_size)
        self.assertEqual(int(query["offset"][0]), 0)
        self.assertEqual((site.end_date - site.start_date).days, 15)


if __name__ == "__main__":
    unittest.main()
