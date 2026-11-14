# Scraper for California's Sixth District Court of Appeal, unpublished opinions
# CourtID: calctapp6d
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp6d


class Site(calctapp6d.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = f"https://www.courts.ca.gov/cms/npopinions.htm?Courts={self.court_code}"
        self.status = "Unpublished"
