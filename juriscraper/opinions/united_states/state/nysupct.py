# Scraper and Back Scraper for New York Commercial Division
# CourtID: nysupct
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer:
# Date: 2015-10-30

from juriscraper.opinions.united_states.state import nyappterm_1st


class Site(nyappterm_1st.Site):

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court = 'Commercial+Division'
        self.parameters.update({'court': self.court})