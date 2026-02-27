"""Scraper for Board of Veterans' Appeals
CourtID: bva
Court Short Name: BVA
Type: Nonprecedential
History:
    2014-09-09: Created by Jon Andersen
    2016-05-14: Updated by arderyp
    2026-02-24: Rewritten by grossir to use VA sitemap after old
                endpoint (index.va.gov) was taken down. See #873

The VA publishes all BVA decisions as plain text files, indexed via
per-year XML sitemaps at https://www.va.gov/vetapp{YY}/sitemap.xml
(e.g. vetapp25 for 2025, vetapp92 for 1992).

Each .txt file starts with a structured header:
    Citation Nr: 25000001
    Decision Date: 01/01/25    Archive Date: 12/11/24

    DOCKET NO. 16-36 738

The sitemaps and the .txt files are served with chunked
transfer-encoding and no Accept-Ranges header, so HTTP range
requests are not supported for either resource.  We must download
each file in full.

Sitemap entries are ordered chronologically: new decisions are
appended at the end.  The regular scraper exploits this by
processing only the tail of the current year's sitemap; the
backscraper iterates over all years (1992-present).
"""

import os
import re
from datetime import datetime

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # Sitemaps available from 1992 to present
    first_opinion_date = datetime(1992, 1, 1)
    days_interval = 365

    # check the latest 50 cases on a regular scrape
    # the upload schedule and volume is unknown, so we will have to run a
    # periodic backscraper for the active year
    # limiting cases helps prevent hitting the servers too hard and helps the
    # scraper exit fast enough. Even when the files are small, the servers
    # are slow
    cases_to_scrape = 50

    sitemap_url = "https://www.va.gov/vetapp{yy:02d}/sitemap.xml"

    # Some older decisions (pre-1997) lack a DOCKET NO. line.
    citation_re = re.compile(r"Citation Nr:\s*(\S+)")
    date_re = re.compile(r"Decision Date:\s*(\S+)")
    docket_re = re.compile(r"DOCKET NO\.\s*(.+)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

        self.status = "Unpublished"
        self.expected_content_types = ["text/plain"]

        current_yy = datetime.today().year % 100
        self.url = self.sitemap_url.format(yy=current_yy)
        self.is_backscrape = False
        # supressing the save_response_fn, since the downloaded sitemaps are
        # very big 15-20MB and would fill the CL S3 response bucket
        self.save_response = None

    async def _download(self, request_dict=None):
        """Fall back to the previous year's sitemap if the current
        year's does not exist yet. Do not do this in a backscrape
        """
        if self.test_mode_enabled() or self.is_backscrape:
            return await super()._download(request_dict)

        # Uses a HEAD request (headers only, no body) to cheaply check
        # existence before committing to a full GET of the ~18 MB XML.
        r = self.request["session"].head(self.url, timeout=10)
        if r.status_code == 404:
            # Current year's sitemap doesn't exist yet;
            # try the previous year
            prev_yy = (datetime.today().year - 1) % 100
            self.url = self.sitemap_url.format(yy=prev_yy)
            logger.info(
                "Current year sitemap not found, falling back to %s",
                self.url,
            )

        return super()._download(request_dict)

    async def _process_html(self) -> None:
        """Parse the sitemap XML and fetch individual decisions.

        Sitemap entries are appended chronologically, so the newest
        decisions are at the end.  For regular runs we only process
        the last `self.cases_to_scrape` entries to keep runtime reasonable.
        """
        # lxml's HTML parser can handle the sitemap XML; namespace
        # prefixes are stripped so //loc works directly
        locs = self.html.xpath("//loc/text()")

        for loc in reversed(locs):
            if len(self.cases) >= self.cases_to_scrape:
                logger.info("Reached case limit")
                break

            await self._fetch_and_parse_decision(loc)

    async def _fetch_and_parse_decision(self, url: str) -> None:
        """Download a single .txt decision and extract metadata.

        Uses download_content to fetch the file.  In test mode,
        resolves the URL relative to the example file's directory
        (same pattern as texapp.py for sub-example pages).

        :param url: Full URL to the .txt file, or a relative path
            in test mode
        """

        if self.test_mode_enabled() and "http" in url:
            # there is a single example with a valid sub example
            self.cases.append(
                {
                    "name": "Placeholder",
                    "url": url,
                    "date": "2025/02/24",
                    "docket": "Placeholder",
                    "citation": "Placeholder",
                    "content": "Placeholder",
                }
            )
            return

        # BVA .txt files use Windows-1252 encoding for special
        # characters like § (section sign).  download_content
        # returns bytes; we decode after.
        download_kwargs = {"doctor_is_available": False}
        if self.test_mode_enabled():
            download_kwargs["media_root"] = os.path.dirname(self.mock_url)
        raw = await self.download_content(url, **download_kwargs)

        content = raw.decode("cp1252")

        citation_match = self.citation_re.search(content)
        date_match = self.date_re.search(content)

        if not citation_match or not date_match:
            logger.warning("Could not parse header from %s", url)
            return

        citation = citation_match.group(1)
        date_str = date_match.group(1)
        docket_match = self.docket_re.search(content)
        docket = docket_match.group(1).strip() if docket_match else ""

        self.cases.append(
            {
                # BVA decisions use the docket as the case name
                # because veterans' names are not published
                "name": docket or citation,
                "url": url,
                "date": date_str,
                "docket": docket,
                "citation": citation,
                "content": content,
            }
        )

    async def _download_backwards(self, yy: int) -> None:
        """Download and process all decisions from a given year's sitemap.

        Called once per year by the backscrape caller.

        :param yy: 2-digit year (e.g. 92 for 1992, 25 for 2025)
        """
        self.url = self.sitemap_url.format(yy=yy)
        logger.info("Backscraping year %02d from %s", yy, self.url)
        self.is_backscrape = True

        # Process all entries for a backscrape
        self.cases_to_scrape = 1_000_000
        self.html = await self._download()
        await self._process_html()

    def make_backscrape_iterable(self, kwargs):
        """Convert the parent's date-range tuples into 2-digit year ints.

        The parent creates (start_date, end_date) tuples based on
        days_interval.  We only need the year boundaries, since
        _download_backwards operates on one year's sitemap at a time.
        """
        super().make_backscrape_iterable(kwargs)

        # back_scrape_iterable is a list of (start, end) date tuples
        start_year = self.back_scrape_iterable[0][0].year
        end_year = self.back_scrape_iterable[-1][-1].year

        self.back_scrape_iterable = [
            y % 100 for y in range(start_year, end_year + 1)
        ]
