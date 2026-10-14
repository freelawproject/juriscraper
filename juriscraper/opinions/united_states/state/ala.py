"""
Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Alabama
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
 - 2023-11-14: Alabama no longer uses page or use selenium.
 - 2026-01-12: fetch detailed publication data from new API endpoint.
 - 2026-01-28: Add backscraper using pagination.
"""

import re
from collections.abc import Mapping

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Document(TypedDict):
    documentName: str
    documentLinkUUID: str


class _PublicationItem(TypedDict):
    title: str
    caseInstanceUUID: str
    caseNumber: str
    groupName: str


class _Publication(TypedDict):
    publicationDate: str
    publicationItems: list[dict[str, object]]


class _Release(TypedDict):
    publicationUUID: str


class _ReleaseResults(TypedDict):
    results: list[_Release]


class _Releases(TypedDict):
    _embedded: _ReleaseResults


_publication_adapter = TypeAdapter(_Publication)
_publication_item_adapter = TypeAdapter(_PublicationItem)
_document_adapter = TypeAdapter(_Document)
_releases_adapter = TypeAdapter(_Releases)


class Site(OpinionSiteLinear[int]):
    json: _Publication

    court_str = "68f021c4-6a44-4735-9a76-5360b2e8af13"
    base_url = "https://publicportal-api.alappeals.gov"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}/courts/cms/publications"
        self.request["parameters"]["params"] = {
            "courtID": self.court_str,
            "page": 0,
            "size": 1,
            "sort": "publicationDate,desc",
        }
        self.make_backscrape_iterable(kwargs)

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> None:
        """Download the publication list and then fetch detailed publication data.

        The initial API returns a list of publications, but we need to fetch
        the detailed publication endpoint to get full case information.
        """
        if self.test_mode_enabled():
            self.json = _publication_adapter.validate_python(
                await super()._download(request_dict), strict=True
            )
            return

        # First, get the list of publications
        resp = _releases_adapter.validate_python(
            await super()._download(request_dict), strict=True
        )

        # Get the publicationUUID from the initial response
        releases = resp["_embedded"]["results"]
        publication_uuid = releases[0].get("publicationUUID")

        # Fetch detailed publication data (no params needed for this endpoint)
        self.url = f"{self.base_url}/courts/{self.court_str}/cms/publication/{publication_uuid}"
        self.request["parameters"]["params"] = {}
        self.json = _publication_adapter.validate_python(
            await super()._download(request_dict), strict=True
        )

    @override
    def _process_html(self) -> None:
        date_filed = self.json["publicationDate"][:10]
        for item in self.json["publicationItems"]:
            documents = item.get("documents", [])
            if not bool(documents):
                continue
            if not isinstance(documents, list):
                raise TypeError("Publication documents must be a list")
            first_document: object = documents[0]
            if not isinstance(first_document, dict):
                raise TypeError("A publication document must be an object")

            # Only process actual opinions, skip orders
            document_name: object = first_document["documentName"]
            if document_name not in [
                "Opinion",
                "Decision",
            ]:
                continue

            document = _document_adapter.validate_python(
                first_document, strict=True
            )
            publicationItem = _publication_item_adapter.validate_python(
                item, strict=True
            )
            name = publicationItem["title"]

            url = "{}/courts/{}/cms/case/{}/docketentrydocuments/{}".format(
                self.base_url,
                self.court_str,
                publicationItem["caseInstanceUUID"],
                document["documentLinkUUID"],
            )
            docket = publicationItem["caseNumber"]

            lower_court = ""
            lower_court_number = ""

            # Match (Appeal from <court>: <number>) format for standard appeals
            match = re.search(
                r"\(Appeal from (?P<lower_court>[^:]+):\s*(?P<lower_court_number>[^)]+)\)",
                name,
            )
            if match is not None:
                lower_court = match.group("lower_court").strip()
                lower_court_number = match.group("lower_court_number").strip()
                name = name[: match.start()].rstrip()

            # For "In re:" cases, extract the actual case name from parenthetical
            in_re_match = re.search(r"\((In re: .*?)\)", name)
            if in_re_match is not None:
                name = in_re_match.group(1).strip()

            judge = publicationItem["groupName"]
            if judge == "On Rehearing":
                judge = ""

            per_curiam = False
            if "curiam" in judge.lower():
                judge = ""
                per_curiam = True

            self.cases.append(
                {
                    "date": date_filed,
                    "name": name,
                    "docket": docket,
                    "status": "Published",
                    "url": url,
                    "judge": judge,
                    "per_curiam": per_curiam,
                    "lower_court": lower_court,
                    "lower_court_number": lower_court_number,
                }
            )

    @override
    async def _download_backwards(self, d: int) -> None:
        """Fetches a page of publications for backscraping."""
        self.url = f"{self.base_url}/courts/cms/publications"
        self.request["parameters"]["params"] = {
            "courtID": self.court_str,
            "page": d,
            "size": 1,
            "sort": "publicationDate,desc",
        }
        await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: Mapping[str, object]) -> None:
        """Checks if backscrape start and end arguments have been passed"""
        start = str(kwargs.get("backscrape_start"))
        end = str(kwargs.get("backscrape_end"))

        if not start.isdigit():
            start = "0"
        if not end.isdigit():
            end = "100"  # good amount of pages

        self.back_scrape_iterable = range(int(start), int(end))
