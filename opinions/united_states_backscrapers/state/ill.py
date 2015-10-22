# History:
#   2015-10-20: Created by Andrei Chelaru

from datetime import datetime
from lxml import html
from dateutil import parser
from juriscraper.OpinionSite import OpinionSite
from juriscraper.AbstractSite import logger


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.year = 0
        self.court_id = self.__module__
        self.url = ''
        self.url_base = 'http://www.illinoiscourts.gov/Opinions/SupremeCourt/{year}/default.asp'
        self.back_scrape_iterable = range(1996, 2015)
        self.download_url_path = None
        self.case_name_path = None
        self.case_dates_path = None
        self.case_dates_path_day = None
        self.case_dates_path_month = None
        self.precedential_statuses_path = None
        self.docket_numbers_path = None
        self.neutral_citations_path = None

    def _get_download_urls(self):
        return list(self.html.xpath(self.download_url_path))

    def _get_case_names(self):

        case_names = [' '.join(i.strip() for i in e.xpath('.//text()')).strip() for e in self.html.xpath(self.case_name_path)]
        return case_names

    def _get_case_dates(self):

        if self.year <= 2006:
            case_dates = []
            for e in self.html.xpath(self.case_dates_path):
                month = ''.join(e.xpath(self.case_dates_path_month)).strip()
                day = ''.join(e.xpath(self.case_dates_path_day)).strip()
                month = month.replace('Decemberr', 'December')
                try:
                    case_dates.append(datetime.strptime('{} {} {}'.format(self.year, month, day), '%Y %B %d'))
                except ValueError:
                    raise
        else:
            case_dates = [parser.parse(''.join(i.strip() for i in d.xpath('.//text()')), fuzzy=True)
                          for d in self.html.xpath(self.case_dates_path)]

        return case_dates

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
            nums = ' '.join(i.strip() for i in e.xpath(".//text()"))
            nums = nums.replace('Official Reports', '')
            docket_numbers.append(nums)
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_citations = None
        if self.neutral_citations_path:
            neutral_citations = []
            for e in self.html.xpath(self.neutral_citations_path):
                neutral_citations.append(' '.join(i.strip() for i in e.xpath(".//text()")).strip())

        return neutral_citations

    def _download_backwards(self, d):
        self.__set_paths(d)

        self.url = self.url_base.format(year=self.year)
        logger.info('Scraping year {}'.format(self.year))
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def __set_paths(self, year):
        self.year = year
        if year < 2006:
            base_path = '//tr/td[4][a]'
            self.download_url_path = '{}/a[1]/@href'.format(base_path)
            self.case_name_path = '{}/preceding-sibling::td[1]'.format(base_path)
            self.case_dates_path = base_path
            self.case_dates_path_day = './preceding-sibling::td[3]//text()'
            self.case_dates_path_month = './/ancestor::tr[1]/preceding-sibling::tr[count(./td) = 1][td//strong][1]/td//text()'
            self.precedential_statuses_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.docket_numbers_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.neutral_citations_path = None
        elif 2006 <= year <= 2010:
            if year == 2010:
                base_path = '//tr/td[3][div/a]'
                self.download_url_path = '{}/div[1]/a[1]/@href'.format(base_path)
                self.case_name_path = '{}/div[1]/a[1]'.format(base_path)
            else:
                base_path = '//tr/td[3][a]'
                self.download_url_path = '{}/a[1]/@href'.format(base_path)
                self.case_name_path = '{}/a[1]'.format(base_path)
            if year == 2006:
                self.case_dates_path = base_path
                self.case_dates_path_day = './preceding-sibling::td[2]//text()'
                self.case_dates_path_month = './/ancestor::tr[1]/preceding-sibling::tr[count(./td) = 1][1]/td//text()'
            else:
                self.case_dates_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.precedential_statuses_path = '{}/preceding-sibling::td[1]'.format(base_path)
            self.docket_numbers_path = '{}/preceding-sibling::td[1]'.format(base_path)
            self.neutral_citations_path = None
        elif 2010 < year < 2015:
            base_path = '//tr/td[4][div/a/text()]'
            self.download_url_path = '{}/div[1]/a[1]/@href'.format(base_path)
            self.case_name_path = '{}/div[1]/a[1]'.format(base_path)
            self.case_dates_path = '{}/preceding-sibling::td[3]'.format(base_path)
            self.precedential_statuses_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.docket_numbers_path = '{}/preceding-sibling::td[2]'.format(base_path)
            self.neutral_citations_path = '{}/preceding-sibling::td[1]'.format(base_path)
