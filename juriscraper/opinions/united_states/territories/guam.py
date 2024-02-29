"""Scraper for Supreme Court of Guam
CourtID: guam
Court Short Name: Guam
Author: mmantel
History:
  2019-12-09: Created by mmantel
  2024-01-25: updated by grossir
"""

import re
from datetime import date
from typing import Optional

from dateutil import parser
from dateutil.parser import ParserError

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://guamcourts.org/Supreme-Court-Opinions/Supreme-Court-Opinions.asp"
        self.status = "Published"

        self._year = date.today().year
        self.parameters = {"Year": str(self._year)}
        self.method = "POST"

        # The year dropdown goes back to 1990, but the Court wasn't
        # created until 1996 and there are no opinions posted for
        # prior years.
        self.back_scrape_iterable = range(1996, self._year)

    def _process_html(self) -> None:
        """Process HTML into case objects

        Some docket numbers are a consolidation of other dockets
        For example: "CVA12-018 (consolidated with CVA12-030)"
        Deleting the date and citation from the free text allows us
        to catch these names

        :return: None
        """
        middle_of_the_year = f"{self._year}/07/13"

        row_xpath = '//a[@id="Opinion"]/following-sibling::table'
        for table in self.html.xpath(row_xpath):
            text = table.xpath(".//td/text()")[0]

            # Seen formats: 2021-Guam 3, 2021 Guam 29, 2020 Guam15,
            # Edge cases which will be left empty: "Guam 7", "014 Guam 31"
            citation = ""
            citation_match = re.search(r"\d{4}[\s-]*Guam[\s-]*\d{1,2}", text)
            if citation_match:
                text = text.replace(citation_match.group(0), " ")
                citation = citation_match.group(0)

            row_date = self.find_date(text)
            name = table.xpath(".//a/text()")[0]
            docket = text.replace(row_date, "") if row_date else text
            docket = docket.replace(" filed ", "").strip(" .,\r\n")

            # If the docket is not in the free text, sometimes it is at the end
            # of the case name. Sometimes, it does not exist
            if not docket:
                docket_match = re.search(r"[A-Z]{3}\d{2}-\d{3}", name)
                if docket_match:
                    docket = docket_match.group(0)

            self.cases.append(
                {
                    "url": table.xpath(".//a/@href")[0],
                    "name": name,
                    "docket": docket,
                    "date": row_date or middle_of_the_year,
                    "date_filed_is_approximate": row_date is None,
                    "citation": citation,
                }
            )

    def find_date(self, text: str) -> Optional[str]:
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
                pass

    def _download_backwards(self, year: int) -> None:
        """Sets up the download of past records

        :param year: search filter for the page
        :return: None
        """
        self._year = year
        self.parameters = {"Year": str(year)}
