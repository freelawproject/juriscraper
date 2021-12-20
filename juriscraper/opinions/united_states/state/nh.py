"""
Scraper for New Hampshire Supreme Court
CourtID: nh
Court Short Name: NH
Court Contact: webmaster@courts.state.nh.us
Author: Andrei Chelaru
Reviewer: mlr
History:
    - 2014-06-27: Created
    - 2014-10-17: Updated by mlr to fix regex error.
    - 2015-06-04: Updated by bwc so regex catches comma, period, or
    whitespaces as separator. Simplified by mlr to make regexes more semantic.
    - 2016-02-20: Updated by arderyp to handle strange format where multiple
    case names and docket numbers appear in anchor text for a single case pdf
    link. Multiple case names are concatenated, and docket numbers are
    concatenated with ',' delimiter
    - 2021-12-21: Updated for new web site, by flooie and satsuki-chan
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.nh.gov/content/api/documents"
        self.method = "GET"
        self.parameters = {
            "sort": "field_date_posted|desc",
            "page": "1",
            "size": "25",
            "purpose": "1331+undefined",
            "tag": "1206+",
        }

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            return super()._download(request_dict)
        resp = self.request["session"].get(self.url, params=self.parameters)
        return resp.json()

    def _process_html(self) -> None:
        for op in self.html["data"]:
            docket, name = op["documentName"].split(",", 1)
            date = op["documentPosted"]
            url = re.findall(r"(http.*docu.*\.pdf)", op["documentContent"])[0]
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "status": "Published",
                    "url": url,
                }
            )
