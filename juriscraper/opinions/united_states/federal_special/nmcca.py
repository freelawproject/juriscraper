"""Scraper for the Navy-Marine Corps Court of Criminal Appeals
CourtID: nmcca
Court Short Name:
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from datetime import date, datetime
from urllib.parse import urlencode

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Document(TypedDict):
    download_url: str


class _Attachment(TypedDict):
    document: _Document


_OpinionFields = TypedDict(
    "_OpinionFields",
    {
        "6e61b248-ef67-423e-b321-f2ed8ad05728": str,
        "80dedfc1-74a9-4372-a36f-8736c6baf754": str,
        "9152980f-7bd6-4b48-8130-10500cda8cca": str,
        "9a84d8ce-017d-4a4b-821f-2fa33b700b0c": str,
    },
)


class _Opinion(TypedDict):
    data: _OpinionFields
    documents: list[_Attachment]


class _Search(TypedDict):
    results: list[_Opinion]


_search_adapter = TypeAdapter(_Search)


class Site(OpinionSiteLinear[tuple[date, date]]):
    base_url = "https://www.jag.navy.mil/api/tables/decisions-opinions/data/"
    days_interval = 60
    first_opinion_date = datetime(2004, 1, 8)

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        kwargs.setdefault("verify", False)
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        response = _search_adapter.validate_python(self.html, strict=True)
        for row in response["results"]:
            fields = row["data"]
            date = fields["6e61b248-ef67-423e-b321-f2ed8ad05728"]
            docket = fields["80dedfc1-74a9-4372-a36f-8736c6baf754"]
            notes = fields["9152980f-7bd6-4b48-8130-10500cda8cca"]
            name = fields["9a84d8ce-017d-4a4b-821f-2fa33b700b0c"]
            url = row["documents"][0]["document"]["download_url"]
            if notes == "Unpublished":
                status = "Unpublished"
            else:
                status = "Published"
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "status": status,
                    "docket": docket,
                }
            )

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request

        "6e61b248-ef67-423e-b321-f2ed8ad05728" seems to be the name
        of the date field. It is also present on the response JSON keys.
        It seems stable through time, from last example file edit in 2023
        to April 2024.

        If something changes, go to
        https://www.jag.navy.mil/about/organization/ojag/code-05/nmcca/opinions/

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        ts = str(datetime.now().timestamp()).replace(".", "")[:13]
        start = dates[0].strftime("%Y-%m-%d")
        end = dates[1].strftime("%Y-%m-%d")
        params = {
            "page": "1",
            "page_size": "100",
            "ordering": "-data__6e61b248-ef67-423e-b321-f2ed8ad05728",
            "data__6e61b248-ef67-423e-b321-f2ed8ad05728__gte": start,
            "data__6e61b248-ef67-423e-b321-f2ed8ad05728__lte": end,
            "_": ts,
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = await self._download()
        self._process_html()
