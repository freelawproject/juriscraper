"""
Scraper template for the 'Other Courts' of the NY Reporter
Court Contact: phone: (518) 453-6900
Author: Gianfranco Rossi
History:
 - 2024-01-05, grossir: created
 - 2025-07-03, luism: make back scraping dynamic
 - 2026-09-29, renatodvc: use the new "current/index" pages; parse the new
   opinion template
"""

import re
from datetime import date
from typing import Any

from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import set_api_token_header
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.exceptions import ParsingException
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.opinions.united_states.state import ny
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

citation_regex = r"(?<=\[)\d+ Misc 3d\s+[\S]+(?=\])"


class Site(OpinionSiteLinear):
    court_regex: str  # to be defined on inheriting classes
    base_url = "https://nycourts.gov/reporter/current/index/miscolo.shtml"
    # month pages from this date on live in "current/index", older ones in
    # "slipidx"
    current_index_start = date(2026, 5, 1)
    first_opinion_date = date(2003, 12, 1)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.court_id = self.__module__
        self.url = self.build_url()

        self.make_backscrape_iterable(kwargs)
        self.expected_content_types = ["application/pdf", "text/html"]
        set_api_token_header(self)

    def build_url(self, target_date: date | None = None) -> str:
        """URL as is loads most recent month page
        There is an URL for each past month of each year back to Dec 2003.
        The current month only exists as the base URL

        :param target_date: used to extract month and year for backscraping
        :returns str: formatted url
        """
        today = date.today()
        if not target_date or (target_date.year, target_date.month) == (
            today.year,
            today.month,
        ):
            return self.base_url

        url = self.base_url
        if target_date < self.current_index_start:
            url = url.replace("/current/index/", "/slipidx/")
        month = target_date.strftime("%B").lower()

        return url.replace(".shtml", f"_{target_date.year}_{month}.shtml")

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
        # a missing page is served with a 200 status code
        title = self.html.xpath("string(//title)")
        if "404 ERROR" in title:
            raise ParsingException(f"nytrial: page not found {self.url}")

        row_xpath = "//table[caption]//tr[position()>1 and td]"
        for row in self.html.xpath(row_xpath):
            court = re.sub(
                r"\s+", " ", row.xpath("td[2]")[0].text_content()
            ).strip(", ")

            if not self.is_court_of_interest(court):
                logger.debug("Skipping %s", court)
                continue

            url = row.xpath("td[1]/a/@href")[0]
            # republished decisions ("30000" slip op numbers) link to a stub
            # page that only links to the PDF
            url = re.sub(
                r"/current/3dseries/(\d{4})/(\d{4}_3\d{4})\.shtml$",
                r"/pdfs/\1/\2.pdf",
                url,
            )
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

    async def _download_backwards(self, target_date: date) -> None:
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
        if "<h1>" in target_text:
            return self.extract_from_current_template(scraped_text)

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
        if cite_match := re.search(citation_regex, target_text):
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
    def extract_from_current_template(scraped_text: str) -> dict[str, Any]:
        """Extract values from the opinion template used since April 2026

        The header is a <div> with the <h1> case name, the slip opinion and
        Misc 3d citations, the court and the judge. It is followed by the
        parties <div>, the court <p>, the "Decided on" <p> and the docket <p>

        :param scraped_text: html string contents, after cleanup_content
        :return: dict where keys match courtlistener model objects
        """
        metadata: dict[str, dict] = {
            "Citation": {},
            "Docket": {},
            "Opinion": {},
            "OpinionCluster": {},
        }
        tree = fromstring(scraped_text)
        header = tree.xpath("//h1/parent::div")
        if not header:
            return {}

        header_lines = [
            clean_string(p.text_content()) for p in header[0].xpath("./p")
        ]
        if cite_match := re.search(citation_regex, " ".join(header_lines)):
            metadata["Citation"] = cite_match.group(0)

        judge_regex = re.compile(
            r"(?P<judge>[^,]+(, (Jr|Sr|II|III)\.?)?), (J|S|C\.?J|A\.?J|J\.H\.O|J\.S\.C|Ref)\.?(\s*\(.*\))?"
        )
        for line in header_lines:
            if judge_match := judge_regex.fullmatch(line):
                metadata["Opinion"]["author_str"] = normalize_judge_string(
                    judge_match.group("judge")
                )[0]
                break

        decided = tree.xpath(
            "//p[starts-with(normalize-space(), 'Decided on')]"
        )
        if not decided:
            return {k: v for k, v in metadata.items() if v}

        # Index No. L&T 305703/25, L&T Index No. 316192-25/QU,
        # CR-004361-26NY, IND 70036-25, 2017KN054132, 00452-04
        docket_regex = re.compile(
            r".{0,12}\b(Case|Claim|Docket|Index|File|Indictment|Ind\.?|IND)\b.*|[A-Z]{1,4}[- ]?[\dX][\w/&. -]*|[A-Z/0-9-]*\d[A-Z/0-9-]*"
        )
        docket_p = decided[0].getnext()
        if docket_p is not None and docket_p.tag == "p":
            docket = clean_string(docket_p.text_content())
            # avoid censored or missing docket numbers, such as
            # "Case No. XXXXX" or "Claim No. NONE"
            if (
                docket_regex.fullmatch(docket)
                and "XXX" not in docket
                and re.search(r"\d", docket)
            ):
                metadata["Docket"]["docket_number"] = docket

        court_p = decided[0].getprevious()
        parties = court_p.getprevious() if court_p is not None else None
        if parties is not None and parties.tag == "div":
            full_case = harmonize(
                " ".join(p.text_content() for p in parties.xpath("./p"))
            )
            metadata["Docket"]["case_name_full"] = full_case
            metadata["OpinionCluster"]["case_name_full"] = full_case

        return {k: v for k, v in metadata.items() if v}

    @staticmethod
    def cleanup_content(content: bytes) -> bytes:
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
