"""Scraper for the Alaska Supreme Court
CourtID: alaska
Court Short Name: Alaska

History:
    - 2010-07-23: Original
    - 2026-06-22: Migrated to the Westlaw-hosted "Alaska Case Law Service",
      after the court moved its opinions there (issue #2009)

Notes:
    Both the Supreme Court and the Court of Appeals are published on the same
    Westlaw site (https://govt.westlaw.com/akcases). A single search returns
    opinions from both courts; they are told apart by the court label in each
    result's description line ("Alaska" vs "Alaska App."). The Court of Appeals
    scraper (alaskactapp) subclasses this one and overrides `court_label`.
"""

import re
from datetime import date, timedelta
from html import unescape
from urllib.parse import urlencode, urljoin

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://govt.westlaw.com/akcases/"
    # Court label as rendered in each result's description line. Subclasses
    # override this to scrape a different court from the same result feed.
    court_label = "Alaska"

    # Oldest opinions on the site date back to 1960
    first_opinion_date = date(1960, 1, 1)
    days_interval = 30

    # The BrowserHawk capability gate only checks that this cookie is present,
    # not its value (it normally encodes browser plugin detection results).
    browserhawk_cookie = "bhab=1&bhav=11"

    # Regexes for parsing a result's description line, e.g.:
    # "Not Reported in Pac. Rptr., 2026 WL 1746651, Alaska App., June 17, 2026 (NO. A-14271)"
    court_regex = re.compile(
        r",\s*(Alaska(?: App\.)?),\s+[A-Z][a-z]+ \d{1,2}, \d{4}"
    )
    date_regex = re.compile(r"[A-Z][a-z]+ \d{1,2}, \d{4}")
    docket_regex = re.compile(r"\(NO\.\s*([^)]+)\)")
    # Unpublished opinions are flagged "Not Reported in Pac. Rptr."; published
    # ones carry a Pacific Reporter citation (real, or the "--- P.3d ----"
    # placeholder)
    unpublished_regex = re.compile(r"Not Reported")
    published_regex = re.compile(r"P\.\d+d")
    westlaw_citation_regex = re.compile(r"\d{4} WL \d+")
    reporter_citation_regex = re.compile(r"\d+ P\.\d+d \d+")
    # Party designations stripped from the case name, including the surrounding
    # comma and trailing punctuation, so "X, Appellant, v. Y" -> "X v. Y"
    party_roles_regex = re.compile(
        r",?\s*\b(?:Cross[- ])?(?:Appellants?|Appellees?|Petitioners?|"
        r"Respondents?|Plaintiffs?|Defendants?|Cross-Petitioners?|"
        r"Cross-Respondents?)\b[.,]?",
        re.I,
    )
    whitespace_regex = re.compile(r"\s+")
    # Document id within a result link, e.g. "/Document/I454c96d0..."
    document_id_regex = re.compile(r"/Document/(I[0-9A-Fa-f]+)")
    # Canonical results URL embedded in a BrowserHawk interstitial
    interstitial_regex = re.compile(r"url='([^']*Results[^']*bhjs=0[^']*)'")
    # Per-request tokens stripped from document URLs for a stable content hash
    volatile_token_regex = re.compile(
        r"(?:&amp;|&)(?:ppcid|uniqueId)=[^&\"'<>]*"
    )
    # Lower court (and judge) in the opinion text, used by extract_from_text
    lower_court_regex = re.compile(
        r"""
        (?:
            Appeals?\s+from\s+the\s+|
            Appeals\s+in\s+File\s+Nos\.\s+S-\d+(?:/\d+)?\s+from\s+the\s+|
            Petitions?\s+for\s+Review\s+from\s+the\s+|
            Petition\s+for\s+Hearing\s+from\s+the\s+|
            Certified\s+(?:Original\s+Application\s+for\s+Relief\s+and\s+Jurisdiction\s+Transfer|Question)\s+from\s+the\s+
        )
        (?P<lower_court>.*?)(?=Judge\.|\n\s*\n)
        """,
        re.X | re.DOTALL,
    )
    # Lower court docket number, e.g. "Superior Court No. 3AN-19-05436 CI" or
    # "Superior Court Nos. 1JU-22-00038/54 CN"; appears next to the lower court
    lower_court_number_regex = re.compile(
        r"(?:Superior|District) Court Nos?\.?:?\s*"
        r"(\d[A-Z]{2}-\d{2}-\d{3,6}(?:/\d+)?\s+[A-Z]{2})"
    )
    # Panel of judges from the "Before:" line, e.g.
    # "Before: Carney, Chief Justice, and Borghesan, ... Oravec, Justices."
    # The panel ends at the "Justices."/"Judges." role; any bracketed
    # "not participating" judge that follows is intentionally excluded.
    panel_regex = re.compile(
        r"Before:\s*(?P<panel>.*?)\s*(?:Justices?|Judges?)\.", re.DOTALL
    )
    # Inline titles to drop from the panel, e.g. ", Chief Justice"
    panel_title_regex = re.compile(
        r",?\s*(?:Chief\s+)?(?:Justices?|Judges?)\b"
    )
    # Split the panel into individual judges on commas and "and"
    panel_split_regex = re.compile(r",|\s+and\s+")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=self.days_interval)
        # A browser User-Agent is required to pass the site's bot management
        self.request["headers"]["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # Opinions are served as HTML documents, not PDFs
        self.expected_content_types = ["text/html"]
        self.make_backscrape_iterable(kwargs)
        self.url = self._build_search_url()

    async def _process_html(self) -> None:
        self._parse_results_page(self.html)
        if self.test_mode_enabled():
            return
        while next_url := self._next_page_url():
            self.html = await self._get_html_tree_by_url(next_url)
            self._parse_results_page(self.html)

    def _parse_results_page(self, tree) -> None:
        """Parse one results page, keeping only this court's opinions.

        Each result is an ``<li>`` with the case name in an ``a.resultLink``
        and a description line carrying citation, court, date and docket, e.g.:
        "Not Reported in Pac. Rptr., 2026 WL 1746651, Alaska App.,
        June 17, 2026 (NO. A-14271)"

        :param tree: the lxml tree of a results page
        """
        for row in tree.xpath("//ol[@id='results']/li"):
            anchor = row.xpath(".//a[@class='resultLink']")
            description = row.xpath(
                ".//div[@class='co_resultsListDescription']/text()"
            )
            if not anchor or not description:
                logger.warning(
                    "%s: skipping result row with unexpected structure: %s",
                    self.court_id,
                    row.text_content().strip(),
                )
                continue
            description = description[0].strip()

            # A single search returns both Alaska courts; skip the other one
            court = self.court_regex.search(description)
            if not court or court.group(1) != self.court_label:
                continue

            # Date and docket are required; everything else is best-effort
            date_match = self.date_regex.search(description)
            docket_match = self.docket_regex.search(description)
            if not date_match or not docket_match:
                logger.error(
                    "%s: incomplete metadata, skipping row '%s'",
                    self.court_id,
                    description,
                )
                continue

            # Precedential status from the reporter field
            if self.unpublished_regex.search(description):
                status = "Unpublished"
            elif self.published_regex.search(description):
                status = "Published"
            else:
                status = "Unknown"

            # Citations are passed through as-is for CourtListener to parse,
            # preferring the official Pacific Reporter cite over the Westlaw one
            reporter = self.reporter_citation_regex.search(description)
            westlaw = self.westlaw_citation_regex.search(description)
            if reporter:
                citation = reporter.group(0)
                parallel_citation = westlaw.group(0) if westlaw else ""
            elif westlaw:
                citation, parallel_citation = westlaw.group(0), ""
            else:
                citation, parallel_citation = "", ""

            # Case name: drop party-role designations and normalize casing
            name = self.party_roles_regex.sub("", anchor[0].text_content())
            name = self.whitespace_regex.sub(" ", name).strip(" .")

            # Build a clean, downloadable document URL from the result link
            doc_id = self.document_id_regex.search(anchor[0].get("href"))
            url = urljoin(
                self.base_url,
                f"Document/{doc_id.group(1)}?"
                + urlencode({"viewType": "FullText", "bhcp": "1"}),
            )

            self.cases.append(
                {
                    "name": titlecase(name),
                    "url": url,
                    "date": date_match.group(0),
                    "docket": docket_match.group(1).strip(),
                    "status": status,
                    "citation": citation,
                    "parallel_citation": parallel_citation,
                }
            )

    def cleanup_content(self, content: bytes) -> str | bytes:
        """Isolate the opinion from the surrounding Westlaw site chrome.

        Deletes hash altering content

        :param content: the raw document page bytes
        :return: the opinion document HTML, or the original content if the
            expected container is missing
        """
        tree = html.fromstring(content)
        nodes = tree.xpath("//*[@id='co_document']")
        if not nodes:
            return content
        cleaned = html.tostring(nodes[0], encoding="unicode")

        # Strip per-request tokens from embedded image/link URLs so the
        # content hash is stable across downloads (CL dedupes on hash) #2009
        return self.volatile_token_regex.sub("", cleaned)

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Configure the date window for a historical range and download.

        :param dates: (start_date, end_date) tuple
        """
        self.start_date, self.end_date = dates
        logger.info(
            "Backscraping for range %s %s", self.start_date, self.end_date
        )
        self.html = await self._download()
        await self._process_html()

    def _build_search_url(self) -> str:
        """Build a Word-template search URL bounding the opinion date range.

        Westlaw's `aft`/`bef` date connectors are exclusive, so widen the
        window by a day on each end to make ``[start_date, end_date]``
        inclusive. A query term is required because the site rejects
        date-only searches; "court" appears in virtually all opinions.

        :return: the absolute search URL
        """
        after = self.start_date - timedelta(days=1)
        before = self.end_date + timedelta(days=1)
        query = (
            f"court & da(aft {after.month}/{after.day}/{after.year}"
            f" & bef {before.month}/{before.day}/{before.year})"
        )
        params = {
            "t_querytext": query,
            "t_Method": "TNC",
            "Template": "Word",
            "Submit": "Search",
        }
        return (
            f"{urljoin(self.base_url, 'Search/Results')}?{urlencode(params)}"
        )

    async def _download(self, request_dict=None):
        """Bootstrap a session and fetch the first results page.

        The site sits behind a BrowserHawk capability gate. We seed cookies by
        loading the index, inject the capability cookie, then request the
        search. The first search hit may return a "click to continue"
        interstitial that embeds the canonical results URL (with a
        server-generated SearchId); if so, we follow it.
        """
        if self.test_mode_enabled():
            return await super()._download(request_dict)

        await self._request_url_get(urljoin(self.base_url, "Index"))
        self.request["session"].cookies.set(
            "bhResults",
            self.browserhawk_cookie,
            domain="govt.westlaw.com",
            path="/",
        )

        self.url = self._build_search_url()
        await self._request_url_get(self.url)
        if "click here to continue" in self.request["response"].text.lower():
            self.url = self._follow_interstitial(self.request["response"].text)
            await self._request_url_get(self.url)

        self._post_process_response()
        return self._return_response_text_object()

    def _follow_interstitial(self, text: str) -> str:
        """Extract the canonical results URL from a BrowserHawk interstitial.

        :param text: the interstitial page HTML
        :return: the absolute canonical results URL
        """
        match = self.interstitial_regex.search(text)
        if not match:
            raise ValueError(
                f"{self.court_id}: could not parse BrowserHawk interstitial"
            )
        url = unescape(match.group(1)).replace("bhjs=0", "bhcp=1")
        return urljoin(self.base_url, url)

    def _next_page_url(self) -> str | None:
        """Return the absolute URL of the next results page, if any."""
        links = self.html.xpath(
            "//a[contains(., 'Next set of documents')]/@href"
        )
        return links[0] if links else None

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract the lower court (and its judge) from the opinion text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        metadata = {}

        lower_court_str = ""
        if match := self.lower_court_regex.search(scraped_text):
            lower_court_str = self.whitespace_regex.sub(
                " ", match.group("lower_court")
            ).strip()

        if lower_court_str:
            parts = [part.strip() for part in lower_court_str.split(",")]
            if "appeals" in parts[0].lower():
                lower_court = parts[0]
            else:
                lower_court = ", ".join(parts[:2])
            # Handle judge name, including cases like "Jr."
            lower_court_judge = None
            if len(parts) > 1:
                lower_court_judge = parts[-2]
                if lower_court_judge == "Jr." and len(parts) > 2:
                    lower_court_judge = f"{parts[-3]} Jr."

            metadata["Docket"] = {"appeal_from_str": lower_court}
            if lower_court_judge:
                metadata.setdefault("OriginatingCourtInformation", {})[
                    "assigned_to_str"
                ] = lower_court_judge

        # The lower court docket number sits right beside the lower court
        if number_match := self.lower_court_number_regex.search(scraped_text):
            lower_court_number = self.whitespace_regex.sub(
                " ", number_match.group(1)
            ).strip()
            metadata.setdefault("OriginatingCourtInformation", {})[
                "docket_number"
            ] = lower_court_number

        # The panel of judges from the "Before:" line
        if panel_match := self.panel_regex.search(scraped_text):
            panel = self.panel_title_regex.sub("", panel_match.group("panel"))
            judges = [
                judge.strip(" .,")
                for judge in self.panel_split_regex.split(panel)
                if judge.strip(" .,")
            ]
            if judges:
                metadata.setdefault("OpinionCluster", {})["judges"] = (
                    ", ".join(judges)
                )

        return metadata
