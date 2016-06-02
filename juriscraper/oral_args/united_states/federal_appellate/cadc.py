"""Scraper for D.C. Circuit of Appeals
CourtID: cadc
Court Short Name: cadc
Author: Andrei Chelaru
Reviewer: mlr
Date created: 18 July 2014
"""

from datetime import datetime, date

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        #d = date(month=5, day=1, year=2014)
        self.url = 'http://www.cadc.uscourts.gov/recordings/recordings.nsf/DocsByRDate?OpenView&count=100&SKey={yearmo}'.format(
            yearmo=d.strftime('%Y%m')
        )
        self.back_scrape_iterable = ["%s%02d" % (year, month) for year in
                                     range(2007, d.year + 1) for month in
                                     range(1, 13)]

    def _get_download_urls(self):
        path = "id('ViewBody')//div[contains(concat(' ',@class,' '),' row-entry')]//@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "id('ViewBody')//*[contains(concat(' ',@class,' '),' column-two')]/div[1]/text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "id('ViewBody')//date/text()"
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(e):
        e = ''.join(e.split())
        return datetime.strptime(e, '%m/%d/%Y').date()

    def _get_docket_numbers(self):
        path = "id('ViewBody')//*[contains(concat(' ',@class,' '),' row-entry')]//a//text()"
        return list(self.html.xpath(path))

    def _get_judges(self):
        path = '//div[span[contains(., "Judges")]]/text()'
        return [' '.join(s.split()) for s in self.html.xpath(path)]

    def _download_backwards(self, yearmo):
        self.url = 'http://www.cadc.uscourts.gov/recordings/recordings.nsf/DocsByRDate?OpenView&count=100&SKey={yearmo}'.format(
            yearmo=yearmo,
        )
        self.html = self._download()


