"""Scraper for Federal Circuit of Appeals
CourtID: cafc
Court Short Name: cafc
Author: Andrei Chelaru
Reviewer: mlr
History:
 - created by Andrei Chelaru, 18 July 2014
 - Updated/rewritten by mlr, 2016-04-14
"""

from datetime import date
from dateutil.rrule import DAILY, rrule
from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        self.url = "http://www.cafc.uscourts.gov/oral-argument-recordings?field_date_value2[value][date]={date}".format(
            date=d.strftime("%Y-%m-%d")
        )
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=1,  # Every day
                dtstart=date(2015, 7, 10),
                until=date(2016, 4, 14),
            )
        ]

    def _get_download_urls(self):
        path = "//td[contains(@class,'views-field-field-filename')]//@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "//td[contains(@class,'views-field-title')]//text()"
        return [" ".join(s.split()) for s in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "//span[@class='date-display-single']/@content"
        return [convert_date_string(s.strip()) for s in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = "//td[contains(@class,'views-field-field-case-number')]//text()"
        return [s.strip() for s in self.html.xpath(path)]

    def _download_backwards(self, d):
        self.url = (
            self.url
        ) = "http://www.cafc.uscourts.gov/oral-argument-recordings?field_date_value2[value][date]={date}".format(
            date=d.strftime("%Y-%m-%d")
        )
        self.html = self._download()
