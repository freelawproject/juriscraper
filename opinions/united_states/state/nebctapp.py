# Author: Michael Lissner
# Date created: 2013-06-21

from datetime import date
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.crawl_date = today
        self.url = 'http://supremecourt.ne.gov/coa/opinions/%s' % today.strftime('%Y-%m-%d')
        #self.url = 'http://supremecourt.ne.gov/coa/opinions/2013-06-18'  # For testing...
        self.back_scrape_iterable = range(0, 11)

    def _get_download_urls(self):
        path = '//tr[contains(@class, "opinion")]//a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//tr[contains(@class, "opinion")]//a/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        # Uses the case names path as surrogate for date counting
        path = '//tr[contains(@class, "opinion")]//a/text()'
        return [self.crawl_date] * len(self.html.xpath(path))

    def _get_precedential_statuses(self):
        path = '//tr[contains(@class, "opinion")]//a/@href'
        statuses = []
        for url in self.html.xpath(path):
            if 'memorandum' in url:
                statuses.append("Unpublished")
            else:
                statuses.append("Published")
        return statuses

    def _get_docket_numbers(self):
        path = '//tr[contains(@class, "opinion")]/td[1]//text()[normalize-space() != ""]'
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
                 '/coa/opinions/2013-03-26']
        self.crawl_date = datetime.strptime(paths[i][-10:], '%Y-%m-%d').date()
        self.url = host + paths[i]
        self.html = self._download()
