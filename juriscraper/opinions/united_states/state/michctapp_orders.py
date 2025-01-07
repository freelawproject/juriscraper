"""Scraper for the Michigan Court of Appeals
CourtID: michctapp
Court Short Name: Mich. Ct. App.
Type: Published and Unpublished
Reviewer: mlr
History:
    - 2014-09-19: Created by Jon Andersen
    - 2022-01-28: Updated for new web site, @satsuki-chan.
"""

from typing import List
from urllib.parse import urlencode

from juriscraper.opinions.united_states.state import mich, mich_orders


class Site(mich_orders.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Court Of Appeals"
        self.court_resource = "order"
        self.opinion_type='SearchCaseOrders'

    def get_class_name(self):
        return "michctapp_orders"

    def get_court_name(self):
        return "Michigan Court of Appeals"
