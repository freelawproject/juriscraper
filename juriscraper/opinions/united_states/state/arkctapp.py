# Author: Michael Lissner
# Date created: 2013-08-10

from juriscraper.opinions.united_states.state import ark


class Site(ark.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url_id = 'courtofappeals'
        self.url = self.get_url()
