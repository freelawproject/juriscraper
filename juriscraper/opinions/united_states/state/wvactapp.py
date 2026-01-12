# Author: Michael Lissner
# Date created: 2013-06-21

from juriscraper.opinions.united_states.state import wva


class Site(wva.Site):
    """
    This site returns all data in a single request, ~1800 opinions as of 2026
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.courtswv.gov/appellate-courts/intermediate-court-of-appeals/opinions/prior-terms"
