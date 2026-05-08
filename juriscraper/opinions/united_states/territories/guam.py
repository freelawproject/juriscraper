"""Scraper for Supreme Court of Guam
CourtID: guam
Court Short Name: Guam
Author: mmantel
History:
  2019-12-09: Created by mmantel
  2024-01-25: updated by grossir
  2026-05-04: updated for new legacydata endpoint by grossir (#1938)
"""

import re
from datetime import date

from dateutil import parser
from dateutil.parser import ParserError

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.guamcourts.gov/legacydata/supreme-court-opinions"

    # The year dropdown goes back to 1990, but the Court wasn't
    # created until 1996 and there are no opinions posted for
    # prior years.
    first_opinion_date = date(1996, 1, 1)
    days_interval = 365

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.status = "Published"

        self._year = date.today().year
        self.request["parameters"]["params"] = {
            "action": "get_items",
            "type": "SPRMOP",
            "year": str(self._year),
        }
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Process HTML into case objects

        Some docket numbers are a consolidation of other dockets
        For example: "CVA12-018 (consolidated with CVA12-030)"
        Deleting the date and citation from the free text allows us
        to catch these names

        :return: None
        """
        middle_of_the_year = f"{self._year}/07/13"

        for item in self.html.xpath(
            '//div[contains(@class, "item_for_list")]'
        ):
            anchor = item.xpath(".//h4/a")[0]
            name = anchor.text_content().strip()
            url = anchor.get("href")
            text = " ".join(item.xpath(".//p//text()")).strip()
            # Some entries arrive double-encoded; \xc2\xa0 is mojibake for
            # a non-breaking space and breaks both the citation and date
            # regexes when it sits between tokens
            text = re.sub(r"[\xa0\xc2]+", " ", text)

            # Seen formats: 2021-Guam 3, 2021 Guam 29, 2020 Guam15
            # Edge cases left empty: "Guam 7", "014 Guam 31"
            citation = ""
            if citation_match := re.search(
                r"\d{4}[\s-]*Guam[\s-]*\d{1,2}", text
            ):
                text = text.replace(citation_match.group(0), " ")
                citation = citation_match.group(0)

            row_date = self.find_date(text)
            docket = text.replace(row_date, "") if row_date else text
            docket = docket.replace(" filed ", "").strip(" .,\r\n")

            # If the docket is not in the free text, sometimes it is at the end
            # of the case name. Sometimes, it does not exist
            if not docket and (
                docket_match := re.search(r"[A-Z]{3}\d{2}-\d{3}", name)
            ):
                docket = docket_match.group(0)

            self.cases.append(
                {
                    "url": url,
                    "name": name,
                    "docket": docket,
                    "date": row_date or middle_of_the_year,
                    "date_filed_is_approximate": row_date is None,
                    "citation": citation,
                }
            )

    def find_date(self, text: str) -> str | None:
        """Find dates on text, and validate that they are indeed dates
        Sometimes the regex will pick a part of the string that is not a date

        :param text: free text with docket, date and citation info in varying order
        :return: validated date or None
        """
        # Seen formats: "12-28-2023", "October 11, 2023", "Nov. 29, 2023"
        date_pattern = r"([JFMASONDa-z.]+|\d{1,4})[\s-]+\d{1,2}[,\s-]+\d{2,4}"
        for date_match in re.finditer(date_pattern, text):
            try:
                parser.parse(date_match.group())
                return date_match.group()
            except ParserError:
                logger.warning("Unable to find date %s", text)
                pass

    def make_backscrape_iterable(self, kwargs):
        super().make_backscrape_iterable(kwargs)

        # keep unique years
        iterable = []
        for d, _ in self.back_scrape_iterable:
            if d.year not in iterable:
                iterable.append(d.year)

        self.back_scrape_iterable = iterable

    async def _download_backwards(self, year: int) -> None:
        """Sets up the download of past records

        :param year: search filter for the page
        :return: None
        """
        self._year = year
        self.request["parameters"]["params"]["year"] = str(year)
