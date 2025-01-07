"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich.
Contact: sitefeedback@courts.mi.gov
History:
    - 2014-09-21: Updated by Jon Andersen to handle some fields being missing
    - 2014-08-05: Updated to have a dynamic URL, an oversight during check in.
    - 2022-01-28: Updated for new web site, @satsuki-chan.
"""

import re
from datetime import datetime
from typing import List
from urllib.parse import urlencode

from typing_extensions import override

from juriscraper.DeferringList import DeferringList
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Supreme Court"
        self.court_resource="supreme-court-opinion"
        self.opinion_type='SearchCaseOpinions'
        # Currently blocked from Michigan so we drop the user agent for now
        self.request["headers"] = {"User-Agent": ""}
        self.title_re = r"(MSC|COA) (?P<docket>\d+)\s+(?P<name>.+)\s+Opinion"
        self.status = "Published"
        self.cases = []

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for item in self.html["searchItems"]:
            match = re.search(self.title_re, item["title"])

            if match:
                docket = match.group("docket")
                name = self.cleanup_case_name(match.group("name"))
            else:
                # In some cases the case name is missing. Grab the docket from the title in a different manner
                docket = item["title"].split("_")[0]
                name = ""
                continue
            self.cases.append({
                "date": item["displayDate"],
                "docket": [docket],
                "name": name,
                "url": f"https://www.courts.michigan.gov{item['documentUrl'].strip()}",
                "lower_court": self.get_lower_courts(item["courts"]),
                "disposition": item["title"],
            })

    @override
    def _get_case_name_shorts(self):
        """Generates short case names for all the case names that we scrape."""
        case_name_shorts = []
        for case in self.cases:
            case_name=case['name']
            case_name_shorts.append(self.cnt.make_case_name_short(case_name))
        return case_name_shorts

    def _get_case_names(self) -> List[str]:
        """Get case names *if* missing

        In some cases the case name is missing. This method uses a deferred list to the get the case name.

        :return: List of case names
        """
        # def fetcher(case):
        #     if case["name"] != "":
        #         # Return the name we extracted without using fetcher
        #         return case["name"]
        #     elif self.test_mode_enabled():
        #         # if we're in test mode, return a dummy name
        #         return "Test Name"
        #     else:
        #         # Else, query the API and return the name of the case
        #         self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseSearchContent/?searchQuery={case['title']}"
        #         self.html = self._download()
        #         case["name"] = self.html["opinionResults"]["searchItems"][0][
        #             "title"].title()
        #     return case["name"]
        # return DeferringList(seed=self.cases, fetcher=fetcher)
        names=[]
        for i in self.cases:
            names.append(i['name'])
        return names

    def cleanup_case_name(self, name_raw: str) -> str:
        """Clean up case name in Michigan

        :param name_raw: Raw title string
        :return: Cleaned name
        """
        name = titlecase(name_raw)
        if "People of Mi " in name:
            name = name.replace("People of Mi ", "People of Michigan ")
        return name

    def get_lower_courts(self, courts: List[str]) -> str:
        """Get the lower courts

        :param courts: Court names as an array
        :return: The lower courts combined into a string
        """
        if courts:
            lower_courts = ", ".join(courts).lstrip(", ")
        else:
            lower_courts = ""
        return titlecase(lower_courts)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        page = 1
        page_size = 100
        last_page = None
        while True:
            self.filters = (("releaseDate",
                             f"Custom Range:{start_date.month}/{start_date.day}/{start_date.year}:{end_date.month}/{end_date.day}/{end_date.year}"),
                            ("page", f"{page}"), ("sortOrder", "Newest"),
                            ("searchQuery", ""), ("pageSize", f"{page_size}"),)
            params = self.filters + (("resource", self.court_resource),
                                     ("aAppellateCourt", self.court),)
            self.url = f"https://www.courts.michigan.gov/api/CaseSearch/{self.opinion_type}?{urlencode(params)}"
            self.parse()
            last_page=self.html['totalPages']
            if last_page !=0:
                if page == last_page and last_page is not None:
                    break
            else:
                break
            self.downloader_executed = False
            page = page + 1
        return 0

    def get_court_name(self):
        return "Supreme Court of Michigan"

    def get_class_name(self):
        return "mich"

    def get_state_name(self):
        return "Michigan"

    def get_court_type(self):
        return "state"
