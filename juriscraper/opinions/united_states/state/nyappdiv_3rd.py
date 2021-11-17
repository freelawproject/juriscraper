# Scraper for New York Appellate Divisions 3rd Dept.
# CourtID: nyappdiv_3rd
# Court Short Name: NY

from juriscraper.opinions.united_states.state import nyappdiv_1st


class Site(nyappdiv_1st.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.division = 3
        self.url = self.build_url()
