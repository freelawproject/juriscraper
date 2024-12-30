"""Scraper for Nevada Supreme Court
CourtID: nev

History:
    - 2023-12-13: Updated by William E. Palin
"""

from lxml.html import fromstring

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_code = "10001"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/AdvanceOpinions"
        self.search = "https://caseinfo.nvsupremecourt.us/public/caseSearch.do"
        self.xp = "//tr[td[contains(text(), 'Opinion')]]/td/a/@href"
        self.status = "Published"
        self.request["headers"] = {
            "Referer": "https://nvcourts.gov/",
            "XApiKey": "080d4202-61b2-46c5-ad66-f479bf40be11",
        }

    def filter_cases(self):
        """Filter JSON to last two opinions without dupes

        Consolidated cases get listed multiple times so we want to remove
        those as well to avoid duplication issues

        :return: List of cases to download
        """
        cases = []
        for case in self.html:
            advances = [case["advanceNumber"] for case in cases]
            if (
                "COA" in case["caseNumber"]
                or case["advanceNumber"] in advances
            ):
                continue
            cases.append(case)
        return cases[:20]

    def _process_html(self):
        """Process Nevada Case Opinions

        :return: None
        """
        for case in self.filter_cases():
            vol = int(case["date"].split("-")[0]) - 1884
            citation = f"{vol} Nev., Advance Opinion {case['advanceNumber']}"
            self.cases.append(
                {
                    "citation": citation,
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
        self.parameters = {
            "action": "",
            "csNumber": csNumber,
            "shortTitle": "",
            "exclude": "off",
            "courtID": self.court_code,
            "startRow": "1",
            "displayRows": "50",
            "orderBy": "CsNumber",
            "orderDir": "DESC",
            "href": "/public/caseView.do",
            "submitValue": "Search",
        }
        self._request_url_post(self.search)
        content = self.request["response"].text
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
