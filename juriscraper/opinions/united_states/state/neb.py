# Author: Michael Lissner
# Date created: 2013-06-13

from datetime import date
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_if_py3


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.crawl_date = today
        self.url = 'http://supremecourt.ne.gov/sc/opinions/%s' % today.strftime('%Y-%m-%d')
        self.back_scrape_iterable = range(0, 11)

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
        docket_numbers = []
        for el in self.html.xpath(path):
            text = clean_if_py3(str(el)).strip()
            if text:
                docket_numbers.append(text)

        return docket_numbers

    def _get_west_state_citations(self):
        path = '//tr[contains(concat(" ", @class, " "), " sc-opinion ")]/td[2]//text()[normalize-space() != ""]'
        return list(self.html.xpath(path))

    def _download_backwards(self, i):
        host = 'http://supremecourt.ne.gov'
        paths = ['/sc/opinions/2013-06-21',
                 '/sc/opinions/2013-06-14',
                 '/sc/opinions/2013-05-31',
                 '/sc/opinions/2013-05-24',
                 '/sc/opinions/2013-05-17',
                 '/sc/opinions/2013-05-10',
                 '/sc/opinions/2013-05-03',
                 '/sc/opinions/2013-04-25',
                 '/sc/opinions/2013-04-19',
                 '/sc/opinions/2013-04-12',
                 '/sc/opinions/2013-04-05',
                 '/sc/opinions/2013-03-29']
        self.crawl_date = datetime.strptime(paths[i][-10:], '%Y-%m-%d').date()
        self.url = host + paths[i]
        self.html = self._download()
