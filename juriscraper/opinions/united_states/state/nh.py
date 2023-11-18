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
    - 2021-12-29: Updated for new web site, by flooie and satsuki-chan
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.nh.gov/content/api/documents?iterate_nodes=true&q=%40field_document_subcategory%7C%3D%7C2256%40field_document_purpose%7C%3D%7C1331&sort=field_date_posted%7Cdesc%7CALLOW_NULLS&filter_mode=exclusive&page=1&size=25"
        self.status = "Published"

    def _download(self):
        if self.test_mode_enabled():
            import json

            return json.load(open(self.url))
        return (
            self.request["session"]
            .get(
                self.url,
                headers=self.request["headers"],
                verify=self.request["verify"],
                timeout=60,
            )
            .json()
        )

    def _process_html(self) -> None:
        for case in self.html["data"]:
            url = case["fields"]["field_document_file"]["0"]["fields"]["uri"][
                0
            ].split("//")[1]
            if "," not in case["title"]:
                continue
            docket, name = case["title"].split(",", 1)
            self.cases.append(
                {
                    "name": name.strip(),
                    "docket": docket.strip(),
                    "date": case["fields"]["field_date_posted"][0],
                    "url": f"https://www.courts.nh.gov/sites/g/files/ehbemt471/files/{url}",
                }
            )
