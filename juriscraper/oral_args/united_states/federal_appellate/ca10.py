"""Scraper for Tenth Circuit of Appeals
CourtID: ca10
Author: mlr
"""

import datetime

from juriscraper.lib.html_utils import (
    get_table_column_links,
    get_table_column_text,
)
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # query for results of current month
        now = datetime.datetime.now()
        start_date = now - datetime.timedelta(weeks=4)
        start = "%d/%d/%d" % (
            start_date.month,
            start_date.day,
            start_date.year,
        )
        end = "%d/%d/%d" % (now.month, now.day, now.year)
        self.url = (
            "https://www.ca10.uscourts.gov/oralargument/search-results?"
            "field_oa_hearing_date_value[min][date]=%s&"
            "field_oa_hearing_date_value[max][date]=%s"
        ) % (start, end)

    def _get_download_urls(self):
        return get_table_column_links(self.html, 6)

    def _get_case_names(self):
        return get_table_column_text(self.html, 3)

    def _get_docket_numbers(self):
        dockets = get_table_column_text(self.html, 2)
        # Handle case where "no results" message is put in table cell, see: ca10_example_2.html
        return (
            []
            if len(dockets) == 1 and "no results" in dockets[0].lower()
            else dockets
        )

    def _get_case_dates(self):
        return [
            convert_date_string(ds)
            for ds in get_table_column_text(self.html, 4)
        ]
