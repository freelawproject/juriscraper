"""
Scraper for the United States Bankruptcy Appellate Panel for the First Circuit
CourtID: bap1
Court Short Name: 1st Cir. BAP
"""
from typing import Dict
from datetime import datetime, timedelta

from lxml.html import HtmlElement

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.AbstractSite import logger


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.bap1.uscourts.gov/bapopn"
        self.court_id = self.__module__

        self.method = "GET"

        # Search the last month
        date_filter_end = datetime.today()
        date_filter_start = date_filter_end - timedelta(30)
        self.parameters = {
            "params": {
                "opn": "",
                "field_opn_short_title_value": "",
                "field_opn_issdate_value[min][date]": date_filter_start.strftime(
                    "%m/%d/%Y"
                ),
                "field_opn_issdate_value[max][date]": date_filter_end.strftime(
                    "%m/%d/%Y"
                ),
            }
        }

        self.back_scrape_iterable = ["placeholder"]

    def _download(self, request_dict: Dict = {}) -> HtmlElement:
        return super()._download(self.parameters)

    def _process_html(self) -> None:
        for row in self.html.xpath("//tr[td]"):
            opinion_name = row.xpath("td[1]")[0].text_content().strip()
            status = self.get_status_from_opinion_name(opinion_name)

            case = {
                "status": status,
                "url": row.xpath("td[1]/a/@href")[0],  # opinion url
                "docket": row.xpath("td[2]")[0].text_content().strip(),
                # Pub Date
                "date": row.xpath("td[3]")[0].text_content().strip(),
                # short title
                "name": row.xpath("td[4]")[0].text.strip(),
                # district
                "lower_court": row.xpath("td[4]/span")[0]
                .text_content()
                .strip(),
            }

            self.cases.append(case)

    def _download_backwards(self, _) -> None:
        self.backscraper = True
        self.parameters = {}  # delete date filters used in normal scraper

        self.html = self._download()
        self._process_html()

        next_page_exists = True

        while next_page_exists:
            next_page_url = self.extract_next_page_url()

            if next_page_url:
                logger.info(f"Scraping next page: {next_page_url}")
                self.html = self._get_html_tree_by_url(next_page_url)
            else:
                next_page_exists = False

            self._process_html()

    def extract_next_page_url(self) -> str:
        next_page_link_xpath = "//a[@title='Go to next page']/@href"
        elements = self.html.xpath(next_page_link_xpath)

        return elements[0] if elements else ""

    @staticmethod
    def get_status_from_opinion_name(opinion_name: str) -> str:
        if opinion_name.endswith("U"):
            status = "Unpublished"
        elif opinion_name.endswith("P"):
            status = "Published"
        else:
            status = "Unknown"

        return status
