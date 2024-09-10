"""Scraper for Eleventh Circuit of Appeals
CourtID: ca11
Court Short Name: ca11
Author: Jon Andersen
Reviewer: mlr
Date created: 28 Aug 2018
"""

from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    base_url = "https://www.ca11.uscourts.gov/oral-argument-recordings"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.back_scrape_iterable = [i for i in range(0, 52)]
        self.base_path = "//tr[not(th)]"

    def _get_download_urls(self):
        path = f"{self.base_path}//td[5]//@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = f"{self.base_path}//td[2]/text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = f"{self.base_path}//td[3]/text()"
        return list(map(self._return_case_date, self.html.xpath(path)))

    @staticmethod
    def _return_case_date(s):
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()

    def _get_docket_numbers(self):
        path = f"{self.base_path}//td[1]/text()"
        # normalize docket numbers
        # get rid of "consolidated with" text
        # parse docket numbers like docketnum1 & docketnum2
        # also handle docketnum1\ndocketnum2\ndocketnum3
        # Return comma joined string like docketnum1, docketnum2
        return [
            ", ".join(
                d.strip()
                .upper()
                .replace("&", "\n")
                .replace(" AND ", "\n")
                .replace(",", "\n")
                .replace("CONS. WITH", "\n")
                .replace("CONSOLIDATED WITH", "\n")
                .split()
            )
            for d in self.html.xpath(path)
        ]

    def _download_backwards(self, i):
        self.url = f"{self.base_url}?page={i}"
        self.html = self._download()
