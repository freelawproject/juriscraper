# Scraper for California's Fifth District Court of Appeal, unpublished opinions
# CourtID: calctapp5d
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp5d


class Site(calctapp5d.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = f"https://www.courts.ca.gov/cms/npopinions.htm?Courts={self.court_code}"
        self.status = "Unpublished"
