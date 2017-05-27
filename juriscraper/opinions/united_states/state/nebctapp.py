# Author: Michael Lissner
# Date created: 2013-06-21

from juriscraper.opinions.united_states.state import neb


class Site(neb.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'https://supremecourt.nebraska.gov/courts/court-appeals/opinions'
