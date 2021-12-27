"""
Scraper for Florida 3rd District Court of Appeal
CourtID: flaapp3
Court Short Name: flaapp3
Contact: 3dca@flcourts.org, Angel Falero <faleroa@flcourts.org> (305-229-6743)
"""

from juriscraper.lib.html_utils import (
    get_table_column_links,
    get_table_column_text,
)
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Browser url: https://www.3dca.flcourts.org/Opinions/Most-Recent-Opinion-Release
        self.url = "https://www.3dca.flcourts.org/search/opinions/?sort=opinion/type%20desc,%20opinion/case_number%20asc&view=embed_custom&searchtype=opinions&recent_only=1&hide_search=1&hide_filters=1&limit=75&offset=0"

    def _get_case_names(self):
        return get_table_column_text(self.html, 4)

    def _get_download_urls(self):
        return get_table_column_links(self.html, 1)

    def _get_case_dates(self):
        date_strings = get_table_column_text(self.html, 7)
        return [convert_date_string(ds) for ds in date_strings]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _get_docket_numbers(self):
        return get_table_column_text(self.html, 3)
