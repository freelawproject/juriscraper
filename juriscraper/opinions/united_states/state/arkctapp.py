# Author: Michael Lissner
# Date created: 2013-08-10

from juriscraper.opinions.united_states.state import ark


class Site(ark.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://opinions.aoc.arkansas.gov/weblink8/Browse.aspx?startid=39308'
        self.court_id = self.__module__
