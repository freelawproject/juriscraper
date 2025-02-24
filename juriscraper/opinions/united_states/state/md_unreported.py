"""
Scraper for Maryland Court of Appeals
CourtID: md
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
Court Support: webmaster@mdcourts.gov, mdlaw.library@mdcourts.gov
"""

from datetime import date, datetime

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.disable_certificate_verification()
        self.status = "Published"

    # def _process_html(self) -> None:
    #     pass

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "md_unrepoted"

    def get_court_name(self):
        return "Maryland Court of Special Appeals"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Maryland"
