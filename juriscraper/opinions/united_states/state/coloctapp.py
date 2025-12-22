"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.

History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by William E. Palin
    - 2023-11-04: Updated by Honey K. Joule
    - 2023-11-19: Updated by William E. Palin
    - 2025-08-11: Add cleanup_content method, quevon24
"""

from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    api_court_code = "14024_02"
    days_interval = 15
    docket_number_regex = r"\d{2,2}CA\d{1,4}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_content_types = ["application/pdf"]

    @staticmethod
    def cleanup_content(content):
        """Return raw pdf content"""
        return content
