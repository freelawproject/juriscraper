"""Scraper for Nevada Supreme Court
CourtID: nev

History:
    - 2023-12-13: Updated by William E. Palin
"""


import json
from datetime import datetime
from typing import Dict

from lxml.html import fromstring

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/AdvanceOpinions"
        self.search = "https://caseinfo.nvsupremecourt.us/public/caseSearch.do"
        self.xp = "//tr[td[contains(text(), 'Opinion')]]/td/a/@href"
        self.status = "Published"

    def set_now(self) -> None:
        """Define the now variable

        Use hard coded value for tests

        :return: None
        """
        if self.test_mode_enabled():
            self.now = datetime.fromisoformat("2023-11-02T00:00:00")
        else:
            self.now = datetime.now()

    def correct_court(self, case: Dict) -> bool:
        """Filter out cases based on court

        Check the case number to see if its a COA case or not

        :param case: the case information
        :return: if it is a COA case or not
        """
        if "COA" not in case["caseNumber"]:
            return True

    def _download(self, **kwargs):
        """Download the JSON to parse

        :param kwargs:
        :return: None
        """
        self.set_now()
        if self.test_mode_enabled():
            return json.load(open(self.url))
        return (
            self.request["session"]
            .get(
                self.url,
                headers=self.request["headers"],
                verify=self.request["verify"],
                timeout=60,
            )
            .json()
        )

    def _process_html(self):
        for case in self.html:
            if not self.correct_court(case):
                continue

            if (self.now - datetime.fromisoformat(case["date"])).days > 30:
                # Stop at 30 days
                break
            self.cases.append(
                {
                    "name": case["caseTitle"],
                    "docket": case["caseNumber"],
                    "date": case["date"],
                    "url": "placeholder",
                }
            )

    def fetch_document_link(self, csNumber: str):
        """Fetch document url

        Using case number - make a request to return the case page and
        find the opinion

        :param csNumber: the docket number/cs number to search
        :return: the document url
        """
        data = {
            "action": "",
            "csNumber": csNumber,
            "shortTitle": "",
            "exclude": "off",
            "startRow": "1",
            "displayRows": "50",
            "orderBy": "CsNumber",
            "orderDir": "DESC",
            "href": "/public/caseView.do",
            "submitValue": "Search",
        }
        content = self.request["session"].post(self.search, data=data).text
        slug = fromstring(content).xpath(self.xp)[-1]
        return f"https://caseinfo.nvsupremecourt.us{slug}"

    def _get_download_urls(self):
        """Get download urls

        :return: List URLs
        """

        def fetcher(case):
            if self.test_mode_enabled():
                return case["url"]
            return self.fetch_document_link(case["docket"])

        return DeferringList(seed=self.cases, fetcher=fetcher)
