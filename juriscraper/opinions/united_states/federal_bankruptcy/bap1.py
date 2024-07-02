"""
Scraper for the United States Bankruptcy Appellate Panel for the First Circuit
CourtID: bap1
Court Short Name: 1st Cir. BAP
Court Contact: ca01_BAP@ca1.uscourts.gov, (617) 748-9650
Author: Gianfranco Rossi
History:
 - 2023-12-28, grossir: created
"""

import calendar
import re
from typing import Any, Dict, Optional

from lxml.html import HtmlElement

from juriscraper.lib.exceptions import SkipRowError
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    lower_court_to_abbreviation = {
        "USBC - District of New Hampshire": "NH",
        "USBC - District of Massachusetts (Worcester)": "MW",
        "USBC - District of Puerto Rico": "PR",
        "USBC - District of Massachusetts (Boston)": "MB",
        "USBC - District of Maine (Portland)": "EP",
        "USBC - District of Rhode Island": "RI",
        "Bankrupcty Court of ME - Bangor": "EB",
        "Bankruptcy Court of MA - Boston": "MB",
        "Bankruptcy Court of MA - Springfield": "MS",
        "Bankruptcy Court of ME - Portland": "EP",
        "Bankruptcy Court - Rhode Island": "RI",
        "Bankruptcy Court - San Juan Puerto Rico": "PR",
        "Bankruptcy Court of MA - Worcester": "MW",
        "Bankruptcy Court - Ponce Puerto Rico": "PR",
        "Bankruptcy Court of NH, Concord": "NH",
    }
    # See issue #828 for mapper extraction reference

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = self.url = "https://www.bap1.uscourts.gov/bapopn"
        self.court_id = self.__module__

        # There are 29 historical pages as of development in Dec 2023
        # source indexes from 0
        self.back_scrape_iterable = range(29)[::-1]

    def _download(self, request_dict: Optional[Dict] = None) -> HtmlElement:
        """Gets the source's HTML

        For a normal periodic scraper, get the last page where
        most recent opinions are
        Backscraper will iterate over all available pages

        :param request_dict: unused in this scraper
        :return: HTML object from the downloaded page
        """
        if self.base_url == self.url:
            self.html = super()._download()
            self.url = self.html.xpath("//li/a/@href")[-1]

        return super()._download()

    def _download_backwards(self, page_number: int) -> None:
        """Method used by backscraper to download historical records

        :param page_number: an element of self.back_scrape_iterable
        :return: None
        """
        self.url = f"{self.base_url}?page={page_number}"

    def _process_html(self) -> None:
        """Parses a page's HTML into opinion dictionaries

        Most recent opinions are on the last rows of the table

        :return: None
        """
        for row in self.html.xpath("//tr[td]")[::-1]:
            docket_string = self.get_text_by_xpath(row, "td[1]")

            try:
                status = self.get_status_from_docket_string(docket_string)
            except SkipRowError:
                continue

            partial_docket_number = self.get_text_by_xpath(row, "td[2]")
            date_placeholder = self.get_text_by_xpath(row, "td[3]")
            lower_court = self.get_text_by_xpath(row, "td[4]/span")
            name = row.xpath("td[4]")[0].text.strip()

            docket = self.build_full_docket_number(
                partial_docket_number, lower_court
            )

            self.cases.append(
                {
                    "status": status,
                    "url": row.xpath("td[1]/a/@href")[0],
                    "docket": docket,
                    "date": date_placeholder,
                    "name": name,
                    "lower_court": lower_court,
                }
            )

    def build_full_docket_number(
        self, partial_docket_number: str, lower_court: str
    ) -> str:
        """Completes docket number with lower court abbreviation

        For each unique lower court in the opinions available on the source,
        a linked opinion PDF was opened and the abbrevation extracted

        :param partial_docket_number: The partial docket string
        :param lower_court: The lower court abbreviation
        :return: The full docket number
        """
        lower_court_abbreviation = self.lower_court_to_abbreviation.get(
            lower_court, ""
        )

        return f"BAP No. {lower_court_abbreviation} {partial_docket_number}"

    @staticmethod
    def get_status_from_docket_string(docket_string: str) -> str:
        """Extracts status implicit in partial docket number

        Examples of opinion names: 02-084P1.01A, 00-094P1, 21-021P

        :param docket_string
        :raises SkipRowError: when the docket refers to an order
        :return: status in `[Published, Unpublished, Unknown]`
        """
        if "P" in docket_string:
            status = "Published"
        elif "U" in docket_string:
            status = "Unpublished"
        elif "O" in docket_string:
            raise SkipRowError(
                f"Skipping row {docket_string} because it is an order"
            )
        else:
            status = "Unknown"

        return status

    @staticmethod
    def get_text_by_xpath(html_element: HtmlElement, xpath: str) -> str:
        """Extracts first text content from html element located by xpath

        :param html_element: anchor element for xpath selection
        :param xpath: xpath string
        :return: stripped text content
        """
        return html_element.xpath(xpath)[0].text_content().strip()

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extract Date Filed from text

        :param scraped_text: Text of scraped content
        :return: Dict in the format expected by courtlistener,
                 containing date_filed
        """
        months = "|".join(calendar.month_name[1:])
        date_pattern = re.compile(rf"({months})\s+\d{{1,2}}\s?,?\s+\d{{4}}")
        match = re.search(date_pattern, scraped_text)
        date_extracted = match.group(0) if match else ""
        date_filed = re.sub(r"\s+", " ", date_extracted).strip()

        metadata = {
            "OpinionCluster": {
                "date_filed": convert_date_string(date_filed),
            },
        }
        return metadata
