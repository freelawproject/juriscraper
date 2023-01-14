"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
    - 2023-01-13: Update to use RSS Feed
"""

from juriscraper.opinions.united_states.federal_appellate import ca9_p


class Site(ca9_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/memoranda/index.xml"
        self.status = "Unpublished"
