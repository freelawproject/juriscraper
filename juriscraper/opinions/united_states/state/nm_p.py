# Author: Michael Lissner
# Date created: 2013-06-05

from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url(date.today().year)
        self.back_scrape_iterable = range(2009, 2013)

    def _get_download_urls(self):
        return self.get_cell_data(2, '//a/@href')

    def _get_case_names(self):
        return self.get_cell_data(2, '//a/text()')

    def _get_case_dates(self):
        return [convert_date_string(ds) for ds in self.get_cell_data(1, '//text()')]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        return self.get_cell_data(4, '//text()')

    def _get_neutral_citations(self):
        return self.get_cell_data(3, '//text()')

    def _download_backwards(self, year):
        self.set_url(year)
        self.html = self._download()

    def get_cell_data(self, cell_number, sub_path=False):
        path = '//table[@id="GridView1"]/tr/td[%d]' % cell_number
        if sub_path:
            path += sub_path
        return self.html.xpath(path)

    def set_url(self, year):
        self.url = 'http://www.nmcompcomm.us/nmcases/NMARYear.aspx?db=scr&y1=%s&y2=%s' % (year, year)
