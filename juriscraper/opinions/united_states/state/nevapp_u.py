"""Scraper for unpublished dispositions of the Court of Appeals of Nevada
CourtID: nevapp
Court Short Name: Nev. App.

History:
    - 2026-07-11: Created, #2011
"""

from datetime import datetime

from juriscraper.opinions.united_states.state import nev_u, nevapp


class Site(nev_u.Site):
    # Court of Appeals UUID in the ACIS portal, shared with nevapp
    court_uuid = nevapp.Site.court_uuid

    # The Court of Appeals was seated in 2015; earliest entry in the feed
    first_opinion_date = datetime(2015, 1, 22)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
