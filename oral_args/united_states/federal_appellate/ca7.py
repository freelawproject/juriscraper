"""Scraper for Seventh Circuit of Appeals
CourtID: ca7
Court Short Name: ca7
Author: Andrei Chelaru
Reviewer:
Date created: 19 July 2014
"""

from datetime import datetime, date

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        d = date.today()
        # In order to get all the case numbers from a year the number bellow
        # should be changed to all the nr. from 10 to around 50
        start_case_number = 10
        self.url = 'http://media.ca7.uscourts.gov/oralArguments/oar.jsp?caseyear={yr}&casenumber={nr}&listCase=List+case(s)'.format(
            yr=d.strftime('%y'),
            nr=start_case_number
        )

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
    def _return_case_date(e):
        e = ''.join(e.split())
        return datetime.strptime(e, '%m/%d/%Y').date()

    def _get_docket_numbers(self):
        path = '//tr[@bgcolor]/td[1]/text()'
        return list(self.html.xpath(path))