"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig <asadullahbeg@outlook.com>
History:
    - 2014-07-11: created
    - 2014-08-08, mlr: updated to fix InsanityError on case_dates
    - 2014-09-18, mlr: updated XPath to fix InsanityError on docket_numbers
    - 2015-06-17, mlr: made it more lenient about date formatting
    - 2016-07-21, arderyp: fixed to handle altered site format
    - 2017-01-10, arderyp: restructured to handle new format use case that includes opinions without dates and flagged for 'future' publication
    - 2022-02-02, satsuki-chan: Fixed docket and name separator, changed super class to OpinionSiteLinear
    - 2023-11-04, flooie: Fix scraper
"""

import re
from datetime import date
from typing import Tuple

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_abbv = "sup"
    start_year = 2000
    base_url = "http://www.jud.ct.gov/external/supapp/archiveARO{}{}.htm"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

        self.current_year = int(date.today().strftime("%Y"))
        self.url = self.make_url(self.current_year)
        self.make_backscrape_iterable(kwargs)

        self.cipher = "AES256-SHA256"
        self.set_custom_adapter(self.cipher)

    @staticmethod
    def find_published_date(date_str: str) -> str:
        """Extract published date

        :param date_str: The row text
        :return: The date string
        """
        m = re.search(
            r"(\b\d{1,2}/\d{1,2}/\d{2,4}\b)|(\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b)",
            date_str,
        )
        return m.groups()[0] if m.groups()[0] else m.groups()[1]

    def extract_dockets_and_name(self, row) -> Tuple[str, str]:
        """Extract the docket and case name from each row

        :param row: Row to process
        :return: Docket(s) and Case Name
        """
        text = " ".join(row.xpath("ancestor::li[1]//text()"))
        clean_text = re.sub(r"[\n\r\t\s]+", " ", text)
        m = re.match(
            r"(?P<dockets>[SAC0-9, ]+)(?P<op_type> [A-Z].*)? - (?P<case_name>.*)",
            clean_text,
        )
        if not m:
            # Handle bad inputs
            m = re.match(
                r"(?P<dockets>[SAC0-9, ]+)(?P<op_type> [A-Z].*)? (?P<case_name>.*)",
                clean_text,
            )
        op_type = m.group("op_type")
        name = m.group("case_name")
        if op_type:
            name = f"{name} ({op_type.strip()})"
        return m.group("dockets"), name

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath(".//*[contains(@href, '.pdf')]"):
            pub = row.xpath('preceding::*[contains(., "Published")][1]/text()')
            if not pub:
                # Seen on most recent opinions, which have a header like
                # "Publication in the Connecticut Law Journal To Be Determined"
                logger.warning(
                    "No publication date for %s", row.text_content()
                )
                continue

            date_filed = self.find_published_date(pub[0])
            dockets, name = self.extract_dockets_and_name(row)
            self.cases.append(
                {
                    "url": row.get("href"),
                    "name": name,
                    "docket": dockets,
                    "date": date_filed,
                }
            )

    def make_url(self, year: int) -> str:
        """Makes URL using year input
        Data available since 2000, so (year % 2000) will work fine

        :param year: full year integer
        :return: url
        """
        year_str = str(year % 2000).zfill(2)
        return self.base_url.format(self.court_abbv, year_str)

    def _download_backwards(self, year: int) -> None:
        """Build URL with year input and scrape

        :param year: year to scrape
        :return None
        """
        logger.info("Backscraping for year %s", year)
        self.url = self.make_url(year)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly
        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if start else self.start_year
        end = int(end) + 1 if end else self.current_year

        self.back_scrape_iterable = range(start, end)
