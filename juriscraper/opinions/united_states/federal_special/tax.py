# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1
import asyncio
from datetime import date, datetime, timedelta
from typing import NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Case(TypedDict):
    docketNumber: str
    docketEntryId: str
    documentType: str
    filingDate: str
    caseCaption: str
    signedJudgeName: NotRequired[str | None]
    judge: NotRequired[str | None]


class _Search(TypedDict):
    results: NotRequired[list[_Case]]


class _DownloadURL(TypedDict):
    url: str


_search_adapter = TypeAdapter(_Search)
_url_adapter = TypeAdapter(_DownloadURL)


class Site(OpinionSiteLinear[tuple[date, date]]):
    json: _Search

    first_opinion_date = datetime(1986, 5, 1)
    days_interval = 10
    base_url = "https://public-api-green.dawson.ustaxcourt.gov/public-api"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.set_blue_green = False
        self.url = f"{self.base_url}/opinion-search"
        self.court_id = self.__module__
        self.method = "GET"

        self.td = date.today()
        today = self.td.strftime("%m/%d/%Y")
        last_month = (self.td - timedelta(days=31)).strftime("%m/%d/%Y")
        self.params = self.request["parameters"]["params"] = {
            "dateRange": "customDates",
            "startDate": last_month,
            "endDate": today,
            "opinionTypes": "MOP,SOP,TCOP",
        }
        self.make_backscrape_iterable(kwargs)

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> _Search:
        """Download from api

        The tax court switches between blue and green deploys so we need to
        check which one is current before we continue

        :param request_dict: An empty dictionary.
        :return: None
        """
        if request_dict is None:
            request_dict = {}
        self.url = f"{self.base_url}/opinion-search"
        if self.test_mode_enabled():
            return _search_adapter.validate_python(
                await super()._download(request_dict), strict=True
            )

        if not self.set_blue_green:
            check = await self.request["session"].get(self.url)
            if check.status_code != 200:
                self.base_url = (
                    "https://public-api-blue.dawson.ustaxcourt.gov/public-api"
                )
                self.url = f"{self.base_url}/opinion-search"
            self.set_blue_green = True

        return _search_adapter.validate_python(
            await super()._download(request_dict), strict=True
        )

    @override
    async def _process_html(self) -> None:
        """Process the JSON response

        Iterate over each item on the page collecting our data.
        return: None
        """
        self.json = _search_adapter.validate_python(self.html, strict=True)

        for case in self.json.get("results", []):
            url = await self._get_url(
                case["docketNumber"], case["docketEntryId"]
            )
            status = (
                "Published"
                if case["documentType"] == "T.C. Opinion"
                else "Unpublished"
            )
            self.cases.append(
                {
                    "judge": case.get(
                        "signedJudgeName", case.get("judge", "")
                    ),
                    "date": case["filingDate"][:10],
                    "docket": case["docketNumber"],
                    "url": url,
                    "name": titlecase(case["caseCaption"]),
                    "status": status,
                }
            )

    async def _get_url(self, docket_number: str, docketEntryId: str) -> str:
        """Fetch the PDF URL with AWS API key

        param docket_number: The docket number
        param docketEntryId: The docket entry id
        return: The URL to the PDF
        """
        self.url = f"{self.base_url}/{docket_number}/{docketEntryId}/public-document-download-url"
        if self.test_mode_enabled():
            # Don't fetch urls when running tests.  Because it requires
            # a second api request.
            return self.url

        html = await super()._download()
        pdf_url = _url_adapter.validate_python(html, strict=True)["url"]
        return pdf_url

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request to the API

        Note that the API returns 100 results or less, so the
        days_interval should be conservative

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.params["startDate"] = dates[0].strftime("%m/%d/%Y")
        self.params["endDate"] = dates[1].strftime("%m/%d/%Y")
        self.html = await self._download()
        await self._process_html()
        result_count = len(self.json.get("results", []))
        logger.info(
            "Backscraping for range %s %s\n%s cases found",
            *dates,
            result_count,
        )

        # Using time.sleep to prevent rate limiting
        # {'message': 'you are only allowed 15 requests in a 60 second window time', 'type': 'ip-limiter'}
        if result_count > 0:
            logger.info("Sleeping for 61 seconds to prevent rate limit")
            await asyncio.sleep(61)
