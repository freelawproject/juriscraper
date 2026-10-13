"""
Scraper for Idaho Supreme Court / Court of Appeals
Contact: Sara Velasquez, svelasquez@idcourts.net, 208-947-7501
History:
 - 2014-08-05, mlr: Updated.
 - 2015-06-19, mlr: Updated to simply the XPath expressions and to fix an OB1
   problem that was causing an InsanityError. The cause was nasty HTML in their
   page.
 - 2015-10-20, mlr: Updated due to new page in use.
 - 2015-10-23, mlr: Updated to handle annoying situation.
 - 2016-02-25 arderyp: Updated to catch "ORDER" (in addition to "Order") in download url text
 - 2024-12-30, grossir: updated to OpinionSiteLinear
 - 2025-07-09, luism: Updated to prevent wrongly formatted dates
 - 2025-08-29, luism: Added extract_from_text to get lower court information
 - 2026-04-30, grossir: rewrote for the new isc.idaho.gov SPA + JSON API (#1914)
"""

import re
from datetime import date, datetime
from urllib.parse import urlencode, urljoin

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import (
    BackscrapeOptions,
    ExtractedMetadata,
    RawOpinion,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Block(TypedDict, total=False):
    component_name: str
    content: dict[str, object] | None


class _Document(TypedDict, total=False):
    content: list[_Block] | None


class _Result(TypedDict, total=False):
    id: int
    entry_date: str | None
    seo_description: str | None
    detail_json: _Document | None


class _Search(TypedDict, total=False):
    results: list[_Result] | None
    hasMore: bool
    nextCursor: str | None


_search_adapter = TypeAdapter(_Search)
_document_adapter = TypeAdapter(_Document)


class Site(OpinionSiteLinear[tuple[date, date]]):
    base_url = "https://isc.idaho.gov"
    list_path = "/api/cms-content-search"
    doc_path = "/api/cms-document"

    # Overridden by subclasses
    category = "ISC Civil"
    default_status = "Published"
    is_per_curiam = False

    # API caps server-side at 100; daily scrape only needs the first page
    # Since every scrape makes `page_size` secondary requests, let's limit
    # this value according to the expected volume. Published opinions will
    # have a smaller volume
    page_size = 10
    days_interval = 30
    first_opinion_date = datetime(2010, 1, 1)

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.status = self.default_status
        self.url = self._build_list_url("DESC")
        self.should_have_results = True
        self._back_start: date | None = None
        self._back_done = False
        # Parallel to self.cases; populated in _process_html so we can keep
        # the API's polished `title` as the case_name_short despite using
        # the long plaintiff/defendant join as `name`.
        self._case_name_shorts: list[str] = []
        self.make_backscrape_iterable(kwargs)

    def _build_list_url(self, direction: str, cursor: str = "") -> str:
        params = [
            ("scope", "documents"),
            ("category", self.category),
            ("sort_by", "entry_date"),
            ("sort_direction", direction),
            ("limit", str(self.page_size)),
        ]
        if bool(cursor):
            params.append(("cursor", cursor))

        return urljoin(self.base_url, f"{self.list_path}?{urlencode(params)}")

    @override
    async def _process_html(self) -> None:
        if not isinstance(self.html, dict):
            logger.info("Unexpected response type %s", self.html)
            return

        data = _search_adapter.validate_python(self.html, strict=True)
        results = data.get("results")
        if results is None:
            return
        for result in results:
            doc_id = result.get("id")
            entry_date = (
                entry_date_value
                if (entry_date_value := result.get("entry_date")) is not None
                else ""
            )[:10]

            # Backscrape: stop emitting once we cross the start_date
            if (
                self._back_start is not None
                and bool(entry_date)
                and entry_date < self._back_start.isoformat()
            ):
                self._back_done = True
                return

            doc = await self._fetch_doc_detail(result)
            content = self._extract_opinion_content(doc)
            opinion_field = content.get("opinion_file")
            if opinion_field is not None and not isinstance(
                opinion_field, dict
            ):
                raise TypeError("An opinion file field must be an object.")
            opinion_file = (
                opinion_field.get("value")
                if opinion_field is not None
                else None
            )
            url = (
                opinion_file.get("url")
                if isinstance(opinion_file, dict)
                else None
            )
            if not isinstance(url, str) or not bool(url):
                logger.error(
                    "%s: missing opinion_file URL for document id %s",
                    self.court_id,
                    doc_id,
                )
                continue

            release_date = self._field(content, "release_date")
            title = self._field(content, "title")
            if not bool(title):
                title = self._fallback_name(result)
            name = self._build_full_name(content)
            case: RawOpinion = {
                "date": (release_date if bool(release_date) else entry_date),
                "docket": self._field(content, "docket_number"),
                "name": name if bool(name) else title,
                "url": url,
                "summary": self._field(content, "summary"),
            }
            if self.is_per_curiam:
                case["per_curiam"] = True
            self.cases.append(case)
            self._case_name_shorts.append(title)

    @staticmethod
    def _extract_opinion_content(doc: _Document) -> dict[str, object]:
        """Pull the Opinion component's content out of a cms-document
        response.
        """
        content = doc.get("content")
        if content is None:
            return {}
        for block in content:
            if block.get("component_name") == "Opinion":
                fields = block.get("content")
                return fields if bool(fields) else {}
        return {}

    @staticmethod
    def _field(content: dict[str, object], key: str) -> str:
        field = content.get(key)
        if field is not None and not isinstance(field, dict):
            raise TypeError(f"Opinion field {key!r} must be an object.")
        value: object = field.get("value") if field is not None else None
        return str(value).strip() if value is not None else ""

    def _build_full_name(self, content: dict[str, object]) -> str:
        """Join plaintiff and defendant from the doc detail into a long
        case name, titlecased. Returns "" if either side is missing.
        """
        plaintiff = self._field(content, "plaintiff").rstrip(",;. ").strip()
        defendant = self._field(content, "defendant").rstrip(",;. ").strip()
        if bool(plaintiff) and bool(defendant):
            return titlecase(f"{plaintiff} vs. {defendant}")
        return ""

    @override
    def _get_case_name_shorts(self) -> list[str]:
        # Use the source's polished `title` field instead of the default
        # CaseNameTweaker heuristic, which can't handle Idaho's long
        # all-caps party names.
        return list(self._case_name_shorts)

    @staticmethod
    def _fallback_name(result: _Result) -> str:
        # Listing's seo_description is "Case Name\nSummary..."
        description = result.get("seo_description")
        desc = description.strip() if description is not None else ""
        return desc.split("\n", 1)[0] if bool(desc) else ""

    async def _fetch_doc_detail(self, result: _Result) -> _Document:
        # In test mode, the cms-document response is embedded inside each
        # listing result under "detail_json" to keep example files
        # consolidated.
        if self.test_mode_enabled():
            detail = result.get("detail_json")
            return detail if bool(detail) else {}

        doc_id = result.get("id")
        url = urljoin(self.base_url, f"{self.doc_path}?id={doc_id}")
        await self._request_url_get(url)
        self._post_process_response()
        doc = self._return_response_text_object()
        return _document_adapter.validate_python(
            (doc if bool(doc) else {}), strict=True
        )

    @override
    async def _download_backwards(self, d: tuple[date, date]) -> None:
        start, _ = d
        self._back_start = start
        self._back_done = False
        cursor = ""
        self.page_size = 100  # set page size to max

        while not self._back_done:
            self.url = self._build_list_url("DESC", cursor)
            self.html = await self._download()
            data = _search_adapter.validate_python(self.html, strict=True)
            if not bool(data.get("results")):
                logger.info("No results")
                break

            await self._process_html()
            if self._back_done or not bool(data.get("hasMore")):
                logger.info("Backscrape done")
                break

            next_cursor = data.get("nextCursor")
            if not bool(next_cursor):
                logger.info("No cursor")
                break
            cursor = next_cursor

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Build a single (start, end) tuple from kwargs.

        We paginate by cursor inside _download_backwards rather than by
        calendar windows, so a single tuple is enough.
        """
        start_str = kwargs.get("backscrape_start")
        end_str = kwargs.get("backscrape_end")
        start = (
            datetime.strptime(start_str, "%Y/%m/%d").date()
            if bool(start_str)
            else self.first_opinion_date.date()
        )
        end = (
            datetime.strptime(end_str, "%Y/%m/%d").date()
            if bool(end_str)
            else date.today()
        )
        self.back_scrape_iterable = [(start, end)]

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            Appeals?\s+from\s+the\s+
            (?P<lower_court>[^.]+?)
            (?=\s*\.)
            """,
            re.X | re.DOTALL,
        )

        judge_pattern = re.compile(
            r"County[.,]\s*(?P<judge>.+?), (?:Senior )?District Judge"
        )

        result: ExtractedMetadata = {}
        if (match := pattern.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            if "County," in lower_court:
                lower_court = lower_court.split("County")[0] + "County"

            result["Docket"] = {
                "appeal_from_str": lower_court,
            }

            if (match := judge_pattern.search(scraped_text)) is not None:
                lower_court_judge = re.sub(
                    r"\s+", " ", match.group("judge")
                ).strip()
                result["OriginatingCourtInformation"] = {
                    "assigned_to_str": lower_court_judge
                }

        return result
