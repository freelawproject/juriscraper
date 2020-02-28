"""Scraper for Fifth Circuit of Appeals
CourtID: ca5
Court Short Name: ca5
Reviewer: mlr
History:
 - 2014-07-19: Created by Andrei Chelaru
 - 2014-11-08: Updated for new site by mlr.
"""

from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.ca5.uscourts.gov/rss.aspx?Feed=OralArgRecs"

    def _get_download_urls(self):
        path = "//item/link"
        return [e.tail for e in self.html.xpath(path)]

    def _get_case_names(self):
        path = "//item/description/text()[2]"
        return [s for s in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "//item/description/text()[3]"
        return [
            datetime.strptime(date_string[9:], "%m/%d/%Y").date()
            for date_string in self.html.xpath(path)
        ]

    def _get_docket_numbers(self):
        path = "//item/description/text()[1]"
        return [s for s in self.html.xpath(path)]
