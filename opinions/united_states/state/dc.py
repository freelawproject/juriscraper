"""Scraper for the D.C. Court of Appeals
CourtID: dc
Court Short Name: D.C.
Author: V. David Zvenyach
Date created:2014-02-21
"""

import time
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite
# from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.dccourts.gov/internet/opinionlocator.jsf'

    # tr.class="opinionTR1" or "opinionTR2"
    # <tr class="opinionTR1"><td class="opinionC1"><a href="/internet/documents/13-BG-955.pdf" target="13-BG-955.pdf">13-BG-955</a></td><td class="opinionC2">In re: Scott B. Gilly</td><td class="opinionC3">Nov 7, 2013</td><td class="opinionC4"></td><td class="opinionC5"></td></tr>

    #.opinionC1/a[@href]
    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table//tr/td[1]/a/@href')]

    #.opinionC2
    def _get_case_names(self):
        return [t for t in self.html.xpath('//table//tr/td[2]/text()')]

    #.opinionC3 (e.g., Nov 7, 2013)
    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%b %d, %Y'))) for date_string in self.html.xpath('//table//tr/td[3]/text()')]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    #.opinionC1 value (e.g., 13-BG-955)
    def _get_docket_numbers(self):
        return [t for t in self.html.xpath('//table//tr/td[1]/a/text()')]