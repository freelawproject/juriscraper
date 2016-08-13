# Author: Michael Lissner
# Date created: 2013-05-23


from juriscraper.opinions.united_states.state import haw

class Site(haw.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.target_id = 'ICA'
