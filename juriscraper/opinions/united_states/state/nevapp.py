"""Scraper for Court of Appeals of the State of Nevada
CourtID: nevapp
Court Short Name: Nev. App.

History:
    - 2023-12-13: Created by William E. Palin
    - 2026-06-22: Reworked for the new Thomson Reuters ACIS portal, #2010
    - 2026-10-01: Resolve judge initials to full names, #2049
"""

from datetime import date

from juriscraper.opinions.united_states.state import nev


class Site(nev.Site):
    # Court of Appeals UUID in the ACIS portal; everything else (endpoint,
    # opinion type filter, parsing) is shared with the Supreme Court scraper
    court_uuid = "74764f58-a87f-4ec5-8233-7a1255e410b3"
    # Same format as nev, complete since the court started in 2015
    initials_to_judges = {
        # Department 1
        "JT": [("Jerome T. Tao", date(2015, 1, 5), date(2023, 1, 2))],
        "DW": [("Deborah L. Westbrook", date(2023, 1, 2), None)],
        # Department 2
        "MG": [("Michael P. Gibbons", date(2015, 1, 5), None)],
        # Department 3
        "AS": [("Abbi Silver", date(2015, 1, 5), date(2019, 1, 7))],
        "BB": [("Bonnie A. Bulla", date(2019, 3, 4), None)],
    }
