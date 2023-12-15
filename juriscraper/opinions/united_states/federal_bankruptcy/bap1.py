"""
Scraper for the United States Bankruptcy Appellate Panel for the First Circuit
CourtID: bap1
Court Short Name: 1st Cir. BAP
"""

from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.bap1.uscourts.gov/bapopn"
        self.court_id = self.__module__

    def _download(self, request_dict={}) -> None:
        html_tree = super()._download(request_dict)
        self.extract_cases(html_tree)

        if self.test_mode_enabled():
            return html_tree

        # Walk over pagination "Next" page(s), if present
        proceed = True

        while proceed:
            next_page_url = self.extract_next_page_url(html_tree)

            if next_page_url:
                logger.info(f"Scraping next page: {next_page_url}")
                html_tree = self._get_html_tree_by_url(next_page_url)
                self.extract_cases(html_tree)
            else:
                proceed = False

    def extract_next_page_url(self, html_tree: HtmlElement) -> str:
        next_page_link_xpath = '//a[@title="Go to next page"]/@href'
        elements = html_tree.xpath(next_page_link_xpath)

        return elements[0] if elements else ""

    def _process_html(self):
        """Defined only to avoid not implemented error"""
        pass

    def extract_cases(self, html_tree: HtmlElement) -> None:
        for row in html_tree.xpath("//tr[td]"):
            case = {
                "status": "Unknown",
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
