"""
Scraper template for the 'Other Courts' of the NY Reporter
Court Contact: phone: (518) 453-6900; fax: (518) 426-1640
Author: Gianfranco Rossi
History:
 - 2024-01-05, grossir: created
"""
import calendar
import re
from datetime import date
from typing import Any, Dict, List, Optional

from dateutil.rrule import MONTHLY, rrule
from lxml.html import HtmlElement
from lxml.html import fromstring as html_fromstring

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import get_html5_parsed_text
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_regex: str  # to be defined on inheriting classes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.court_id = self.__module__
        self.url = self.build_url()

        date_keys = rrule(
            MONTHLY, dtstart=date(2003, 12, 1), until=date(2023, 12, 30)
        )
        self.back_scrape_iterable = [i.date() for i in date_keys]

    def build_url(self, target_date: Optional[date] = None) -> str:
        """URL as is loads most recent month page
        There is an URL for each month of each year back to Dec 2003

        :param target_date: used to extract month and year for backscraping
        :returns str: formatted url
        """
        base_url = "https://nycourts.gov/reporter/slipidx/miscolo.shtml"

        if not target_date:
            return base_url

        end = f"_{target_date.year}_{target_date.strftime('%B')}.shtml"

        return base_url.replace(".shtml", end)

    def is_court_of_interest(self, court: str) -> bool:
        """'Other Courts' of NY Reporter consists of 10 different
        family of sources. Each family has an scraper that inherits
        from this class and defines a `court_regex` to capture those
        that belong to its family

        For example
        "Civ Ct City NY, Queens County" and "Civ Ct City NY, NY County"
        belong to nycciv family

        :param court: court name
        :return: true if court name matches
                family of courts of calling scraper
        """
        return bool(re.search(self.court_regex, court))

    def _process_html(self) -> None:
        """Parses a page's HTML into opinion dictionaries

        :return: None
        """
        for row in self.html.xpath("//table[caption]//tr[position()>1]"):
            court = row.xpath("td[2]")[0].text_content()

            if not self.is_court_of_interest(court):
                logger.debug(f"Skipping {court}")
                continue

            url = row.xpath("td[1]/a/@href")[0]
            name = row.xpath("td[1]/a")[0].text_content()
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
                }
            )

    def _get_docket_numbers(self) -> List[None]:
        """Overriding from OpinionSiteLinear, since docket numbers are
        not in the HTML and they are required

        We will get them on the extract_from_text stage on courtlistener
        :return: list of None values
        """
        return [None for _ in self.cases]

    def _download_backwards(self, target_date: date) -> None:
        """Method used by backscraper to download historical records

        :param target_date: an element of self.back_scrape_iterable
        :return: None
        """
        self.url = self.build_url(target_date)

    def _make_html_tree(self, text: str) -> HtmlElement:
        """Overrides method from AbstractSite
        Taken from nyappterm_1st that implements this same site
        but needs different parsing

        :param text: html as text
        :returns: html object
        """
        return get_html5_parsed_text(text)

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extracts docket number, judge name and citation, if available

        :param scraped_text: can be cleansed HTML with some tags
                             or plain PDF text, processed by courtlistener
        :return: Dictionary where each key is a courtlistener Django Model name
                and each value is dictionary of model's fields
        """
        docket_number = self.get_docket_number_from_text(scraped_text)
        judge = self.get_judge_from_text(scraped_text)
        citation = self.get_citation_from_text(scraped_text)

        metadata = {}

        if docket_number:
            metadata["Docket"] = {"docket_number": docket_number.strip()}
        if judge:
            metadata["Opinion"] = {"author_str": judge.strip()}
        if citation:
            metadata["Citation"] = citation

        return metadata

    def get_docket_number_from_text(self, scraped_text: str) -> str:
        """Get docket number
        Sometimes it is explicit in a table at the beginning of the document
        with the heading 'Docket Number'

        Sometimes it is explicit in the first lines of the text with headings
        such as 'Index No', 'Docket No', etc

        Sometimes it is just a special string, that may be numeric only
        Sometimes it may not exist

        :param scraped_text: scraped text
        :return: docket number if it exists
        """
        match = re.search(r"Docket Number:(?P<docket>.+)", scraped_text)
        if match:
            return match.group("docket")

        regex = r"(Docket|Index|File|Claim|Case)\s(Number|No)\s?(\.|:)?\s(?P<docket>.+)"
        match = re.search(regex, scraped_text[:2000])
        if match:
            return match.group("docket")

        # If we reach this stage, the docket number is after the document
        # heading table, but shouldn't be to deep into the document

        # There are some purely numeric docket numbers, but strings with
        # symbols or letters are prioritized

        regex_special = r"[-/A-Z]"
        matches = sorted(
            re.finditer(r"[A-Z0-9-/]{5,}", scraped_text[500:2000]),
            key=lambda x: len(re.findall(regex_special, x.group())),
        )

        if not matches:
            return ""

        return matches[-1].group()

    def get_judge_from_text(self, scraped_text: str) -> str:
        """
        Extraction strategy may take advantage of HTML structure
        If that doesn't work, search over free text

        :param scraped_text: string from HTML or PDF
        :return: judge name
        """
        judge = self.get_judge_from_html(scraped_text)

        if not judge:
            match = re.search(r"Judge:\s?(?P<judge>.+)", scraped_text)
            if match:
                judge = match.group("judge")

        return judge

    def get_judge_from_html(self, scraped_text: str) -> str:
        """HTML files have a table where the judge is in the
        3rd or 4th row. Content is checked in case the order of the table
        is not as expected

        3rd row: https://nycourts.gov/reporter/3dseries/2023/2023_23374.htm
        4th row: https://nycourts.gov/reporter/3dseries/2023/2023_23374.htm

        :param scraped_text: scraped text
        :return: Judge if found, or empty string
        """
        if "<table" not in scraped_text:
            return ""

        html = html_fromstring(scraped_text)

        months = "|".join(calendar.month_name[1:])
        negative_regex = rf"Court|Ct|Published|Decided|Slip|{months}"

        for index in range(2, 5):
            candidate = html.xpath("//td")[index].text_content()

            if not re.search(negative_regex, candidate):
                return candidate.strip()

        return ""

    def get_citation_from_text(self, scraped_text: str) -> Dict[str, str]:
        """Extracts volume, reporter and page of citation that
        has the following shape [81 Misc 3d 1211(A)]

        Citation should be searched on the top of the document since an opinion
        may cite other opinions on the argumentation

        Tagged as "Official Citation" on the source. For example:
        https://lrb.nycourts.gov/citator/reporter/citations/detailsview.aspx?id=2023_51315

        :param scraped_text: string from HTML or PDF
        :return: dictionary with expected citation fields
        """
        regex = r"\[(?P<volume>\d+) (?P<reporter>Misc 3d) (?P<page>.+)\]"
        match = re.search(regex, scraped_text[:1200])

        if not match:
            return {}

        return match.groupdict("")
