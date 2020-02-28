"""Scraper for the United States Department of Justice Attorney General
CourtID: ag
Court Short Name: United States Attorney General
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/olc/opinions?items_per_page=40"
        self.back_scrape_url = self.url + "&page=%d"
        self.back_scrape_iterable = None
        self.cell_path = "//table//tr/td[%d]"

    def _download(self, request_dict={}):
        if not self.test_mode_enabled():
            # don't set this if running tests, as it hits the network
            self.back_scrape_iterable = range(0, self.get_last_page() + 1)
        return super(Site, self)._download(request_dict)

    def _get_case_names(self):
        cells = self.html.xpath(self.cell_path % 2)
        return [cell.text_content().strip() for cell in cells]

    def _get_download_urls(self):
        base_path = self.cell_path % 2
        return [href for href in self.html.xpath("%s//a[1]/@href" % base_path)]

    def _get_case_dates(self):
        cells = self.html.xpath(self.cell_path % 1)
        return [
            convert_date_string(cell.text_content().strip()) for cell in cells
        ]

    def _get_docket_numbers(self):
        """advisory opinions have no docket numbers"""
        return [""] * len(self.case_names)

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_summaries(self):
        cells = self.html.xpath(self.cell_path % 3)
        return [cell.text_content().strip() for cell in cells]

    def get_last_page(self):
        html = self._get_html_tree_by_url(self.url)
        path = "//li[contains(@class, 'pager__item--last')]/a[1]/@href"
        return int(html.xpath(path)[0].split("=")[-1])

    def _download_backwards(self, page_num):
        self.url = self.back_scrape_url % page_num
        self.html = self._download()
