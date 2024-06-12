"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by WEP
    - 2023-11-19: Drop Selenium by WEP
    - 2023-12-20: Updated with citations, judges and summaries, Palin
"""

import datetime
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from dateutil import parser

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = date(2009, 1, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.courts.state.co.us/Courts/Supreme_Court/Proceedings/Index.cfm"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        :return: None
        """
        for row in self.html.xpath("//div[@id='Dispositions']/a"):
            case_id = row.attrib["onclick"].split("'")[1]
            div = row.xpath(f"//div[@id='Case_{case_id}']")[0]
            if not div.xpath(".//a/text()"):
                # This is set to avoid data decades back
                continue

            document_type = div.xpath(".//a/text()")[0]
            if "Opinion" not in document_type:
                logger.info(
                    "%s is a %s, not a opinion. Skipping",
                    case_id,
                    document_type,
                )
                continue

            summary = (
                row.xpath(f"//div[@id='Case_{case_id}']")[0]
                .text_content()
                .strip()
            )

            date_filed_str = self.find_date(summary)
            date_filed = parser.parse(date_filed_str)

            # Proper place for this would be the `set_date_range`
            # function, but enable_test_mode is ran after init
            if self.test_mode_enabled():
                self.end_date = datetime(2023, 11, 19)
                self.start_date = self.end_date - timedelta(days=180)

            if date_filed < self.start_date or date_filed > self.end_date:
                logger.info(
                    "Opinion date %s is out of scrape range. Skipping",
                    date_filed,
                )
                continue

            url = div.xpath(".//a/@href")[0]

            title = row.xpath("following-sibling::text()")[0].strip()
            docket, name = title.split(" ", 1)
            name, _ = name.split("  ")
            if "(Honorable" in name:
                name, judge = name.split("(")
                name = name.strip()
                judges = judge.strip(")").strip().replace("Honorable", "")
            else:
                logger.info("No judge name could be extracted from %s", name)
                judges = ""

            if "https://www.courts.state.co.us/" not in url:
                url = f"https://www.courts.state.co.us/{url}"

            self.cases.append(
                {
                    "summary": summary,
                    "date": date_filed_str,
                    "name": name,
                    "docket": docket.strip(","),
                    "url": url,
                    "judge": judges,
                }
            )

    def set_date_range(
        self, start: Optional[date] = None, end: Optional[date] = None
    ):
        """Set date range to scrape opinions

        Default behaviour is to scrape between today and six months ago
        Backscrape behaviour will depend on the input

        """
        if start:
            self.start_date = start
            self.end_date = end
        else:
            self.end_date = datetime.today()
            self.start_date = self.end_date - timedelta(days=180)

    def find_date(self, summary: str) -> str:
        """Find date filed

        Normally it follows a typical pattern but not always

        :param summary: Use summary text to find date filed
        :return: date as string
        """
        if "Opinion issued" in summary:
            return summary.split("Opinion issued")[1]
        date_pattern = re.compile(
            r"((January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s?,?\s+(\d{4}))"
        )
        match = re.findall(date_pattern, summary)
        date_filed = match[-1][0] if match else ""
        return date_filed

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extract Citation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        m = re.findall(r"(20\d{2})\s(CO)\s(\d+A?)", scraped_text)
        if not m:
            return {}

        vol, reporter, page = m[0]
        return {
            "Citation": {
                "volume": vol,
                "reporter": reporter,
                "page": page,
                "type": 8,  # NEUTRAL in courtlistener Citation model
            },
        }

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly
        :param kwargs: passed when initializing the scraper, may or
        may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = [(start, end)]

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Set date range from backscraping args and scrape

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_date_range(*dates)
        logger.info("Backscraping for range %s %s", *dates)
        self.html = self._download()
        self._process_html()
