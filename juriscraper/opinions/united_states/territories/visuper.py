# Scraper for Superior Court of the Virgin Islands
# CourtID: visuper

# History:
#   2023-12-11: Created as visuper_p - Garza
#   2024-01-15: Updated - Rossi
#   2025-07-09: Fixed - luism
#   2026-05-08: Migrated to new public portal API; merged visuper_p and
#               visuper_u into a single visuper scraper (#1945) - grossir

# The new portal serves both published and unpublished opinions from a single
# `/courts/cms/publications` endpoint with no server-side filter to split them,
# so this scraper emits every publication and derives the per-row status from
# the data itself.


import re
from datetime import date
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # https://usvipublicportal.vicourts.org/portal/search/publication
    base_url = "https://usvipublicportal-api.vicourts.org"
    # USVI Superior Court. Supreme Court also available in this portal
    court_uuid = "87edff36-c02b-4073-aea4-c0652bc123d9"

    # 1 + page_size requests per scrape
    # this seems to be a low-volume court, let's be gentle with the site
    # Backscraper bumps `size` to `backscrape_page_size`.
    page_size = 5
    backscrape_page_size = 50

    # Portal launched with these publications in late 2025.
    first_opinion_date = date(2025, 12, 1)
    days_interval = 30

    citation_split_re = re.compile(
        r"^\s*(?P<cite>\d{4}\s+V\.?I\.?\s+Super\.?\s+\d+\s*U?)\s*-\s*(?P<name>.+)$",
        re.I,
    )
    signed_date_re = re.compile(
        r"signed\s+by\s+.*?\s+on\s+(?P<signed>[A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        re.I,
    )

    # publicationNote: "...UNPUBLISHED MEMORANDUM OPINION..." or "...Published
    # Memorandum Opinion..." — case mixed, but always one of the two words.
    note_status_re = re.compile(r"\b(?P<status>(?:un)?published)\b", re.I)

    # publicationName: "2026 VI Super 15U-..." (unpublished) vs
    # "2026 VI Super 14 -..." (published). The U suffix is the marker.
    name_status_re = re.compile(
        r"\bV\.?I\.?\s*Super\.?\s*\d+(?P<u>\s*U)?\b", re.I
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}/courts/cms/publications"
        self.request["parameters"]["params"] = {
            "courtID": self.court_uuid,
            "page": 0,
            "size": self.page_size,
            "sort": "publicationDate,desc",
        }
        self.should_have_results = True
        self.make_backscrape_iterable(kwargs)

    async def _process_html(self) -> None:
        """Parse the publication list and fetch each publication's detail.

        :return None
        """
        for pub in self.html.get("_embedded", {}).get("results", []):
            if self.test_mode_enabled() and "detailJson" in pub:
                detail = pub["detailJson"]
            else:
                detail = await self._get_detail(pub["publicationUUID"])

            if not detail or not detail.get("publicationItems"):
                logger.warning(
                    "visuper: no detail for publication %s",
                    pub["publicationUUID"],
                )
                continue

            items = sorted(
                detail["publicationItems"],
                key=lambda it: it.get("orderBy") or 0,
            )
            first = items[0]
            if not first.get("documents"):
                logger.error(
                    "visuper: no document for publication %s",
                    pub["publicationUUID"],
                )
                continue

            note = detail.get("publicationNote") or ""
            citation, name = self._split_citation_name(pub["publicationName"])
            date_filed, approximate = self._extract_date(
                note, pub["publicationDate"]
            )
            doc_link = first["documents"][0]["documentLinkUUID"]
            url = urljoin(
                self.base_url,
                f"/courts/{self.court_uuid}/cms/case/"
                f"{first['caseInstanceUUID']}/docketentrydocuments/"
                f"{doc_link}",
            )

            self.cases.append(
                {
                    "name": titlecase(name or first.get("title") or ""),
                    "date": date_filed,
                    "date_filed_is_approximate": approximate,
                    "docket": ", ".join(
                        it["caseNumber"]
                        for it in items
                        if it.get("caseNumber")
                    ),
                    "url": url,
                    "judge": self._clean_judge(first.get("groupName") or ""),
                    "citation": citation,
                    "disposition": (first.get("decision") or "").strip(" ,"),
                    "status": self._derive_status(
                        note, pub["publicationName"]
                    ),
                }
            )

    async def _get_detail(self, publication_uuid: str) -> dict:
        """Fetch a publication detail document.

        :param publication_uuid: publicationUUID from the list response
        :return: parsed JSON detail document
        """
        url = urljoin(
            self.base_url,
            f"/courts/{self.court_uuid}/cms/publication/{publication_uuid}",
        )
        logger.debug("visuper: fetching detail %s", url)
        await self._request_url_get(url)
        self._post_process_response()
        return self._return_response_text_object()

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Filter the publication list by `publicationDate` and process the
        first page of results.

        Single page request — if the interval has more publications than
        `backscrape_page_size`, log a warning so the operator can shrink
        the date range and re-run.

        :param dates: (start, end) date pair from `make_backscrape_iterable`
        :return None
        """
        start, end = dates
        logger.info("visuper: backscrape %s to %s", start, end)
        params = self.request["parameters"]["params"]
        params["size"] = self.backscrape_page_size
        params["page"] = 0
        params["publicationDateFrom"] = f"{start.isoformat()}T00:00:00Z"
        params["publicationDateTo"] = f"{end.isoformat()}T23:59:59Z"
        self.html = await self._download()

        total = (self.html or {}).get("page", {}).get("totalElements") or 0
        if total > self.backscrape_page_size:
            logger.warning(
                "visuper: %s publications in %s..%s exceed page size %s; "
                "shrink --backscrape-start/--backscrape-end and rerun to "
                "fetch the rest",
                total,
                start,
                end,
                self.backscrape_page_size,
            )

        await self._process_html()

    @classmethod
    def _derive_status(cls, note: str, publication_name: str) -> str:
        """Derive precedential status for a publication.

        Prefer the explicit Published / Unpublished word from publicationNote
        (set in the signing record), and fall back to the U-suffix on the
        citation in publicationName when the note is missing or malformed.

        :param note: publicationNote (free text); may be empty
        :param publication_name: e.g. "2026 VI Super 15U- ..."
        :return: "Published", "Unpublished", or "Unknown"
        """
        if match := cls.note_status_re.search(note):
            word = match.group("status").lower()
            return "Unpublished" if word == "unpublished" else "Published"

        if match := cls.name_status_re.search(publication_name):
            return "Unpublished" if match.group("u") else "Published"

        logger.warning(
            "visuper: could not derive status from note=%r name=%r",
            note,
            publication_name,
        )
        return "Unknown"

    @classmethod
    def _split_citation_name(cls, publication_name: str) -> tuple[str, str]:
        """Split publicationName into (citation, case name).

        :param publication_name: e.g. "2026 VI Super 14 - People of..."
        :return: (citation, name); citation is "" if the format is unexpected
        """
        if match := cls.citation_split_re.match(publication_name):
            return match.group("cite").strip(), match.group("name").strip()
        return "", publication_name.strip()

    @classmethod
    def _extract_date(
        cls, note: str, publication_date: str
    ) -> tuple[str, bool]:
        """Extract the signed date from publicationNote, falling back to the
        upload date with the approximate flag set.

        :param note: publicationNote (free text)
        :param publication_date: ISO timestamp of the upload
        :return: (date string, is_approximate)
        """
        if match := cls.signed_date_re.search(note):
            try:
                signed = convert_date_string(match.group("signed"))
                if signed:
                    return signed.strftime("%Y-%m-%d"), False
            except (ValueError, TypeError):
                pass
            logger.warning(
                "visuper: could not parse signed date '%s'",
                match.group("signed"),
            )
        return publication_date[:10], True

    @staticmethod
    def _clean_judge(value: str) -> str:
        """Strip the "Hon." prefix from groupName.

        :param value: raw judge string
        :return: cleaned judge string
        """
        return re.sub(r"^Hon\.?\s+", "", value).strip()
