"""
Scraper template for the 'Other Courts' of the NY Reporter
Court Contact: phone: (518) 453-6900; fax: (518) 426-1640
Author: Gianfranco Rossi
History:
 - 2024-01-03, grossir: created
"""
import re
from datetime import date
from typing import Dict, Optional

from dateutil.rrule import MONTHLY, rrule
from lxml.html import HtmlElement

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
        base_url = "https://nycourts.gov/reporter/slipidx/miscolo_2023_December.shtml"

        if not target_date:
            return base_url

        end = f"_{target_date.year}_{target_date.strftime('%B')}.shtml"

        return base_url.replace(".shtml", end)

    def _process_html(self) -> None:
        """Parses a page's HTML into opinion dictionaries

        :return: None
        """
        for row in self.html.xpath("//table[caption]//tr[position()>1]"):
            court = row.xpath("td[2]")[0].text_content()

            if not self.is_court_of_interest(court):
                logger.debug(f'Skipping %s' % court)
                continue

            url = row.xpath("td[1]/a/@href")[0]
            name = row.xpath("td[1]/a")[0].text_content()
            opinion_date = row.xpath("td[3]")[0].text_content()
            slip_cite = row.xpath("td[4]")[0].text_content()
            status = "Unpublished" if "(U)" in slip_cite else "Published"

            try:
                citation = self.parse_citation_page(url)
            except IndexError:
                logger.info("Citation page has no data")
                citation = {}

            self.cases.append(
                {
                    "name": name,
                    "date": opinion_date,
                    "status": status,
                    "url": url,
                    "parallel_citation": slip_cite,
                    **citation,
                }
            )

    def is_court_of_interest(self, court: str) -> bool:
        """'Other Courts' of NY Reporter consists of
        different family of sources. Each

        :param court: court name
        :return: true if court name matches
                family of courts of calling scraper
        """
        return bool(re.search(self.court_regex, court))

    def parse_citation_page(self, opinion_url: str) -> Dict[str, str]:
        """Parses citation page associated with the slip number
        This page structures fields that would needto be extracted
        from the opinions PDF/HTML

        :param opinion_url: used to extract the slip_id
        :return: citation dict with judge, docket number and citation values
        """
        if self.test_mode_enabled():
            return {
                "docket_number": "Test Mode",
            }

        slip_id = re.search(r"\d{4}_\d+", opinion_url).group(0)
        citation_url = f"https://lrb.nycourts.gov/citator/reporter/citations/detailsview.aspx?id={slip_id}"
        logger.info(f"Getting citation page {citation_url}")
        html = self._get_html_tree_by_url(citation_url)

        base_xpath = '//tr[td[string()="{}:"]]/td[2]'
        fields_to_citation_page_names = {
            "judge": "Judge",
            "docket_number": "Docket No",
            "citation": "Official Citation",
            "": "Prior Case History",
            # "": "Later Case History",
        }

        citation = {}
        for field, name in fields_to_citation_page_names.items():
            xpath = base_xpath.format(name)
            citation[field] = self.get_text_by_xpath(html, xpath)

        return citation

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

    @staticmethod
    def get_text_by_xpath(html_element: HtmlElement, xpath: str) -> str:
        """Extracts first text content from html element located by xpath

        :param html_element: anchor element for xpath selection
        :param xpath: xpath string
        :return: stripped text content
        """
        return html_element.xpath(xpath)[0].text_content().strip()
