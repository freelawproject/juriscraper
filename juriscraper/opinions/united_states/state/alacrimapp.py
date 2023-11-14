# Author: William E. Palin
# Date created: 2023-01-04
# Notes: See Alabama

from juriscraper.opinions.united_states.state import ala


class Site(ala.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_str = "b82b30d5-bd3c-46d7-9451-1cb05e470873"
