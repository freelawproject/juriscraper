# Author: Michael Lissner
# Date created: 2013-06-21

from datetime import date
from datetime import datetime

from juriscraper.GenericSite import GenericSite
from lxml import html


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        self.crawl_date = today
        self.url = 'http://supremecourt.ne.gov/coa/opinions/%s' % today.strftime('%Y-%m-%d')
        #self.url = 'http://supremecourt.ne.gov/coa/opinions/2013-06-18'  # For testing...

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

    def _get_west_state_citations(self):
        path = '//tr[contains(@class, "opinion")]/td[2]'
        cites = []
        for e in self.html.xpath(path):
            s = html.tostring(e, method='text', encoding='unicode')
            if s.strip():
                cites.append(s.strip())
            else:
                # It's a memorandum opinion, s.strip() == ""
                cites.append(None)
        return cites

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
        self.site.crawl_date = datetime.strptime(paths[i][-10:], '%Y-%m-%d').date()
        self.site.url = host + paths[i]
        self.html = self._download()
