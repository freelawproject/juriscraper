"""Scraper for Supreme Court of U.S. OYEZ
CourtID: scotus
Court Short Name: scotus
Author: Andrei Chelaru
Reviewer:
Date created: 20 July 2014
"""

from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.supremecourt.gov/oral_arguments/argument_audio.aspx'

    def _get_download_urls(self):
        path = "id('maincontentbox')//tr//a/text()"
        return map(self._return_download_url, self.html.xpath(path))

    def _return_download_url(self, d):
        file_type = 'mp3' # or 'wma'
        download_url = 'http://www.supremecourt.gov/media/audio/{type}files/{docket_number}.{type}'.format(
            type=file_type,
            docket_number=d
        )
        return download_url

    def _get_case_names(self):
        path = "id('maincontentbox')//tr//a/text()/ancestor::tr[1]/td[1]/text()[2]"
        return map(self._return_case_name, self.html.xpath(path))

    def _return_case_name(self, e):
        return e.lstrip('. ')

    def _get_case_dates(self):
        path = "id('maincontentbox')//tr//a/text()/ancestor::tr[1]/td[2]/text()"
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(e):
        return datetime.strptime(e, '%m/%d/%y').date()

    def _get_docket_numbers(self):
        path = "id('maincontentbox')//tr//a/text()"
        return list(self.html.xpath(path))