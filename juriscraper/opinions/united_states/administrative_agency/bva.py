"""Scraper for Board of Veterans' Appeals
CourtID: bva
Court Short Name: BVA
Author: Jon Andersen
Reviewer: mlr
Type: Nonprecedential
History:
    2014-09-09: Created by Jon Andersen
"""

import time
from datetime import datetime
from datetime import date

import re
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Cases before 1997 do not have a docket number to parse.
        self.url = 'http://www.index.va.gov/search/va/bva_search.jsp?RPP=50&RS=1&DB=' + '&DB='.join(
            [str(n) for n in range(datetime.today().year, 1997-1, -1)])
        self.my_case_dates = []
        self.my_case_names = []
        self.my_docket_numbers = []
        self.my_neutral_citations = []
        self.pager_stop = False

        def pager(incr):
            startat = 1+incr
            while not self.pager_stop:
                yield startat
                startat += incr
        self.back_scrape_iterable = pager(50)

    def _get_case_dates(self):
        path = "//div/a/text()[contains(.,'Citation Nr')]"
        regex = re.compile('^Citation Nr: (.*) Decision Date: (.*) ' +
                           'Archive Date: (.*) DOCKET NO. ([-0-9 ]+)')
        for txt in self.html.xpath(path):
            (citation_number, decision_date,
                archive_date, docket_number) = regex.match(txt).group(1, 2, 3, 4)
            case_name = docket_number  # Huh?
            self.my_case_names.append(case_name)
            self.my_docket_numbers.append(docket_number)
            self.my_neutral_citations.append(citation_number)
            self.my_case_dates.append(date.fromtimestamp(time.mktime(
                time.strptime(decision_date, '%m/%d/%y'))))
        if len(self.my_case_dates) == 0:
            self.pager_stop = True
        return self.my_case_dates

    def _get_download_urls(self):
        path = "//div/a[contains(./text(),'Citation Nr')]/@href"
        return [u for u in self.html.xpath(path)]

    def _get_case_names(self):
        return self.my_case_names

    def _get_docket_numbers(self):
        return self.my_docket_numbers

    def _get_neutral_citations(self):
        return self.my_neutral_citations

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.my_case_dates)

    def _get_case_name_shorts(self):
        # We don't (yet) support short case names for administrative bodies.
        return None

    def _download_backwards(self, startat):
        burl = 'http://www.index.va.gov/search/va/bva_search.jsp?RPP=50&RS=%d' % (startat,)
        self.url = burl+'&DB='+'&DB='.join([str(n) for n in
                                            range(datetime.today().year, 1997-1, -1)])
        self.html = self._download()

