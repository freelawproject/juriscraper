"""Scraper for Board of Veterans' Appeals
CourtID: bva
Court Short Name: BVA
Author: Jon Andersen
Reviewer: mlr
Type: Nonprecedential
History:
    2014-09-09: Created by Jon Andersen
    2016-05-14: Updated by arderyp, moved logic from _get_case_dates() to
    standard download() override method.  Parsing information text from
    unlinked text field, due to recent link text typos
"""

import re
from datetime import datetime

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Cases before 1997 do not have a docket number to parse.
        url_query = "&DB=".join(
            [str(n) for n in range(datetime.today().year, 1997 - 1, -1)]
        )
        self.url = (
            "http://www.index.va.gov/search/va/bva_search.jsp?RPP=50&RS=1&DB=%s"
            % url_query
        )
        self.pager_stop = False
        self.back_scrape_iterable = self.pager(50)
        self.cases = []

    def pager(self, incr):
        startat = 1 + incr
        while not self.pager_stop:
            yield startat
            startat += incr

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        self._extract_case_data_from_html(html)
        return html

    def _extract_case_data_from_html(self, html):
        """Build list of data dictionaries, one dictionary per case."""
        regex = re.compile(
            r"^.*Citation Nr: (.*) Decision Date: (.*) Archive Date: (.*) DOCKET NO. ([-0-9 ]+)"
        )

        for result in html.xpath('//div[@id="results-area"]/div/a'):
            text = result.text_content().strip()
            try:
                (citation, date, docket) = regex.match(text).group(1, 2, 4)
            except:
                raise Exception(
                    "regex failure in _extract_case_data_from_html method of bva scraper"
                )

            # There is a history to this, but the long story short is that we
            # are using the docket number in the name field intentionally.
            self.cases.append(
                {
                    "name": docket,
                    "url": result.xpath(".//@href")[0],
                    "date": convert_date_string(date),
                    "status": "Unpublished",
                    "docket": docket,
                    "citation": citation.split()[0],
                }
            )

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_precedential_statuses(self):
        return [case["status"] for case in self.cases]

    def _download_backwards(self, startat):
        base_url = (
            "http://www.index.va.gov/search/va/bva_search.jsp?RPP=50&RS=%d"
            % (startat,)
        )
        date_range = list(range(datetime.today().year, 1997 - 1, -1))
        self.url = f"{base_url}&DB={'&DB='.join([str(n) for n in date_range])}"
        self.html = self._download()
