"""Scraper for Federal Circuit of Appeals
CourtID: cafc
Court Short Name: cafc
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
        self.url = 'http://www.cafc.uscourts.gov/oral-argument-recordings/{date}/all'.format(
            date=d.strftime('%Y-%m')
        )

    def _get_download_urls(self):
        path = "id('searchResults')//tr[position() > 2]/td[4]//@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "id('searchResults')//tr[position() > 2]/td[3]/text()"
        return [' '.join(s.split()) for s in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "id('searchResults')//tr[position() > 2]/td[1]/text()"
        return [datetime.strptime(s.strip(), '%Y-%m-%d').date() for s in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = "id('searchResults')//tr[position() > 2]/td[2]/text()"
        return [s.strip() for s in self.html.xpath(path)]
