# Author: Michael Lissner
# Date created: 2013-06-13

from datetime import date
from datetime import datetime

from juriscraper.GenericSite import GenericSite


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        self.crawl_date = today
        self.url = 'http://supremecourt.ne.gov/sc/opinions/%s' % today.strftime('%m-%d-%Y')

    def _get_download_urls(self):
        path = '//tr[contains(concat(" ", @class, " "), " sc-opinion ")]//a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//tr[contains(concat(" ", @class, " "), " sc-opinion ")]//a/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        # Uses the path to case names as surrogate for date counting
        path = '//tr[contains(concat(" ", @class, " "), " sc-opinion ")]//a/text()'
        return [self.crawl_date] * len(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//tr[contains(concat(" ", @class, " "), " sc-opinion ")]/td[1]//text()[normalize-space() != ""]'
        return list(self.html.xpath(path))

    def _get_west_state_citations(self):
        path = '//tr[contains(concat(" ", @class, " "), " sc-opinion ")]/td[2]//text()[normalize-space() != ""]'
        return list(self.html.xpath(path))

    def _download_backwards(self, i):
        host = 'http://supremecourt.ne.gov'
        paths = ['/coa/opinions/2013-06-18',
                 '/coa/opinions/2013-06-04',
                 '/coa/opinions/2013-05-28',
                 '/coa/opinions/2013-05-21',
                 '/coa/opinions/2013-05-14',
                 '/coa/opinions/2013-05-07',
                 '/coa/opinions/2013-04-30',
                 '/coa/opinions/2013-04-23',
                 '/coa/opinions/2013-04-16',
                 '/coa/opinions/2013-04-09',
                 '/coa/opinions/2013-04-02',
                 '/coa/opinions/2013-03-26',]
        self.site.url = host + paths[i]
        self.html = self._download()
