"""Scraper for Trademark Trial and Appeal Board (TTAB) Reading Room
CourtID: ttab
Court Short Name: TTAB
Author: Ansel Halliburton
Type: Precedential
"""

from datetime import date, datetime
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(1986, 12, 23)
    days_interval = 30
    TTAB_RR_BASE = "https://ttab-reading-room.uspto.gov"
    TTAB_RR_API = urljoin(TTAB_RR_BASE, "ttab-efoia-api/decision/search")
    TTAB_RR_PDF_BASE = urljoin(TTAB_RR_BASE, "/cms/rest/")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.TTAB_RR_API
        self.method = "POST"
        self.status = "Published"
        self.should_have_results = True
        self._search_payload = {
            "dateRangeData": {},
            "facetData": {},
            "parameterData": {"precedentCitableIndicator": "Y"},
            "searchText": "",
            "sortDataBag": [{"issueDate": "desc"}],
            "recordStartNumber": 0,
        }
        self.parameters = {}
        self.request["parameters"] = {"json": self._search_payload}
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        results = self.html.get("results", [])
        seen_docs = set()
        for r in results:
            doc_id = r.get("documentId", "")
            if not doc_id:
                logger.warning("Skipping result: no doc_id")
                continue
            if doc_id in seen_docs:
                logger.warning(f"Skipping result: duplicate doc_id = {doc_id}")
                continue
            seen_docs.add(doc_id)
            self.cases.append(
                {
                    "name": r.get("partyName", "").strip(),
                    "url": urljoin(self.TTAB_RR_PDF_BASE, doc_id.lstrip("/")),
                    "date": r.get("issueDateStr", ""),
                    "docket": r.get("proceedingNumberDisplay", ""),
                    "judge": ", ".join(
                        map(titlecase, r.get("panelMember", "").split(";"))
                    ),  # "LYKOS;ENGLISH;COHEN" -> "Lykos, English, Cohen"
                    "author": titlecase(r.get("decisionWriter", "")),
                    "disposition": r.get("decision", ""),
                    "summary": r.get("issue", ""),
                }
            )

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        self._search_payload["dateRangeData"] = {
            "decisionDate": {
                "from": dates[0].strftime("%Y-%m-%d"),
                "to": dates[1].strftime("%Y-%m-%d"),
            }
        }
        self._search_payload["recordStartNumber"] = 0
        self.html = await self._download()
        total = self.html.get("recordTotalQuantity", 0)
        self._process_html()

        page_size = 25
        start = page_size
        while start < total:
            self._search_payload["recordStartNumber"] = start
            self.html = await self._download()
            self._process_html()
            start += page_size
