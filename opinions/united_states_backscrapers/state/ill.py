# History:
#   2015-10-20: Created by Andrei Chelaru

from datetime import datetime
from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.AbstractSite import logger


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.year = 0
        self.court_id = self.__module__
        self.url = 'http://www.illinoiscourts.gov/Opinions/SupremeCourt/{year}/default.asp'
        self.back_scrape_iterable = range(1996, 2015)
        self.download_url_path = None
        self.case_name_path = None
        self.case_dates_path = None
        self.case_dates_path_1 = None
        self.case_dates_path_2 = None
        self.precedential_statuses_path = None
        self.docket_numbers_path = None
        self.neutral_citations_path = None

    def _get_download_urls(self):
        return list(self.html.xpath(self.download_url_path))

    def _get_case_names(self):
        return list(self.html.xpath(self.case_name_path))

    def _get_case_dates(self):

        if self.case_dates_path_1:
            case_dates = []
            for e in self.html.xpath(self.case_dates_path):
                month = e.xpath(self.case_dates_path_2)[0].strip()
                logger.info(str(month))
                day = e.xpath(self.case_dates_path_1)[0].strip()
                case_dates.append(datetime.strptime('{} {} {}'.format(self.year, month, day), '%Y %B %d'))
            return case_dates
        else:
            return [datetime.strptime(date_string, '%m/%d/%y').date()
                    for date_string in self.html.xpath(self.case_dates_path)]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath(self.precedential_statuses_path):
            s = html.tostring(e, method='text', encoding='unicode')
            if 'NRel' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath(self.docket_numbers_path):
            s = html.tostring(e, method='text', encoding='unicode')
            s = " ".join(s.split())
            if s:
                docket_numbers.append(s)
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_citations = None
        if self.neutral_citations_path:
            neutral_citations = []
            for e in self.html.xpath(self.neutral_citations_path):
                neutral_citations.append(e)
        return neutral_citations

    def _download_backwards(self, d):
        self.set_base_path(d)

        self.url = self.url.format(year=d)
        logger.info('Scraping year {}'.format(d))
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def set_base_path(self, year):
        self.year = year
        if year < 2006:
            base_path = '//tr/td[4][a]'
            self.download_url_path = '{}/a/@href'.format(base_path)
            self.case_name_path = '{}/preceding-sibling::td[1]/a[1]/text()[1]'.format(base_path)
            self.case_dates_path = base_path
            self.case_dates_path_1 = './preceding-sibling::td[3]/text()[1]'
            self.case_dates_path_2 = './/ancestor::tr[1]/preceding-sibling::tr[count(./td) = 1][1]/td/strong/text()'
            self.precedential_statuses_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.docket_numbers_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.neutral_citations_path = None
        elif 2006 <= year < 2010:
            base_path = '//tr/td[3][a]'
            self.download_url_path = '{}/a/@href'.format(base_path)
            self.case_name_path = '{}/a/text()'.format(base_path)
            self.case_dates_path = '{}/preceding-sibling::td[2]//text()'.format(base_path)
            self.precedential_statuses_path = '{}/preceding-sibling::td[1]'.format(base_path)
            self.docket_numbers_path = '{}/preceding-sibling::td[1]'.format(base_path)
            self.neutral_citations_path = None
        elif 2010 <= year < 2015:
            base_path = '//tr/td[4][div/a]'
            self.download_url_path = '{}/div/a/@href'.format(base_path)
            self.case_name_path = '{}/div/a/text()'.format(base_path)
            self.case_dates_path = '{}/preceding-sibling::td[3]//text()'.format(base_path)
            self.precedential_statuses_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.docket_numbers_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.neutral_citations_path = '{}/preceding-sibling::td[1]/text()'.format(base_path)
