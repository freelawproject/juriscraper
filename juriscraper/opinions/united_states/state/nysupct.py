# Scraper and Back Scraper for New York Commercial Division
# CourtID: nysupct
# Court Short Name: NY

from juriscraper.opinions.united_states.state import nyappterm_1st


class Site(nyappterm_1st.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Commercial Division"
        self.parameters.update({"court": self.court})
