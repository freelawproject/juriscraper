"""
Scraper template for the 'Other Courts' of the NY Reporter
Court Contact: phone: (518) 453-6900
Author: Gianfranco Rossi
History:
 - 2024-01-05, grossir: created
 - 2025-07-03, luism: make back scraping dynamic
"""

import re
from datetime import date
from typing import Any, Optional

from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import set_api_token_header
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.opinions.united_states.state import ny
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_regex: str  # to be defined on inheriting classes
    base_url = "https://nycourts.gov/reporter/slipidx/miscolo.shtml"
    first_opinion_date = date(2003, 12, 1)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.court_id = self.__module__
        self.url = self.build_url()

        self.make_backscrape_iterable(kwargs)
        self.expected_content_types = ["application/pdf", "text/html"]
        set_api_token_header(self)

    def build_url(self, target_date: Optional[date] = None) -> str:
        """URL as is loads most recent month page
        There is an URL for each month of each year back to Dec 2003

        :param target_date: used to extract month and year for backscraping
        :returns str: formatted url
        """
        if not target_date:
            return self.base_url

        end = f"_{target_date.year}_{target_date.strftime('%B')}.shtml"

        return self.base_url.replace(".shtml", end)

    def is_court_of_interest(self, court: str) -> bool:
        """'Other Courts' of NY Reporter consists of 10 different families of
        sources. Each family has an scraper that inherits from this class and
        defines a `court_regex` to capture those that belong to its family

        For example
        "Civ Ct City NY, Queens County" and "Civ Ct City NY, NY County"
        belong to nycivct family

        :param court: court name
        :return: true if court name matches
                family of courts of calling scraper
        """
        return bool(re.search(self.court_regex, court))

    def _process_html(self) -> None:
        """Parses a page's HTML into opinion dictionaries

        :return: None
        """
        row_xpath = "//table[caption]//tr[position()>1 and td]"
        for row in self.html.xpath(row_xpath):
            court = re.sub(
                r"\s+", " ", row.xpath("td[2]")[0].text_content()
            ).strip(", ")

            if not self.is_court_of_interest(court):
                logger.debug("Skipping %s", court)
                continue

            url = row.xpath("td[1]/a/@href")[0]
            name = harmonize(row.xpath("td[1]/a")[0].text_content())
            opinion_date = row.xpath("td[3]")[0].text_content()
            slip_cite = row.xpath("td[4]")[0].text_content()
            status = "Unpublished" if "(U)" in slip_cite else "Published"

            self.cases.append(
                {
                    "name": name,
                    "date": opinion_date,
                    "status": status,
                    "url": url,
                    "citation": slip_cite,
                    "child_court": court,
                    "docket": "",
                }
            )

    def _download_backwards(self, target_date: date) -> None:
        """Method used by backscraper to download historical records

        :param target_date: an element of self.back_scrape_iterable
        :return: None
        """
        self.url = self.build_url(target_date)

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Extract values from opinion's text

        The document may be a HTML or a PDF. We use different regexes for each

        :param scraped_text: pdf or html string contents
        :return: dict where keys match courtlistener model objects
        """
        metadata: dict[str, dict] = {
            "Citation": {},
            "Docket": {},
            "Opinion": {},
            "OpinionCluster": {},
        }
        target_text = scraped_text[:2000]
        is_html = "<br>" in target_text and "<table" in target_text
        if not is_html:
            # Most info is in a table at the start of the document
            if pdf_docket := re.search(
                r"\n\s*Docket Number:\s+(?P<docket_number>.+)\s*\n",
                target_text,
            ):
                metadata["Docket"]["docket_number"] = pdf_docket.group(
                    "docket_number"
                ).strip()
            elif pdf_docket := re.search(r"INDEX NO\. \d+/\d+", target_text):
                # fallback to docket number at the start of the second page
                # sometimes the header table does not exist
                metadata["Docket"]["docket_number"] = (
                    pdf_docket.group().strip()
                )
            else:
                logger.error(
                    "nytrial: unable to extract_from_text docket number",
                    extra={"pdf_text": target_text.strip()[:1024]},
                )

            if pdf_judge := re.search(
                r"\n\s*Judge:\s+(?P<judge>.+)\s*\n", target_text
            ):
                metadata["Opinion"]["author_str"] = pdf_judge.group(
                    "judge"
                ).strip()

            return {k: v for k, v in metadata.items() if v}

        # HTML processing
        # Index No. E2024006644
        # Index No. 654864/2023
        # Index No. EF2019-67433
        # Index No. LT-0926-23
        # 00452-04
        # Index No.: 119635/03
        target_text = clean_string(target_text)
        docket_regexes = [
            re.compile(
                r"<br>[\s\n]*(?P<docket_number>(Case|Claim|Docket|Index|File|Indictment|Ind\.) No\.?:? [\d ,/A-Z&\[\]-]+)[\s\n]*(<br>|Appearances)",
                flags=re.IGNORECASE,
            ),
            re.compile(
                r"<br>[\s\n]*(?P<docket_number>[A-Z/0-9-]*\d[A-Z/0-9-]*)[\s\n]*<br>"
            ),
        ]
        for regex in docket_regexes:
            if docket_match := regex.search(target_text):
                docket = docket_match.group("docket_number").strip()
                # avoid censored docket numbers
                # https://www.courtlistener.com/opinion/9500907/xx/
                if "XXX" not in docket:
                    metadata["Docket"]["docket_number"] = docket

        # found on the header table inside brackets "[111 Misc 3d 222]" May have
        # extra symbols next to the page value, such as [A]
        if cite_match := re.search(
            r"(?<=\[)\d+ Misc 3d\s+[\S]+(?=\])", target_text
        ):
            metadata["Citation"] = cite_match.group(0)

        # found on the header table
        judge = ""
        judge_regexes = [
            re.compile(r"(?P<judge>[\s\w\.,-]+), C?[JS]\.?</td>"),
            re.compile(
                r"<br>[\s\n]*(?P<judge>[ \w\.,-]+), C?J\.?[\s\n]*(<br>|<p)"
            ),
        ]
        judge_matches = [
            regex.search(target_text)
            for regex in judge_regexes
            if regex.search(target_text)
        ]
        if len(judge_matches) == 2:
            # last name is in full name
            if judge_matches[0].group("judge") in judge_matches[-1].group(
                "judge"
            ):
                judge = judge_matches[-1].group("judge")
            else:
                judge = judge_matches[0].group("judge")
        elif judge_matches:
            judge = judge_matches[0].group("judge")

        if judge:
            metadata["Opinion"] = {
                "author_str": normalize_judge_string(judge)[0]
            }

        # found on a table after the summary table
        full_case = ""
        # replace <br> with newlines because text_content() replaces <br>
        # with whitespace. If not, case names would lack proper separation
        scraped_text = scraped_text.replace("<br>", "\n")
        full_case = fromstring(scraped_text).xpath("//table")
        full_case = full_case[1].text_content() if len(full_case) > 1 else ""
        if full_case:
            full_case = harmonize(full_case)
            metadata["Docket"]["case_name_full"] = full_case
            metadata["OpinionCluster"]["case_name_full"] = full_case

        return {k: v for k, v in metadata.items() if v}

    @staticmethod
    def cleanup_content(content: str) -> str:
        return ny.Site.cleanup_content(content)

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
