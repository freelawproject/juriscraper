"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2014-07-04: Created by Andrei Chelaru, reviewed by mlr.
 2015-10-23: Parts rewritten by mlr.
 2016-05-04: Updated by arderyp to handle typos in docket string format
 2024-09-05: Updated by flooie to deal with block from main website
 2025-10-27: Updated by quevon24 to fix content cleanup
"""

import re
from datetime import date, timedelta
from typing import Any, Optional
from urllib.parse import urljoin

import nh3
from lxml.html import fromstring, tostring

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import set_api_token_header
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30
    court_id_map = {
        "Court of Appeals": "1",
        "App Div, 1st Dept": "3",
        "App Div, 2d Dept": "4",
        "App Div, 3d Dept": "5",
        "App Div, 4th Dept": "6",
        "Appellate Term, 1st Dept": "7",
        "Appellate Term, 2d Dept": "8",
    }

    base_url = "https://iapps.courts.state.ny.us/lawReporting/Search"
    court = "Court of Appeals"
    empty_result_messages = {"No results found."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self._set_parameters()
        self.expected_content_types = ["application/pdf", "text/html"]
        self.make_backscrape_iterable(kwargs)
        set_api_token_header(self)

    def _set_parameters(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> None:
        """Set the parameters for the POST request.

        If no start or end dates are given, scrape last month.
        This is the default behaviour for the present time scraper

        :param start_date:
        :param end_date:

        :return: None
        """
        self.method = "POST"

        if not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

        self.parameters = {
            "eSearchType": "0",
            "strPartyNames": "",
            "ePartyNameType": "0",
            "oStartDate": start_date.strftime("%m/%d/%Y"),
            "oEndDate": end_date.strftime("%m/%d/%Y"),
            "oCourt": self.court_id_map[self.court],
            "strDocketNumber": "",
            "wmcJudge:strJudge": "",
            "strSlipYear": "",
            "strSlipNumber": "",
            "wmcCitation:strVolume": "",
            "wmcCitation:eReporter": "",
            "wmcCitation:strPage": "",
            "strFullText": "",
            "eFullTextType": "0",
            "btnSubmit": "",
        }

    async def _download(self, request_dict=None):
        """Override to handle Wicket's session-based form submission.

        Wicket requires a GET to the search page first to establish a
        session and obtain the dynamic form action URL, then POST to it.
        """
        if self.test_mode_enabled():
            return await super()._download(request_dict)

        # Step 1: GET the search page to establish session
        self.method = "GET"
        html = await super()._download(request_dict)

        # Step 2: Extract the form action URL
        form_action = html.xpath("//form/@action")
        if not form_action:
            logger.warning("Could not find form action URL")
            return html

        action_url = urljoin(self.base_url, form_action[0])

        # Step 3: POST to the form action URL
        self.method = "POST"
        self.url = action_url
        return await super()._download(request_dict)

    def _process_html(self):
        table = self.html.xpath('.//table[contains(@class, "table")]')
        if not table:
            logger.warning("No results table found.")
            return

        rows = table[0].xpath(".//tbody/tr")
        # Empty-result responses render a single placeholder row whose only
        # cell contains one of the strings below. Treat as normal empty
        # result rather than logging an error per row. Wording is shared
        # across all NY courts using this backend; extend the set if the
        # site ever introduces a new variant.
        if len(rows) == 1:
            only_cells = rows[0].xpath("./td")
            if len(only_cells) == 1:
                placeholder = only_cells[0].text_content().strip()
                if placeholder in self.empty_result_messages:
                    logger.info("%s: no results in date range", self.court_id)
                    return

        for row in rows:
            cells = row.xpath("./td")
            if len(cells) < 9:
                logger.error(
                    "%s: expected 9 cells, got %s", self.court_id, len(cells)
                )
                continue

            url = cells[6].xpath(".//a/@href")
            if not url:
                logger.error("%s: no url found for row", self.court_id)
                continue

            slip_cite = cells[6].xpath(
                './/a/span[not(contains(@class, "visually-hidden"))]/text()'
            )
            slip_cite = slip_cite[0].strip() if slip_cite else ""
            official_citation = cells[4].text_content().strip()
            status = "Unpublished" if "(U)" in slip_cite else "Published"
            docket = cells[2].text_content().strip()
            author = cells[7].text_content().strip()
            case = {
                "name": cells[0].text_content().strip(),
                "date": cells[1].text_content().strip(),
                "url": url[0],
                "status": status,
                "docket": docket,
                "citation": official_citation,
                "parallel_citation": slip_cite,
                "author": "",
                "per_curiam": False,
            }

            # Because P E R C U R I A M, PER CURIAM, and Per Curiam
            pc = re.sub(r"\s", "", author.lower())
            if "percuriam" in pc:
                case["per_curiam"] = True
            elif author:
                cleaned_author = normalize_judge_string(author)[0]
                if cleaned_author.endswith(" J."):
                    cleaned_author = cleaned_author[:-3]
                case["author"] = cleaned_author
            self.cases.append(case)

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Can we extract the docket number from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        dockets = re.search(
            r"^<br>(?P<docket_number>No\. \d+(\s+SSM \d+)?)\s?$",
            scraped_text[:2000],
            re.MULTILINE,
        )
        if dockets:
            return {"Docket": dockets.groupdict()}
        return {}

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self._set_parameters(*dates)
        self.html = await self._download()
        self._process_html()

    @staticmethod
    def cleanup_content(content: bytes) -> bytes:
        """Remove hash altering timestamps to prevent duplicates

        Previously we've been more targeted about removing a href's but
        doctor will strip them out anyway so we should just clean our html
        content here.

        :param content: downloaded content `r.content`
        :return: content without hash altering elements
        """
        try:
            html_str = content.decode("utf-8")
        except UnicodeDecodeError:
            return content

        if not nh3.is_html(html_str):
            return content

        # remove a tags
        allowed = set(nh3.ALLOWED_TAGS)
        allowed.discard("a")

        cleaned = nh3.clean(html_str, tags=allowed)

        tree = fromstring(cleaned)
        normalized_html = tostring(tree, encoding="unicode", method="html")

        return normalized_html.encode()

    @staticmethod
    def clean_docket_match(match: re.Match) -> str:
        """Clean a docket number extracted from text

        :param match: a Match object with a named group
        :return: cleaned docket number
        """
        docket_number = match.group("docket_number")
        docket_number = re.sub(r"(\||\n|<br>)", "; ", docket_number)
        return re.sub("[\\s\n]+", " ", docket_number.strip("; ()"))
