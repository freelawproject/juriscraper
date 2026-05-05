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

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://isc.idaho.gov"
    list_path = "/api/cms-content-search"
    doc_path = "/api/cms-document"

    # Overridden by subclasses
    category = "ISC Civil"
    default_status = "Published"
    is_per_curiam = False

    # API caps server-side at 100; daily scrape only needs the first page
    page_size = 100
    days_interval = 30
    first_opinion_date = datetime(2010, 1, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = self.default_status
        self.url = self._build_list_url("DESC")
        self.expected_content_types = ["application/json"]
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
        if cursor:
            params.append(("cursor", cursor))

        return urljoin(self.base_url, f"{self.list_path}?{urlencode(params)}")

    async def _process_html(self) -> None:
        if not isinstance(self.html, dict):
            logger.info("Unexpected response type %s", self.html)
            return

        for result in self.html.get("results") or []:
            doc_id = result.get("id")
            entry_date = (result.get("entry_date") or "")[:10]

            # Backscrape: stop emitting once we cross the start_date
            if (
                self._back_start
                and entry_date
                and entry_date < self._back_start.isoformat()
            ):
                self._back_done = True
                return

            doc = await self._fetch_doc_detail(result)
            content = self._extract_opinion_content(doc)
            opinion_file = (content.get("opinion_file") or {}).get("value")
            url = (opinion_file or {}).get("url")
            if not url:
                logger.error(
                    "%s: missing opinion_file URL for document id %s",
                    self.court_id,
                    doc_id,
                )
                continue

            release_date = self._field(content, "release_date")
            title = self._field(content, "title") or self._fallback_name(
                result
            )
            case = {
                "date": release_date or entry_date,
                "docket": self._field(content, "docket_number"),
                "name": self._build_full_name(content) or title,
                "url": url,
                "summary": self._field(content, "summary"),
            }
            if self.is_per_curiam:
                case["per_curiam"] = True
            self.cases.append(case)
            self._case_name_shorts.append(title)

    @staticmethod
    def _extract_opinion_content(doc: dict) -> dict:
        """Pull the Opinion component's content out of a cms-document
        response.
        """
        for block in doc.get("content") or []:
            if block.get("component_name") == "Opinion":
                return block.get("content") or {}
        return {}

    @staticmethod
    def _field(content: dict, key: str) -> str:
        value = (content.get(key) or {}).get("value")
        return str(value).strip() if value is not None else ""

    def _build_full_name(self, content: dict) -> str:
        """Join plaintiff and defendant from the doc detail into a long
        case name, titlecased. Returns "" if either side is missing.
        """
        plaintiff = self._field(content, "plaintiff").rstrip(",;. ").strip()
        defendant = self._field(content, "defendant").rstrip(",;. ").strip()
        if plaintiff and defendant:
            return titlecase(f"{plaintiff} vs. {defendant}")
        return ""

    def _get_case_name_shorts(self):
        # Use the source's polished `title` field instead of the default
        # CaseNameTweaker heuristic, which can't handle Idaho's long
        # all-caps party names.
        return list(self._case_name_shorts)

    @staticmethod
    def _fallback_name(result: dict) -> str:
        # Listing's seo_description is "Case Name\nSummary..."
        desc = (result.get("seo_description") or "").strip()
        return desc.split("\n", 1)[0] if desc else ""

    async def _fetch_doc_detail(self, result: dict) -> dict:
        # In test mode, the cms-document response is embedded inside each
        # listing result under "detail_json" to keep example files
        # consolidated.
        if self.test_mode_enabled():
            return result.get("detail_json") or {}

        doc_id = result.get("id")
        url = urljoin(self.base_url, f"{self.doc_path}?id={doc_id}")
        await self._request_url_get(url)
        self._post_process_response()
        doc = self._return_response_text_object()
        return doc or {}

    async def _download_backwards(self, d: tuple) -> None:
        start, _ = d
        self._back_start = start
        self._back_done = False
        cursor = ""

        while not self._back_done:
            self.url = self._build_list_url("DESC", cursor)
            self.html = await self._download()
            if not isinstance(self.html, dict) or not self.html.get("results"):
                logger.info("No results")
                break

            await self._process_html()
            if self._back_done or not self.html.get("hasMore"):
                logger.info("Backscrape done")
                break

            cursor = self.html.get("nextCursor") or ""
            if not cursor:
                logger.info("No cursor")
                break

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Build a single (start, end) tuple from kwargs.

        We paginate by cursor inside _download_backwards rather than by
        calendar windows, so a single tuple is enough.
        """
        start_str = kwargs.get("backscrape_start")
        end_str = kwargs.get("backscrape_end")
        start = (
            datetime.strptime(start_str, "%Y/%m/%d").date()
            if start_str
            else self.first_opinion_date.date()
        )
        end = (
            datetime.strptime(end_str, "%Y/%m/%d").date()
            if end_str
            else date.today()
        )
        self.back_scrape_iterable = [(start, end)]

    def extract_from_text(self, scraped_text: str) -> dict:
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

        result = {}
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            if "County," in lower_court:
                lower_court = lower_court.split("County")[0] + "County"

            result["Docket"] = {
                "appeal_from_str": lower_court,
            }

            if match := judge_pattern.search(scraped_text):
                lower_court_judge = re.sub(
                    r"\s+", " ", match.group("judge")
                ).strip()
                result["OriginatingCourtInformation"] = {
                    "assigned_to_str": lower_court_judge
                }

        return result
