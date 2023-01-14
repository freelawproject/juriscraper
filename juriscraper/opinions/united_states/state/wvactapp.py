# Author: Michael Lissner
# Date created: 2013-06-21

from juriscraper.opinions.united_states.state import wva


class Site(wva.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.courtswv.gov/intermediate-court/opinions.html"
