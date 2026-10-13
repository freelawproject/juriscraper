"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich.
Contact: sitefeedback@courts.mi.gov
History:
    - 2014-09-21: Updated by Jon Andersen to handle some fields being missing
    - 2014-08-05: Updated to have a dynamic URL, an oversight during check in.
    - 2022-01-28: Updated for new web site, @satsuki-chan.
    - 2026-02-25: Added backscraping support going back to December 2000.
"""

import re
from datetime import date, datetime
from typing import NotRequired
from urllib.parse import urlencode, urljoin

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import ExtractedMetadata, RawOpinion
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class SearchItem(TypedDict):
    title: str
    filingDate: str
    documentUrl: str
    courts: list[str] | None
    caseUrl: str
    decision: NotRequired[str | None]


class _Search(TypedDict):
    searchItems: list[SearchItem]


SEARCH_RESPONSE = TypeAdapter(_Search)


class Site(OpinionSiteLinear[tuple[date, date]]):
    title_re = re.compile(
        r"(MSC|COA) (?P<docket>\d{6})\s+(?P<name>.+)\s+Opinion"
    )
    court = "Supreme Court"
    days_interval = 10
    first_opinion_date = datetime(2000, 12, 12)
    filters = (
        ("releaseDate", "Past Year"),
        ("page", "1"),
        ("sortOrder", "Newest"),
        ("searchQuery", ""),
        ("resultType", "opinions"),
        ("pageSize", "100"),
    )

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        params = self.filters + (
            ("resource", "supreme-court-opinion"),
            ("aAppellateCourt", self.court),
        )
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"
        # Currently blocked from Michigan so we drop the user agent for now
        self.request["headers"] = {"User-Agent": ""}
        self.make_backscrape_iterable(kwargs)

    @override
    async def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        items = SEARCH_RESPONSE.validate_python(self.html, strict=True)[
            "searchItems"
        ]
        for item in items:
            self.cases.append(await self._extract_case_data_from_item(item))

    async def _extract_case_data_from_item(
        self, item: SearchItem
    ) -> RawOpinion:
        """Extract the case data from the item

        :param item: The item from the API
        :return: The case data
        """
        if (match := self.title_re.search(item["title"])) is not None:
            docket = match.group("docket")
            name = self.cleanup_case_name(match.group("name"))
        else:
            name, docket = await self.get_missing_name_and_docket(item)

        disposition = self.get_disposition(item)

        status = "Published"
        if "Unpublished" in item["title"]:
            status = "Unpublished"

        per_curiam = False
        if "per curiam" in item["title"].lower():
            per_curiam = True

        return {
            "date": item["filingDate"],
            "docket": docket,
            "name": name,
            "url": urljoin(
                (self.url if self.url is not None else ""),
                item["documentUrl"].strip(),
            ),
            "lower_court": self.parse_lower_courts(item["courts"]),
            "status": status,
            "per_curiam": per_curiam,
            "disposition": disposition,
        }

    def cleanup_case_name(self, name_raw: str) -> str:
        """Clean up case name in Michigan

        :param name_raw: Raw title string
        :return: Cleaned name
        """
        name = titlecase(re.sub(r"\s+", " ", name_raw.strip()))
        return name.replace("People of Mi ", "People of Michigan ")

    def parse_lower_courts(self, courts: list[str] | None) -> str:
        """Get the lower courts

        :param courts: Court names as an array
        :return: The lower courts combined into a string
        """
        if not bool(courts):
            return ""
        lower_courts = re.sub(r"\s+", " ", ", ".join(courts).lstrip(", "))
        return titlecase(lower_courts)

    async def get_missing_name_and_docket(
        self, item: SearchItem
    ) -> tuple[str, str]:
        """
        Return 2 placeholders. We can get the values via `extract_from_text`
        To be overriden in `michctapp`
        Sometimes the API returns bad "title" values. See #1648
        """
        return "Placeholder case name", "Placeholder docket number"

    def get_disposition(self, item: SearchItem) -> str:
        """To be overriden by michctapp"""
        return ""

    def _build_backscrape_url(self, dates: tuple[date, date]) -> str:
        """Build URL for backscraping with a custom date range.

        :param dates: (start_date, end_date) tuple
        :return: URL string
        """
        from_date = dates[0].strftime("%m/%d/%Y")
        to_date = dates[1].strftime("%m/%d/%Y")
        params = (
            ("releaseDate", f"Custom Range:{from_date}:{to_date}"),
            ("page", "1"),
            ("sortOrder", "Newest"),
            ("searchQuery", ""),
            ("resultType", "opinions"),
            ("pageSize", "100"),
            ("aAppellateCourt", self.court),
        )
        return f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Download opinions for a specific date range.

        :param dates: (start_date, end_date) tuple from make_backscrape_iterable
        :return: None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.url = self._build_backscrape_url(dates)
        self.html = await self._download()
        await self._process_html()

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extracts case names and docket numbers from the document's text

        :param scraped_text: the document's text
        :return: a dictionary in the shape of Courtlistener's models
        """
        pattern = re.compile(
            r"(?P<case_name>([\S ]+\n)+)\n+\s+Docket Nos?. (?P<docket_number>(\d{6}(,? and |, |.)?)+)"
        )
        if (match := pattern.search(scraped_text[:1500])) is not None:
            docket_number = match.group("docket_number").strip(" .")
            name = self.cleanup_case_name(
                match.group("case_name").replace("\n", ";")
            ).strip("; ")
            return {
                "OpinionCluster": {"case_name": name},
                "Docket": {"case_name": name, "docket_number": docket_number},
            }
        else:
            logger.error(
                "mich: extract_from_text failed",
                extra={"opinion_text": scraped_text[:1024].strip()},
            )
            return {}
