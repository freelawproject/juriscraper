# Author: Michael Lissner
# Date created: 2013-08-10

from juriscraper.opinions.united_states.state import ark


class Site(ark.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "courtofappeals"
        self.url = f"https://opinions.arcourts.gov/ark/{self.court}/en/rss.do"
        self.cite_regex = r"\d{2,4} Ark\. App\. \d+"
