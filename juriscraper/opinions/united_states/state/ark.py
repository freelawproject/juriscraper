# Author: Krist Jin
# Reviewer: Michael Lissner
# Date created: 2013-08-03

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase, convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://opinions.aoc.arkansas.gov/weblink8/Browse.aspx?startid=40626'
        # Excludes rows without docket number in cell 4
        self.cell_path = '//tr/td[@class="DocumentBrowserCell"][%d][../*[4]//text()]'

    def _get_download_urls(self):
        path = '%s/a/@href' % (self.cell_path % 1)
        return [href for href in self.html.xpath(path)]

    def _get_case_names(self):
        path = '%s/a/nobr/span[1]' % (self.cell_path % 1)
        return [cell.text_content() for cell in self.html.xpath(path)]

    def _get_case_dates(self):
        return [convert_date_string(cell.text_content()) for cell in self.html.xpath(self.cell_path % 5)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        return self.return_cell_text(4)

    def _get_judges(self):
        return [titlecase(cell.text_content().upper()) for cell in self.html.xpath(self.cell_path % 2)]

    def _get_neutral_citations(self):
        return self.return_cell_text(6)

    def _get_dispositions(self):
        return [titlecase(docket) for docket in self._get_docket_numbers()]

    def return_cell_text(self, cell_number):
        return [cell.text_content() for cell in self.html.xpath(self.cell_path % cell_number)]
