"""Scraper for Nevada Supreme Court
CourtID: nev

History:
    - 2023-12-13: Updated by William E. Palin
"""


import json
import re
from functools import partial

from lxml.html import fromstring

from juriscraper.NewOpinionSite import NewOpinionSite


class Site(NewOpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/AdvanceOpinions"
        self.search = "https://caseinfo.nvsupremecourt.us/public/caseSearch.do"
        self.status = "Published"
        self.court_code = "10001"

    def _download(self, **kwargs):
        """Download the JSON to parse

        :param kwargs:
        :return: None
        """
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
            deferred_scraper = partial(
                self.scrape_case_page, csNumber=case["caseNumber"]
            )

            self.cases.append(
                {
                    "citation": citation,
                    "name": case["caseTitle"],
                    "docket": case["caseNumber"],
                    "date": case["date"],
                    "url": deferred_scraper,
                    "judge": deferred_scraper,
                    "lower_court": deferred_scraper,
                }
            )

    def scrape_case_page(self, csNumber: str):
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
            "courtID": self.court_code,
            "startRow": "1",
            "displayRows": "50",
            "orderBy": "CsNumber",
            "orderDir": "DESC",
            "href": "/public/caseView.do",
            "submitValue": "Search",
        }
        content = self.request["session"].post(self.search, data=data).text
        html = fromstring(content)
        opinion_xpath = "//tr[td[contains(text(), 'Opinion')]]"
        opinion_row = html.xpath(opinion_xpath)[-1]
        slug = opinion_row.xpath("td/a/@href")[0]

        lower_court_xpath = "//td[text()='Lower Court Case(s):']//following-sibling::td[1]/text()"

        author_str = opinion_row.xpath("td[3]/text()")[0]
        author_match = re.search(r"Author:(?P<judge>[\s\w,]+).", author_str)
        judge = author_match.group("judge") if author_match else ""

        return {
            "url": f"https://caseinfo.nvsupremecourt.us{slug}",
            "lower_court": html.xpath(lower_court_xpath)[0],
            "judge": judge,
        }
