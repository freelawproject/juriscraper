"""
Scraper for Pennsylvania Supreme Court
CourtID: pa
Court Short Name: pa
"""

import re
from datetime import date, datetime, timedelta
from typing import Dict, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court = "Supreme"
    base_url = "https://www.pacourts.us/api/opinion?"
    document_url = "https://www.pacourts.us/assets/opinions/{}/out/{}"
    days_interval = 1
    api_dt_format = "%Y-%m-%dT00:00:00-05:00"
    first_opinion_date = datetime(1998, 4, 27)
    judge_key = "AuthorCode"
    regional_cite_regex = re.compile(r"\d{1,3} A\.3d \d+")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = re.compile(r"(.*)(?:[,-]?\s+Nos?\.)(.*)")
        self.status = "Published"

        now = datetime.now()
        start = now - timedelta(days=1)
        self.params = {
            "startDate": start.strftime(self.api_dt_format),
            "endDate": now.strftime(self.api_dt_format),
            "courtType": self.court,
            "postTypes": "cd,cds,co,cs,dedc,do,ds,mo,oaj,pco,rv,sd",
            "sortDirection": "-1",
        }
        self.url = f"{self.base_url}{urlencode(self.params)}"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parses data into case dictionaries

        Note that pages returned have no pagination

        :return: None
        """
        json_response = self.html

        for cluster in json_response["Items"]:
            disposition_date = cluster["DispositionDate"].split("T")[0]
            title = cluster["Caption"]
            name, docket = self.parse_case_title(title)
            # A.3d cites seem to exist only for pasuperct
            cite = ""
            if cite_match := self.regional_cite_regex.search(title):
                cite = cite_match.group(0)

            for op in cluster["Postings"]:
                per_curiam = False
                author_str = ""

                if op["Author"]:
                    author_str = self.clean_judge(op["Author"][self.judge_key])
                    if author_str.lower() == "per curiam":
                        author_str = ""
                        per_curiam = True

                url = self.document_url.format(self.court, op["FileName"])
                status = self.get_status(op)
                self.cases.append(
                    {
                        "date": disposition_date,
                        "name": name,
                        "docket": docket,
                        "url": url,
                        "judge": author_str,
                        "status": status,
                        "per_curiam": per_curiam,
                        "citation": cite,
                    }
                )

        if not self.test_mode_enabled() and json_response.get("HasNext"):
            next_page = json_response["PageNumber"] + 1
            logger.info("Paginating to page %s", next_page)
            self.params["pageNumber"] = next_page
            self.url = f"{self.base_url}{urlencode(self.params)}"
            self.html = self._download()
            self._process_html()

    def parse_case_title(self, title: str) -> Tuple[str, str]:
        """Separates case_name and docket_number from case string

        :param title: string from the source

        :return: A tuple with the case name and docket number
        """
        search = self.regex.search(title)
        if search:
            name = search.group(1)
            docket = search.group(2)
        else:
            name = title
            docket = ""
        return name, docket

    def get_status(self, op: Dict) -> str:
        """Get status from opinion json.
        Inheriting classes have status data

        :param op: opinion json
        :return: parsed status
        """
        return self.status

    def clean_judge(self, author_str: str) -> str:
        """Cleans judge name. `pa` has a different format than
        `pasuperct` and `pacommwct`
        """
        return author_str

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Modify GET querystring for desired date range

        :param dates: (start_date, end_date) tuple
        :return None
        """
        start, end = dates
        self.params["startDate"] = start.strftime(self.api_dt_format)
        self.params["endDate"] = end.strftime(self.api_dt_format)
        self.url = f"{self.base_url}{urlencode(self.params)}"
        logger.info("Backscraping for range %s %s", *dates)
        self.html = self._download()
        self._process_html()
