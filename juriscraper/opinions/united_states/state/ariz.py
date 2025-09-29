"""
Author: Michael Lissner
Date created: 2013-04-05
Revised by Taliah Mirmalek on 2014-02-07
Scraper for the Supreme Court of Arizona
CourtID: ariz
Court Short Name: Ariz.
"""

import re
from urllib.parse import urljoin

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.azcourts.gov/opinions/SearchOpinionsMemoDecs.aspx?court=999"
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        for row in self.html.xpath("//tr[@class='AOC_NewsItemRow']"):
            raw_status = row.xpath('.//*[contains(@id, "DecType")]/text()')[0]
            if "OPINION" in raw_status:
                status = "Published"
            elif "MEMORANDUM" in raw_status:
                status = "Unpublished"
            else:
                status = "Unknown"

            name = row.xpath(
                './/span[contains(@id , "lblTitle")]//text()'
            ).upper()
            parsed_case = {
                "name": titlecase(name),
                "url": urljoin(
                    self.url,
                    row.xpath('.//a[contains(@id , "hypCaseNum")]/@href'),
                ),
                "date": row.xpath(
                    './/span[contains(@id , "FilingDate")]//text()'
                )[0],
                "docket": row.xpath(
                    './/a[contains(@id , "hypCaseNum")]//text()'
                ),
                "status": status,
            }

            self.cases.append(parsed_case)

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
