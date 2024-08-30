# Author: Phil Ardery
# Date created: 2017-01-27
# Contact: 501-682-9400 (Administrative Office of the Curt)

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import normalize_dashes, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://opinions.arcourts.gov/ark/en/d/s/index.do"
    court_code = "144"
    cite_regex = re.compile(r"\d{2,4} Ark\. \d+", re.IGNORECASE)
    first_opinion_date = datetime(1979, 9, 3)
    days_interval = 7
    not_a_opinion_regex = r"SYLLABUS|(NO (COURT OF APPEALS )?OPINION)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        XMLHttpRequest pagination is triggered every 25 rows, so we must
        try to avoid big date intervals

        :return None
        """
        rows = self.html.xpath("//div[@class='info']")
        if len(rows) >= 25:
            logger.info(
                "25 results for this query, results may be lost in pagination"
            )

        for item in rows:
            per_curiam = False

            name = item.xpath(".//a/text()")[0]
            url = item.xpath(".//a/@href")[1]
            if re.search(self.not_a_opinion_regex, name.upper()):
                logger.info("Skipping %s %s, invalid document", name, url)
                continue

            cite = item.xpath(".//*[@class='citation']/text()")
            if cite:
                cite = cite[0]

            if metadata := item.xpath(".//*[@class='subMetadata']/span[2]"):
                per_curiam = metadata[0].text_content().strip() == "Per Curiam"

            date_filed = item.xpath(".//*[@class='publicationDate']/text()")[0]
            self.cases.append(
                {
                    "date": date_filed,
                    "docket": "",
                    "name": titlecase(name),
                    "citation": cite,
                    "url": url,
                    "status": "Published",
                    "per_curiam": per_curiam,
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Formats and sets `self.url` with date inputs

        If no start or end dates are given, scrape last 7 days.

        :param start: start date
        :param end: end date

        :return None
        """
        if not start:
            end = datetime.now() + timedelta(1)
            start = end - timedelta(7)

        params = {
            "cont": "",
            "ref": "",
            "d1": start.strftime("%m/%d/%Y"),
            "d2": end.strftime("%m/%d/%Y"),
            "col": self.court_code,
            "tf1": "",
            "tf2": "",
            "or": "date",
            "iframe": "true",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        normalized_content = normalize_dashes(scraped_text)
        match = re.findall(r"No\. (\w+-\d+-\d+)", normalized_content)
        if match:
            return {"OpinionCluster": {"docket_number": match[0]}}
        return {}

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()
