"""Scraper for the Vermont Superior Court, Civil Division
CourtID: vtsuperct
Court Short Name: Vermont Superior Court
Court Contact: submit form here https://www.vtcourts.gov/website-feedback-form
"""

from juriscraper.opinions.united_states.state import vt


class Site(vt.Site):
    division = 1
    days_interval = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # extract_from_text sets the status only from a neutral citation or the
        # 3 justice panel heading, and Superior Court decisions have neither
        self.status = "Published"
