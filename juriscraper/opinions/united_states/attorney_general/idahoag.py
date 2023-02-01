"""
Scraper for Idaho Attorney General
CourtID: idahoag
Court Short Name: Idaho AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import json

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.parameters = {
            "page": "1",
            "page_size": "30",
            "cat": "88",
        }
        self.url = f"https://www.ag.idaho.gov/wp-json/wp/v2/opinions"
        self.json = None

    def _download(self, request_dict={}):
        """Custom download

        :param request_dict: empty dict
        :return: JSON
        """
        if self.test_mode_enabled():
            with open(self.url) as f:
                self.json = json.load(f)
            return
        self.json = (
            self.request["session"]
            .get(self.url, params=self.parameters)
            .json()
        )

    def _process_html(self):
        """Process the html

        :return: None
        """
        for item in self.json:
            self.cases.append(
                {
                    "name": f"Attorney General {item['post_title']}",
                    "url": item["location"],
                    "summary": item["description"],
                    "date": item["post_date"],
                    "docket": item["post_title"],
                }
            )
