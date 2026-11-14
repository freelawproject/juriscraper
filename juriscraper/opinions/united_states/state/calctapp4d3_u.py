# Scraper for California's Fourth District Court of Appeal Division 3, unpublished opinions
# CourtID: calctapp4d3
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp4d3


class Site(calctapp4d3.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = f"https://www.courts.ca.gov/cms/npopinions.htm?Courts={self.court_code}"
        self.status = "Unpublished"
