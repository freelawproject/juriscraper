# Author: William E. Palin
# Date created: 2023-01-04
# Notes: See Alabama

from juriscraper.opinions.united_states.state import ala


class Site(ala.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://judicial.alabama.gov/decision/civildecisions"
