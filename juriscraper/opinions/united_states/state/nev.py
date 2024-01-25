"""Scraper for Nevada Supreme Court
CourtID: nev

History:
    - 2023-12-13: Updated by William E. Palin
"""


import json
from datetime import datetime

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

    def set_now(self):
        if self.test_mode_enabled():
            self.now = datetime.fromisoformat("2023-11-02T00:00:00")
        else:
            self.now = datetime.now()

    def correct_court(self, case):
        if "COA" not in case["caseNumber"]:
            return True

    def _download(self, **kwargs):
        """"""
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
        """"""
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
        slug = fromstring(content).xpath(self.xp)[0]
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
