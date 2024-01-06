"""
Scraper template for the 'Other Courts' of the NY Reporter
Court Contact: phone: (518) 453-6900; fax: (518) 426-1640
Author: Gianfranco Rossi
History:
 - 2024-01-05, grossir: created
"""
import re
from datetime import date
from typing import Any, Dict, List, Optional

from dateutil.rrule import MONTHLY, rrule
from lxml.html import HtmlElement
from lxml.html import fromstring as html_fromstring

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import get_html5_parsed_text
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_regex: str  # to be defined on inheriting classes
    base_url = "https://nycourts.gov/reporter/slipidx/miscolo.shtml"

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
        if not target_date:
            return self.base_url

        end = f"_{target_date.year}_{target_date.strftime('%B')}.shtml"

        return self.base_url.replace(".shtml", end)

    def is_court_of_interest(self, court: str) -> bool:
        """'Other Courts' of NY Reporter consists of 10 different
        family of sources. Each family has an scraper that inherits
        from this class and defines a `court_regex` to capture those
        that belong to its family

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

    def _get_docket_numbers(self) -> List[str]:
        """Overriding from OpinionSiteLinear, since docket numbers are
        not in the HTML and they are required

        We will get them on the extract_from_text stage on courtlistener
        :return: list of empty strings values
        """
        return ["" for _ in self.cases]

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
        docket_number = self.get_docket_number(scraped_text)
        judge = self.get_judge(scraped_text)
        citation = self.get_citation(scraped_text)

        metadata = {}

        if docket_number:
            clean_docket_number = clean_string(docket_number)
            metadata["Docket"] = {
                "docket_number": harmonize(clean_docket_number)
            }
        if judge:
            metadata["Opinion"] = {"author_str": judge}
        if citation:
            metadata["Citation"] = citation

        return metadata

    def get_docket_number(self, scraped_text: str) -> str:
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
        if "<table" in scraped_text:
            html = html_fromstring(scraped_text)
            docket_xpath = "//table[@width='75%']/following-sibling::text()"
            element = html.xpath(docket_xpath)
            docket = element[0] if element else ""
        else:
            docket_regex = r"Docket Number:(?P<docket>.+)"
            match = re.search(docket_regex, scraped_text[:500])
            docket = match.group("docket") if match else ""

        return docket.strip()

    def get_judge(self, scraped_text: str) -> str:
        """Get judge from PDF or HTML text

        We delete a trailing ", J." or ", S." after judge's last names,
        which appear in HTML tables. This are honorifics
        For "S.": https://www.nycourts.gov/reporter/3dseries/2023/2023_50144.htm

        :param scraped_text: string from HTML or PDF
        :return: judge name
        """
        if "<table" in scraped_text:
            html = html_fromstring(scraped_text)
            td = html.xpath(
                '//td[contains(text(), ", J.") or contains(text(), ", S.")]'
            )
            judge = td[0].text_content() if td else ""
        else:
            match = re.search(r"Judge:\s?(?P<judge>.+)", scraped_text)
            judge = match.group("judge") if match else ""

        judge = normalize_judge_string(clean_string(judge))[0]
        judge = re.sub(r" [JS]\.$", "", judge)

        return judge.strip()

    def get_citation(self, scraped_text: str) -> Dict[str, str]:
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
