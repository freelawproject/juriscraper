"""
Scraper for the United States Bankruptcy Appellate Panel for the First Circuit
CourtID: bap1
Court Short Name: 1st Cir. BAP
"""
import calendar
import re
from typing import Any, Dict, Optional

from lxml.html import HtmlElement

from juriscraper.lib.exceptions import SkipRowError
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # See issue #828 for mapper extraction reference
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = self.url = "https://www.bap1.uscourts.gov/bapopn"
        self.court_id = self.__module__

        # There are 29 pages as of development in Dec 2023 (source indexes from 0)
        self.back_scrape_iterable = range(29)[::-1]

    def _download(self, request_dict: Optional[Dict] = None) -> HtmlElement:
        # For a normal periodic scraper, get the last page where most recent opinions are
        if self.base_url == self.url:
            self.html = super()._download()
            self.url = self.html.xpath("//li/a/@href")[-1]

        return super()._download()

    def _download_backwards(self, page_number: int) -> None:
        self.url = f"{self.base_url}?page={page_number}"

    def _process_html(self) -> None:
        # Most recent opinions are on the last rows of the table
        for row in self.html.xpath("//tr[td]")[::-1]:
            opinion_number = row.xpath("td[1]")[0].text_content().strip()

            try:
                status = self.get_status_from_opinion_number(opinion_number)
            except SkipRowError:
                continue

            lower_court = row.xpath("td[4]/span")[0].text_content().strip()
            docket_number = row.xpath("td[2]")[0].text_content().strip()

            case = {
                "status": status,
                "url": row.xpath("td[1]/a/@href")[0],  # opinion url
                "docket": self.build_full_docket_number(
                    docket_number, lower_court
                ),
                # Pub Date
                "date": row.xpath("td[3]")[0].text_content().strip(),
                # short title
                "name": row.xpath("td[4]")[0].text.strip(),
                # district
                "lower_court": lower_court,
            }

            self.cases.append(case)

    def build_full_docket_number(
        self, docket_number: str, lower_court: str
    ) -> str:
        """
        Full docket number has the lower court abbreviation in it
        For each unique lower court in the opinions available on the source,
        the linked opinion PDF was opened and the abbrevation extracted
        """
        lower_court_abbreviation = self.lower_court_to_abbreviation.get(
            lower_court, ""
        )

        return f"BAP No. {lower_court_abbreviation} {docket_number}"

    @staticmethod
    def get_status_from_opinion_number(opinion_number: str) -> str:
        """
        Examples of opinion names: 02-084P1.01A, 00-094P1, 21-021P
        """
        if "P" in opinion_number:
            status = "Published"
        elif "U" in opinion_number:
            status = "Unpublished"
        elif "O" in opinion_number:
            raise SkipRowError(
                f"Skipping row {opinion_number} because it is an order"
            )
        else:
            status = "Unknown"

        return status

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extract Date Filed from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        months = "|".join(calendar.month_name[1:])
        date_pattern = re.compile(rf"({months})\s+\d{{1,2}}\s?,?\s+\d{{4}}")
        match = re.search(date_pattern, scraped_text)
        date_extracted = match.group(0) if match else ""
        date_filed = re.sub(r"\s+", " ", date_extracted).strip()

        metadata = {
            "OpinionCluster": {
                "date_filed": date_filed,
            },
        }

        return metadata
