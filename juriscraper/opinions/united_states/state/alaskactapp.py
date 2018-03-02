"""
Scraper for Alaska Court of Appeals
ID: alaskactapp
Court Short Name: Alaska Court of Appeals
"""

import alaska


class Site(alaska.Site):
    url_court_id = 'ap'

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
