"""Scraper for Court of Appeals of the State of Nevada
CourtID: nevapp
Court Short Name: Nev. App.

History:
    - 2023-12-13: Created by William E. Palin
    - 2026-06-22: Reworked for the new Thomson Reuters ACIS portal, #2010
"""

from juriscraper.opinions.united_states.state import nev


class Site(nev.Site):
    # Court of Appeals UUID in the ACIS portal; everything else (endpoint,
    # opinion type filter, parsing) is shared with the Supreme Court scraper
    court_uuid = "74764f58-a87f-4ec5-8233-7a1255e410b3"
