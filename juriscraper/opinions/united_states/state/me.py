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

from juriscraper.AbstractSite import logger
from juriscraper.lib.judge_parsers import normalize_judge_names
from juriscraper.lib.string_utils import convert_date_string, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    url_template = (
        "https://www.courts.maine.gov/courts/sjc/lawcourt/{}/index.html"
    )
    first_opinion_year = 2017

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.maine.gov/courts/sjc/opinions.html"
        self.path_root = '//table[contains(.//th[1], "Opinion")]//tr[td]'
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for row in self.html.xpath(self.path_root):
            cite, name, date = row.xpath("./td")

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
                    "url": name.xpath(".//a")[0].attrib["href"],
                    "docket": "",
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
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
        if m:
            if m.group("author_str") == "PER CURIAM":
                per_curiam = True
                author_str = ""
            else:
                per_curiam = False
                author_str = m.group("author_str")
        else:
            per_curiam = False
            author_str = ""

        date_argued = extracted.get("On Briefs", "") or extracted.get(
            "Argued", ""
        )
        date_argued_str = ""
        if date_argued:
            # Format date
            date_argued = convert_date_string(date_argued)
            date_argued_str = date_argued.strftime("%Y-%m-%d")

        metadata = {
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

    def _download_backwards(self, year: int) -> None:
        self.url = self.url_template.format(year)
        logger.info("Backscraping for year %s %s", year, self.url)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict):
        if kwargs.get("backscrape_start"):
            start = int(kwargs["backscrape_start"])
        else:
            start = self.first_opinion_year

        if kwargs.get("backscrape_end"):
            end = int(kwargs["backscrape_end"])
        else:
            end = date.today().year - 1

        if start == end:
            end = start + 1

        self.back_scrape_iterable = range(start, end)
