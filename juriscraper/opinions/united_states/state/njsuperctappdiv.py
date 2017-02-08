# Author: Krist Jin
# Date created: 2013-08-03

from juriscraper.opinions.united_states.state import nj


class Site(nj.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.judiciary.state.nj.us/opinions/index.htm'
        self.table = '2'  # Used as part of the paths to differentiate between appellate and supreme
