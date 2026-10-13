"""Scraper for Supreme Court of Maine
CourtID: me
Court Short Name: Me.
Author: Brian W. Carver
Date created: June 20, 2014

History:
  2014-06-25 (est): Added code for additional date formats.
  2014-07-02: Was receiving InsanityException and tweaked date code to get some
              missing dates.
  2014-12-15: Fixes insanity exception by tweaking the XPaths.

  2022-01-06: This scraper is not maintained. Future work to gather this
              data should be done by scraping the CourtListener API
              https://www.courtlistener.com/api/rest/v3/clusters/?docket__court__id=me

  2025-03-31: This scraper has been updated with a backscraper (flooie)
"""

import re
from datetime import date

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.judge_parsers import normalize_judge_names
from juriscraper.lib.string_utils import (
    CaseNameTweaker,
    convert_date_string,
    titlecase,
)
from juriscraper.lib.type_utils import BackscrapeOptions, ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[int]):
    url_template = (
        "https://www.courts.maine.gov/courts/sjc/lawcourt/{}/index.html"
    )
    first_opinion_year = 2017

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.maine.gov/courts/sjc/opinions.html"
        self.path_root = '//table[contains(.//th[1], "Opinion")]//tr[td]'
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(self.path_root)
        for row in rows:
            cite, name, date = row.findall("./td")

            # handle the one typo
            date_str = date.text_content().replace("Aguust", "August")

            case_name = titlecase(name.text_content())
            if "Revised" in case_name:
                # handle revised opinions case name
                case_name = case_name.split("Revised")[0].strip()
            self.cases.append(
                {
                    "citation": cite.text_content(),
                    "date": date_str,
                    "name": case_name,
                    "url": name.findall(".//a")[0].attrib["href"],
                    "docket": "",
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract out lots of data from Maine

        :param scraped_text: The first page of content
        :return: The dictionary of extracted data
        """
        pattern = re.compile(
            r"(?P<label>Docket|On Briefs|Decided|Argued|Panel|Reporter of Decisions):\s*(?P<value>[^\n]+)"
        )
        extracted = {}
        for match in pattern.finditer(scraped_text[:500]):
            label = match.group("label")
            value = match.group("value").strip()
            extracted[label] = value

        author = r"(?P<author_str>.*)\n+(\s+)?\[¶1\]"
        m = re.search(author, scraped_text, re.MULTILINE)
        if m is not None:
            if m.group("author_str") == "PER CURIAM":
                per_curiam = True
                author_str = ""
            else:
                per_curiam = False
                author_str = m.group("author_str")
        else:
            per_curiam = False
            author_str = ""

        date_argued = (
            On_Briefs_value
            if bool(On_Briefs_value := extracted.get("On Briefs", ""))
            else extracted.get("Argued", "")
        )
        date_argued_str = ""
        if bool(date_argued):
            # Format date
            date_argued = convert_date_string(date_argued)
            if date_argued is None:
                raise ValueError("An argument date is required")
            date_argued_str = date_argued.strftime("%Y-%m-%d")

        metadata: ExtractedMetadata = {
            "Opinion": {
                "author_str": normalize_judge_names(author_str),
                "per_curiam": per_curiam,
            },
            "OpinionCluster": {
                "judges": extracted.get("Panel", ""),
            },
            "Docket": {
                "date_argued": date_argued_str,
                "docket_number": extracted.get("Docket", ""),
            },
        }

        return metadata

    @override
    async def _download_backwards(self, year: int) -> None:
        self.url = self.url_template.format(year)
        logger.info("Backscraping for year %s %s", year, self.url)
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        if bool(kwargs.get("backscrape_start")):
            start = int(kwargs["backscrape_start"])
        else:
            start = self.first_opinion_year

        if bool(kwargs.get("backscrape_end")):
            end = int(kwargs["backscrape_end"])
        else:
            end = date.today().year - 1

        if start == end:
            end = start + 1

        self.back_scrape_iterable = range(start, end)
