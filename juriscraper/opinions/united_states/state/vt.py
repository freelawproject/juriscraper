"""Scraper for Vermont Supreme Court
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form

If there are errors with the site, you can contact:

 Monica Bombard
 (802) 828-4784

She's very responsive.
"""

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(1, self.get_backscrape_max()))
        self.element_path_format = "//article[@class='views-row media-document']/div[@class='views-field views-field-field-document%s']"
        self.url = (
            "https://www.vermontjudiciary.org/opinions-decisions?f[0]=document_type%3A94&f[1]=court_division_opinions_library_%3A"
            + self.get_division_id()
        )
        self.backscrape_page_base_url = f"{self.url}&page="

    def get_backscrape_max(self):
        return 7

    def get_division_id(self):
        return "7"

    def _get_download_urls(self):
        path_base = self.element_path_format % ""
        path = f"{path_base}//@href"
        return self.html.xpath(path)

    def _get_case_names(self):
        path = self.element_path_format % ""
        return [e.text_content().strip() for e in self.html.xpath(path)]

    def _get_case_dates(self):
        path = self.element_path_format % "-expiration"
        return [
            convert_date_string(e.text_content())
            for e in self.html.xpath(path)
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = self.element_path_format % "-number"
        return [e.text_content().strip() for e in self.html.xpath(path)]

    def _download_backwards(self, page_number):
        logger.info("PROCESSING PAGE: %d" % (page_number + 1))
        self.url = self.backscrape_page_base_url + str(page_number)
        self.html = self._download()
