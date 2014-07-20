"""Scraper for Federal Circuit of Appeals
CourtID: cafc
Court Short Name: cafc
Author: Andrei Chelaru
Reviewer:
Date created: 18 July 2014
"""

from datetime import datetime, date
import random
import re

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        d = date.today()
        self.url = 'http://www.cafc.uscourts.gov/oral-argument-recordings/{date}/all'.format(
            date=d.strftime('%Y-%m-%d')
        )

    def _get_download_urls(self):
        path = "id('searchResults')//tr[position() > 2]/td[4]//@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "id('searchResults')//tr[position() > 2]/td[3]/text()"
        return map(self._return_case_name, self.html.xpath(path))

    @staticmethod
    def _return_case_name(e):
        e = ' '.join(e.split())
        return e

    def _get_case_dates(self):
        path = "id('searchResults')//tr[position() > 2]/td[1]/text()"
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(e):
        e = ''.join(e.split())
        return datetime.strptime(e, '%Y-%m-%d').date()

    def _get_docket_numbers(self):
        path = "id('searchResults')//tr[position() > 2]/td[2]/text()"
        return map(self._return_docket_number, self.html.xpath(path))

    @staticmethod
    def _return_docket_number(e):
        e = ''.join(e.split())
        return e