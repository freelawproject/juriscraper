"""
Scraper for Pennsylvania Supreme Court
CourtID: pa
Court Short Name: pa
"""

import re
import urllib.parse
from datetime import date, datetime, timedelta
from typing import Dict, Tuple
from urllib.parse import urlencode

from lxml import html
from selenium.webdriver.common.devtools.v85.profiler import start

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court = "SUPREME"
    base_url = "https://www.pacourts.us/api/opinion?"
    document_url = "https://www.pacourts.us/assets/opinions/{}/out/{}"
    days_interval = 20
    api_dt_format = "%Y-%m-%dT00:00:00-05:00"
    first_opinion_date = datetime(1998, 4, 27)
    judge_key = "AuthorCode"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = re.compile(r"(.*)(?:[,-]?\s+Nos?\.)(.*)")
        self.status = "Published"

        now = datetime.now() + timedelta(days=1)
        start = now - timedelta(days=7)
        self.params = {
            "startDate": start.strftime(self.api_dt_format),
            "endDate": now.strftime(self.api_dt_format),
            "courtType": self.court,
            # "postTypes": "cd,cds,co,cs,dedc,do,ds,mo,oaj,pco,rv,sd",
            # "pageNumber":0,
            "sortDirection": "-1",
        }
        self.url = f"{self.base_url}{urlencode(self.params)}"
        self.make_backscrape_iterable(kwargs)
        self._opt_attrs = self._opt_attrs + ["minute_orders"]

        self.valid_keys.update({
            "minute_orders"
        })
        self._all_attrs = self._req_attrs + self._opt_attrs

        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_minute_orders(self):
        return self._get_optional_field_by_id("minute_orders")

    def _process_html(self) -> None:
        """Parses data into case dictionaries

        Note that pages returned have no pagination

        :return: None
        """
        json_response = self.html

        for cluster in json_response["Items"]:
            title = cluster["Caption"]
            disposition_date = cluster["DispositionDate"].split("T")[0]
            name, docket = self.parse_case_title(title)

            for op in cluster["Postings"]:
                per_curiam = False
                author_str = ""

                if op["Author"]:
                    author_str = self.clean_judge(op["Author"][self.judge_key])
                    if author_str.lower() == "per curiam":
                        author_str = ""
                        per_curiam = True

                # url = self.document_url.format(self.court, op["FileName"])
                url=f"https://www.pacourts.us/assets/opinions/{self.court}/out/{op['FileName']}?cb=1"
                encoded_url = urllib.parse.quote(url, safe=":/?&=")
                status = self.get_status(op)
                post_type = op["PostType"]["PostingTypeId"]

                if "Case Announcements" in name or "Argument List" in name:
                    order = True
                else:
                    order = False

                self.cases.append(
                    {
                        "date": disposition_date,
                        "name": name,
                        "docket": [docket.strip()],
                        "url": encoded_url,
                        "judge": author_str,
                        "type":post_type,
                        "status": status,
                        "per_curiam": per_curiam,
                        "minute_orders": order
                    }
                )

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
        page=1
        while True:
            self.params["pageNumber"] = page
            self.url = f"{self.base_url}{urlencode(self.params)}"
            logger.info("Backscraping for range %s %s", *dates)
            self.html = self._download()
            json_res = self.html
            if not json_res["Items"]:
                break
            self._process_html()
            page += 1


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self._download_backwards((start_date , end_date))

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_name(self):
        return "Supreme Court of Pennsylvania"

    def get_state_name(self):
        return "Pennsylvania"

    def get_class_name(self):
        return "pa"

    def get_court_type(self):
        return "state"
