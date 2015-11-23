#  Scraper for Fourth Circuit of Appeals
# CourtID: ca4
# Court Short Name: ca4
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 18 July 2014


from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.ca4.uscourts.gov/OAarchive/OAlist.asp'

    def _get_download_urls(self):
        path = '//tr/td[2]/a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//tr/td[3]/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//tr/td[1]/text()'
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(e):
        e = ''.join(e.split())
        return datetime.strptime(e, '%m/%d/%Y').date()

    def _get_judges(self):
        path = '//tr/td[4]/text()'
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = '//tr/td[2]/a/text()'
        return list(self.html.xpath(path))
