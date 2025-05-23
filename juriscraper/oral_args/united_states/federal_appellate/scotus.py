"""Scraper for Supreme Court of U.S.
CourtID: scotus
Court Short Name: scotus
History:
 - 2014-07-20 - Created by Andrei Chelaru, reviewed by MLR
 - 2017-10-09 - Updated by MLR.
"""

from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "http://www.supremecourt.gov/oral_arguments/argument_audio.aspx"
        )
        self.back_scrape_iterable = list(range(2010, 2015))

    def _get_download_urls(self):
        path = "id('list')//tr//a/text()"
        return list(map(self._return_download_url, self.html.xpath(path)))

    @staticmethod
    def _return_download_url(d):
        file_type = "mp3"  # or 'wma' is also available for any case.
        download_url = f"http://www.supremecourt.gov/media/audio/{file_type}files/{d}.{file_type}"
        return download_url

    def _get_case_names(self):
        path = "id('list')//tr/td/span/text()"
        return [s.lstrip(". ") for s in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "id('list')//tr/td[2]//text()"
        return [
            datetime.strptime(s, "%m/%d/%y").date()
            for s in self.html.xpath(path)
            if "Date" not in s
        ]

    def _get_docket_numbers(self):
        path = "id('list')//tr//a/text()"
        return list(self.html.xpath(path))

    def _download_backwards(self, year):
        self.url = (
            f"http://www.supremecourt.gov/oral_arguments/argument_audio/{year}"
        )
        self.html = self._download()
