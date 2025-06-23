"""
CourtID: ncbizct
Court Short Name: North Carolina Business Court
Author: Kevin Ramirez
History:
    2025-05-06, quevon24: First version
"""

import re
from datetime import date
from urllib.parse import urlencode

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    days_interval = 7

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.nccourts.gov/documents/business-court-opinions"
        self.first_opinion_date = date(1996, 10, 24)
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    def _process_html(self):
        for row in self.html.xpath(
            ".//div[contains(@class,'list__items')]/article"
        ):
            # Extract case name and citation
            case_string = (
                row.xpath(".//h5[contains(@class,'list__title')]/a")[0]
                .text_content()
                .strip()
            )
            case_name, citation = self.extract_case_and_citation(case_string)

            # Extract other data
            date_filed = row.xpath(".//time")[0].text_content().strip()
            # In the same span we can find the docket number, the lower court and the author
            span_text = (
                row.xpath(".//div[@class='meta']/span[4]")[0]
                .text_content()
                .strip()
            )
            docket_number = span_text.split("(", 1)[0].strip()

            start_parentheses = span_text.find("(")
            end_parentheses = span_text.find(")")

            author_str = ""
            lower_courts = []
            if start_parentheses != -1 and end_parentheses != -1:
                text_in_parentheses = span_text[
                    start_parentheses + 1 : end_parentheses
                ].strip()
                parts = text_in_parentheses.split(" - ", 1)

                if len(parts) > 0:
                    lower_court_parts = parts[0].strip().split(",")
                    for court in lower_court_parts:
                        lower_courts.append(f"{court} County Court")

                if len(parts) > 1:
                    author_str = parts[1].strip()

            status = row.xpath(".//span[6]")[0].text_content().strip()
            download_url = row.xpath(
                ".//div[contains(@class,'file file--teaser')]/a/@href"
            )[0]

            self.cases.append(
                {
                    "name": titlecase(case_name),
                    "docket": docket_number,
                    "url": download_url,
                    "date": date_filed,
                    "citation": citation,
                    "status": status,
                    "author": author_str,
                    "lower_court": ", ".join(lower_courts),
                }
            )

    def extract_case_and_citation(self, case_string):
        """Extract citations and clean up case name

        Possible strings:
        BRADLEY V. U.S. PACKAGING, INC., et al. 1998 NCBC 3
        FRAZIER v. BEARD 1996 NCBC 1
        ATKORE INT'L, INC. v. DINKHELLER, 2025 NCBC 20
        """
        case_string = case_string.strip()
        citation_match = re.search(r"(\d{4} NCBC \d+)$", case_string)

        if citation_match:
            citation = citation_match.group(1)
            case_name = case_string[: citation_match.start()].strip()
            case_name = case_name.rstrip(", ").strip()
        else:
            citation = ""
            case_name = case_string

        return case_name, citation

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Build URL with year input and scrape

        :param dates: (start_date, end_date) tuple
        :return None
        """
        params = {
            "field_publish_date_value": dates[0].strftime("%m/%d/%Y"),
            "field_publish_date_value_1": dates[1].strftime("%m/%d/%Y"),
        }
        self.url = f"{self.url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()
