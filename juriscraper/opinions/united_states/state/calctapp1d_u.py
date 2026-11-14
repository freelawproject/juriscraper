# Scraper for California's First District Court of Appeal, unpublished opinions
# CourtID: calctapp1d
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp1d


class Site(calctapp1d.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = f"https://www.courts.ca.gov/cms/npopinions.htm?Courts={self.court_code}"
        self.status = "Unpublished"
