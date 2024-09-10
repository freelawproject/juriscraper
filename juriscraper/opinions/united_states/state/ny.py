"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2014-07-04: Created by Andrei Chelaru, reviewed by mlr.
 2015-10-23: Parts rewritten by mlr.
 2016-05-04: Updated by arderyp to handle typos in docket string format
 2024-09-05: Updated by flooie to deal with block from main website
"""

import re
from datetime import date, timedelta
from typing import Any, Dict, Optional, Tuple

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import set_api_token_header
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    first_opinion_date = date(2003, 9, 25)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Court of Appeals"
        self.court_id = self.__module__
        self.url = "https://iapps.courts.state.ny.us/lawReporting/Search?searchType=opinion"
        self._set_parameters()
        self.expected_content_types = ["application/pdf", "text/html"]
        self.make_backscrape_iterable(kwargs)
        set_api_token_header(self)

    def _set_parameters(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> None:
        """Set the parameters for the POST request.

        If no start or end dates are given, scrape last month.
        This is the default behaviour for the present time scraper

        :param start_date:
        :param end_date:

        :return: None
        """
        self.method = "POST"

        if not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

        self.parameters = {
            "rbOpinionMotion": "opinion",
            "Pty": "",
            "and_or": "and",
            "dtStartDate": start_date.strftime("%m/%d/%Y"),
            "dtEndDate": end_date.strftime("%m/%d/%Y"),
            "court": self.court,
            "docket": "",
            "judge": "",
            "slipYear": "",
            "slipNo": "",
            "OffVol": "",
            "Rptr": "",
            "OffPage": "",
            "fullText": "",
            "and_or2": "and",
            "Order_By": "Party Name",
            "Submit": "Find",
            "hidden1": "",
            "hidden2": "",
        }

    def _process_html(self):
        for row in self.html.xpath(".//table")[-1].xpath(".//tr")[1:]:
            slip_cite = " ".join(row.xpath("./td[5]//text()"))
            official_citation = " ".join(row.xpath("./td[4]//text()"))
            url = row.xpath(".//a")[0].get("href")
            url = re.findall(r"(http.*htm)", url)[0]
            status = "Unpublished" if "(U)" in slip_cite else "Published"
            case = {
                "name": row.xpath(".//td")[0].text_content(),
                "date": row.xpath(".//td")[1].text_content(),
                "url": url,
                "status": status,
                "docket": "",
                "citation": official_citation,
                "parallel_citation": slip_cite,
                "author": "",
                "per_curiam": False,
            }
            author = row.xpath("./td")[-2].text_content()

            # Because P E R C U R I A M, PER CURIAM, and Per Curiam
            pc = re.sub(r"\s", "", author.lower())
            if "percuriam" in pc:
                case["per_curiam"] = True
            elif author:
                cleaned_author = normalize_judge_string(author)[0]
                if cleaned_author.endswith(" J."):
                    cleaned_author = cleaned_author[:-3]
                case["author"] = cleaned_author
            self.cases.append(case)

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the docket number from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        dockets = re.search(
            r"^<br>(?P<docket_number>No\. \d+(\s+SSM \d+)?)\s?$",
            scraped_text[:2000],
            re.MULTILINE,
        )
        if dockets:
            return {"Docket": dockets.groupdict()}
        return {}

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self._set_parameters(*dates)
        self.html = self._download()
        self._process_html()
