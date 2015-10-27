# Author: Michael Lissner
# Date created: 2013-06-05

import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.nmcompcomm.us/nmcases/NMARYear.aspx?db=scr&y1=%s&y2=%s' % (today.year, today.year)
        self.back_scrape_iterable = range(2009, 2013)

    def _get_download_urls(self):
        path = '//table[@id="GridView1"]/tr/td[2]//a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//table[@id="GridView1"]/tr/td[2]//a/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//table[@id="GridView1"]/tr/td[1]//text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//table[@id="GridView1"]/tr/td[4]//text()'
        return list(self.html.xpath(path))

    def _get_neutral_citations(self):
        path = '//table[@id="GridView1"]/tr/td[3]//text()'
        return list(self.html.xpath(path))

    def _download_backwards(self, year):
        self.url = 'http://www.nmcompcomm.us/nmcases/NMARYear.aspx?db=scr&y1=%s&y2=%s' % (year, year)
        self.html = self._download()
