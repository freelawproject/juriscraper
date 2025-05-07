"""
CourtID: ncbizct
Court Short Name: North Carolina Business Court
Author: Kevin Ramirez
History:
    2025-05-06, quevon24: First version
"""
import re
from typing import Dict
from datetime import date, datetime
from urllib.parse import urlencode

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.nccourts.gov/documents/business-court-opinions"
        self.first_opinion_date = datetime(1996, 10, 24).date()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for row in self.html.xpath(".//div[contains(@class,'list__items')]/article"):
            # Extract case name and citation
            case_string = row.xpath(f".//h5[contains(@class,'list__title')]/a")[0].text_content().strip()
            case_name, citation = self.extract_case_and_citation(case_string)

            # Extract other data
            date_filed = row.xpath(f".//time")[0].text_content().strip()
            docket_number = row.xpath(f".//span[4]")[0].text_content().split("(", 1)[0].strip()
            status = row.xpath(f".//span[6]")[0].text_content().strip()
            download_url = row.xpath(f".//div[contains(@class,'file file--teaser')]/a/@href")[0]
            description = row.xpath(f".//div[contains(@itemprop,'description')]/p")
            summary_text = description[0].text_content().strip() if description else ""

            self.cases.append(
                {
                    "name": titlecase(case_name),
                    "docket": docket_number,
                    "url": download_url,
                    "summary": summary_text,
                    "date": date_filed,
                    "citation": citation,
                    "status": status,
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
            case_name = case_string[:citation_match.start()].strip()
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

    def make_backscrape_iterable(self, kwargs: Dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.now().date()

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, 1
        )