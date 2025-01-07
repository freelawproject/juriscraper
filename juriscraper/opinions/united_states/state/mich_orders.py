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

from juriscraper.opinions.united_states.state import mich


class Site(mich.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Supreme Court"
        self.court_resource = "supreme-court-order"
        self.opinion_type='SearchCaseOrders'

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for item in self.html["searchItems"]:
            doc=item["mscCaseId"]
            if doc == 0 or doc == '0':
                docket=[]
            else:
                docket=[doc]
            self.cases.append({
                "date": item["displayDate"],
                "docket": docket,
                "name": item["title"],
                "url": f"https://www.courts.michigan.gov{item['documentUrl'].strip()}",
                "lower_court": self.get_lower_courts(item["courts"])
            })

    def get_class_name(self):
        return "mich_orders"
