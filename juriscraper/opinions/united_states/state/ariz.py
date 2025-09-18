"""
Author: Michael Lissner
Date created: 2013-04-05
Revised by Taliah Mirmalek on 2014-02-07
Scraper for the Supreme Court of Arizona
CourtID: ariz
Court Short Name: Ariz.
"""

import re

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.azcourts.gov/opinions/SearchOpinionsMemoDecs.aspx?court=999"
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        # Extract download URLs
        download_urls_path = '//a[contains(@id , "hypCaseNum")]/@href'
        download_urls = self.html.xpath(download_urls_path)

        # Extract case names
        case_names_path = '//span[contains(@id , "lblTitle")]//text()'
        case_names = [
            titlecase(t.upper()) for t in self.html.xpath(case_names_path)
        ]

        # Extract case dates
        case_dates_path = '//span[contains(@id , "FilingDate")]//text()'
        case_dates = list(self.html.xpath(case_dates_path))

        # Extract precedential statuses
        precedential_statuses = []
        precedential_statuses_path = '//*[contains(@id, "DecType")]/text()'
        for s in self.html.xpath(precedential_statuses_path):
            if "OPINION" in s:
                precedential_statuses.append("Published")
            elif "MEMORANDUM" in s:
                precedential_statuses.append("Unpublished")
            else:
                precedential_statuses.append("Unknown")

        # Extract docket numbers
        docket_numbers_path = '//a[contains(@id , "hypCaseNum")]//text()'
        docket_numbers = list(self.html.xpath(docket_numbers_path))

        # Build cases list
        for i in range(len(download_urls)):
            case = {
                "name": case_names[i],
                "date": case_dates[i],
                "status": precedential_statuses[i],
                "docket": docket_numbers[i],
                "url": download_urls[i],
            }
            self.cases.append(case)

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court and judge from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        lower_court_pattern = re.compile(
            r"""
            Appeal\s+from\s+the\s+(?P<lower_court>[^\n]+)\n\s*
            The\s+(?:Honorable\s+)?(?P<lower_court_judge>[^,]+),\s+Judge[^\n]*\n\s*
            No\.\s+(?P<lower_court_number>[^\s]+)
            """,
            re.X | re.MULTILINE | re.DOTALL,
        )

        result = {}

        if match := lower_court_pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

            lower_court_judge = match.group("lower_court_judge").strip()
            lower_court_number = match.group("lower_court_number").strip()

            if lower_court:
                result["Docket"] = {"appeal_from_str": lower_court}
            if lower_court_judge:
                result.setdefault("OriginatingCourtInformation", {})[
                    "assigned_to_str"
                ] = lower_court_judge
            if lower_court_number:
                result.setdefault("OriginatingCourtInformation", {})[
                    "docket_number"
                ] = lower_court_number

        return result
