"""Scraper for Tenth Circuit of Appeals
CourtID: ca10
Author: mlr
"""

from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.lib.html_utils import (
    get_table_column_text,
    get_table_column_links,
)


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.ca10.uscourts.gov/clerk/oral-argument-recordings"
        )

        # HTTPS certificate is bad, but hopefully they'll fix it and we can remove the line below
        self.disable_certificate_verification()

    def _get_download_urls(self):
        return get_table_column_links(self.html, 5)

    def _get_case_names(self):
        return get_table_column_text(self.html, 2)

    def _get_docket_numbers(self):
        dockets = get_table_column_text(self.html, 1)
        # Handle case where "no results" message is put in table cell, see: ca10_example_2.html
        return (
            []
            if len(dockets) == 1 and "no results" in dockets[0].lower()
            else dockets
        )

    def _get_case_dates(self):
        return [
            convert_date_string(ds)
            for ds in get_table_column_text(self.html, 3)
        ]
