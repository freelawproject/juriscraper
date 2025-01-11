"""
Scraper template for the 'Other Courts' of the NY Reporter
Court Contact: phone: (518) 453-6900
Author: Gianfranco Rossi
History:
 - 2024-01-05, grossir: created
"""

import re
from datetime import date
from itertools import chain
from typing import Any, Dict, List, Optional

from dateutil.rrule import MONTHLY, rrule
from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import harmonize
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_regex: str  # to be defined on inheriting classes
    base_url = "https://nycourts.gov/reporter/slipidx/miscolo.shtml"
    first_opinion_date = date(2003, 12, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.court_id = self.__module__
        self.url = self.build_url()

        date_keys = rrule(
            MONTHLY, dtstart=self.first_opinion_date, until=date(2023, 12, 30)
        )
        self.back_scrape_iterable = [i.date() for i in date_keys]
        self.expected_content_types = ["application/pdf", "text/html"]

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

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extract values from opinion's text

        :param scraped_text: pdf or html string contents
        :return: dict where keys match courtlistener model objects
        """
        pattern = r"Judge:\s?(.+)|([\w .,]+), [JS]\.\s"
        judge = self.match(scraped_text, pattern)

        pattern = r"</table><br><br\s?/?>\s?(.*)\r?\n|Docket Number:\s?(.+)"
        docket_number = self.match(scraped_text, pattern)

        regex_citation = r"(?<=\[)\d+ Misc 3d .+(?=\])"
        cite_match = re.search(regex_citation, scraped_text[:2000])

        # Only for .htm links
        full_case = None
        if scraped_text.find("<table") != -1:
            # replace <br> with newlines because text_content() replaces <br>
            # with whitespace. If not, case names would lack proper separation
            scraped_text = scraped_text.replace("<br>", "\n")
            full_case = fromstring(scraped_text).xpath("//table")
            full_case = full_case[1].text_content() if full_case else ""

        metadata = {
            "Docket": {"docket_number": docket_number},
        }

        if judge:
            metadata["Opinion"] = {
                "author_str": normalize_judge_string(judge)[0]
            }
        if cite_match:
            metadata["Citation"] = cite_match.group(0)
        if full_case:
            full_case = harmonize(full_case)
            metadata["Docket"]["case_name_full"] = full_case
            metadata["OpinionCluster"] = {"case_name_full": full_case}

        return metadata

    @staticmethod
    def match(scraped_text: str, pattern: str) -> str:
        """Returns first match

        :param scraped_text: HTML or PDF string content
        :param pattern: regex string

        :returns: first match
        """
        m = re.findall(pattern, scraped_text)
        r = list(filter(None, chain.from_iterable(m)))
        return r[0].strip() if r else ""
