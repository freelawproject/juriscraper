"""Scraper for Nevada Supreme Court
CourtID: nev
Court Short Name: Nev.

History:
    - 2023-12-13: Updated by William E. Palin
    - 2026-06-22: Reworked for the new Thomson Reuters ACIS portal, #2010
"""

import re
from datetime import date, datetime
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # Index https://nvcourts.gov/supreme/decisions
    base_url = "https://acis-api.nvcourts.gov/courts/cms/docketentrydocuments"
    document_url = "https://acis-api.nvcourts.gov/courts/{court}/cms/case/{case}/docketentrydocuments/{document}"

    # Court UUID in the ACIS portal; overridden by nevapp (Court of Appeals)
    court_uuid = "dc01122c-a19d-4eb7-bfe9-5b96e93c26fd"
    # "Opinion/Dispositional" docket entry type; covers authored opinions
    # (subtype 1000230) and per curiam opinions (subtype 1000234), both
    # published advance opinions
    opinion_type_id = "1000014"

    # Advance opinion citation, e.g. "142 Nev. Adv. Opn. No. 45". The "No."
    # is occasionally dropped in the source text, hence optional.
    citation_regex = re.compile(
        r"\d+\s+Nev\.\s+Adv\.\s+Opn?\.\s+(?:No\.)?\s*\d+"
    )
    # "Author: Cadish, J." / "Author: Herndon, C.J." / "Author: X, Chief Justice"
    # ("Author" is sometimes misspelled "Authur" and the colon is optional)
    author_regex = re.compile(
        r"Auth(?:or|ur):?\s*([A-Z][A-Za-z'\-]+,\s*(?:C\.?J\.?|J\.?|Chief Justice))"
    )
    # Disposition is quoted, e.g. '"Vacated and remanded."'
    disposition_regex = re.compile(r'"\s*([^"]+?)\s*"')
    # Panel, e.g. "Majority: Stiglich/Cadish/Lee"
    majority_regex = re.compile(r"Majority:\s*([A-Za-z/]+)")
    # Consolidated cases, e.g. "... C/W 85175" or "... C/W 88016/88190"
    consolidated_regex = re.compile(r"\s*\bC/W\s+([\d/,\s]+)")
    # Parentheticals that mark the case type rather than a party; these are
    # stripped from the case name. Party parentheticals such as "(State)" or
    # a person's name are kept.
    case_type_regex = re.compile(
        r"\s*\((?:CIVIL|CRIMINAL|CHILD CUSTODY|FAMILY|NRAP\s*\d+)\)",
        re.IGNORECASE,
    )

    days_interval = 30
    first_opinion_date = datetime(2000, 1, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.page_size = 25
        # Set during a backscrape to filter results to the requested window
        self.start_date = None
        self.end_date = None
        self.set_url()
        self.request["headers"].update(
            {
                "Accept": "application/json",
                "Referer": "https://acis.nvcourts.gov/",
            }
        )
        self.expected_content_types = ["application/pdf"]
        self.make_backscrape_iterable(kwargs)

    def set_url(self, page: int = 0) -> None:
        """Build the document-search API URL for a results page

        :param page: zero-indexed results page
        :return: None
        """
        params = {
            "docketEntryHeader.docketEntryTypeID": self.opinion_type_id,
            "caseHeader.courtID": self.court_uuid,
            "page": page,
            "size": self.page_size,
            "sort": "docketEntryHeader.filedDate,desc",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    async def _process_html(self) -> None:
        """Build cases from the document-search JSON feed

        The PDF link is built directly from the result, so no per-case
        request is needed. Opinion metadata (citation, disposition, author,
        panel) lives in the free-text docketEntryDescription and is parsed
        inline.

        :return: None
        """
        for result in self.html["_embedded"]["results"]:
            entry = result["docketEntryHeader"]
            header = result["caseHeader"]
            date_filed = entry["filedDate"][:10]

            # During a backscrape, keep only rows in the requested window
            if self.start_date:
                filed = datetime.strptime(date_filed, "%Y-%m-%d").date()
                if not (self.start_date <= filed <= self.end_date):
                    continue

            # Secured documents can't be downloaded; skip rather than ingest
            # an opinion with an unreachable URL
            if entry.get("securedDocument"):
                logger.warning(
                    "%s: skipping secured (non-downloadable) document for docket %s",
                    self.court_id,
                    header["caseNumber"],
                )
                continue

            name, consolidated = self.clean_name(header["caseTitle"])
            docket = header["caseNumber"]
            if consolidated:
                docket = f"{docket} c/w {consolidated}"

            case = {
                "name": name,
                "docket": docket,
                "date": date_filed,
                "url": self.document_url.format(
                    court=self.court_uuid,
                    case=header["caseInstanceUUID"],
                    document=result["documentLinkUUID"],
                ),
            }
            case.update(
                self.parse_description(entry.get("docketEntryDescription", ""))
            )
            self.cases.append(case)

    def clean_name(self, title: str) -> tuple[str, str]:
        """Clean the raw, upper-cased case title

        Removes the consolidated-docket suffix ("C/W ...") and case-type
        parentheticals ("(CIVIL)", "(CRIMINAL)", ...), while keeping
        party-name parentheticals such as "(State)" or "(Williams)".

        :param title: the raw caseTitle from the feed
        :return: (titlecased name, "c/w"-joined consolidated docket numbers)
        """
        consolidated = ""
        if match := self.consolidated_regex.search(title):
            consolidated = " c/w ".join(re.findall(r"\d+", match.group(1)))
            title = title[: match.start()]

        title = self.case_type_regex.sub("", title)
        return titlecase(title.strip()), consolidated

    def parse_description(self, description: str) -> dict:
        """Extract opinion metadata from the docket entry description

        Always returns the same keys (with empty/False defaults) so every
        case dict is consistent, which the OpinionSiteLinear getters require.

        :param description: the free-text docketEntryDescription
        :return: dict with citation, disposition, author, per_curiam and judge
        """
        metadata = {
            "citation": "",
            "disposition": "",
            "author": "",
            "per_curiam": False,
            "judge": "",
        }

        if match := self.citation_regex.search(description):
            # The source abbreviates the reporter as "Opn.", but official guidelines
            # https://nvsctlawlib.libguides.com/nvcitationguide/case-law
            # (and reporters-db) use "Op." ("Nev. Adv. Op. No."), so normalize
            metadata["citation"] = match.group(0).replace("Opn.", "Op.")

        if match := self.disposition_regex.search(description):
            metadata["disposition"] = match.group(1)

        if "per curiam" in description.lower():
            metadata["per_curiam"] = True
        elif match := self.author_regex.search(description):
            metadata["author"] = match.group(1)

        if match := self.majority_regex.search(description):
            # Some entries list clerk initials (e.g. "MG/BB/DW") instead of
            # justice surnames; keep only the surnames
            judges = [
                name
                for name in match.group(1).split("/")
                if len(name) >= 3 and not name.isupper()
            ]
            if judges:
                metadata["judge"] = ", ".join(judges)

        return metadata

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Collapse the default per-interval windows into a single range

        The ACIS API has no server-side date filter, so a backscrape pages
        through the whole date-sorted feed once and filters locally. There is
        no benefit to splitting the request into intervals.

        :param kwargs: backscrape arguments
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        start = self.back_scrape_iterable[0][0]
        end = self.back_scrape_iterable[-1][1]
        self.back_scrape_iterable = [(start, end)]

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Page through the date-sorted feed for a backscrape window

        Results are sorted by filed date descending, so we page until we pass
        the start of the requested window; _process_html filters each page.

        :param dates: (start_date, end_date)
        :return: None
        """
        self.start_date, self.end_date = dates
        self.page_size = 100
        logger.info("Backscraping for range %s %s", *dates)

        page = 0
        while True:
            self.set_url(page)
            self.html = await self._download()
            results = self.html["_embedded"]["results"]
            if not results:
                break

            await self._process_html()

            oldest = datetime.strptime(
                results[-1]["docketEntryHeader"]["filedDate"][:10], "%Y-%m-%d"
            ).date()
            if oldest < self.start_date:
                break
            page += 1
