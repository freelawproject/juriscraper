"""Scraper for Seventh Circuit of Appeals
CourtID: ca7
Court Short Name: ca7
Author: Andrei Chelaru
Reviewer: mlr
Date created: 19 July 2014
"""

from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://media.ca7.uscourts.gov/oralArguments/oar.jsp?caseyear=&casenumber=&period=Past+month'

    def _get_download_urls(self):
        path = '//tr[@bgcolor]/td[5]//@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//tr[@bgcolor]/td[2]/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//tr[@bgcolor]/td[4]/text()'
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(s):
        return datetime.strptime(s.strip(), '%m/%d/%Y').date()

    def _get_docket_numbers(self):
        path = '//tr[@bgcolor]/td[1]/text()'
        return list(self.html.xpath(path))
