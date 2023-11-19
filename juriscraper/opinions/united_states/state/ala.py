"""
Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Alabama
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
 - 2023-011-14: Alabama no longer uses page or use selenium.
"""

import json

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_str = "68f021c4-6a44-4735-9a76-5360b2e8af13"

    def _build_url(self, court_str):
        return f"https://publicportal-api.alappeals.gov/courts/cms/publications?courtID={court_str}&page=0&size=25&sort=publicationDate%2Cdesc"

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            with open(self.url) as file:
                self.json = json.load(file)
        else:
            self.url = self._build_url(self.court_str)
            self.json = super()._download()

    def _process_html(self):
        for item in self.json["_embedded"]["results"][:1]:
            date_filed = item["scheduledDate"][:10]
            for publicationItem in item["publicationItems"]:
                if not publicationItem.get("documents", []):
                    continue

                url = f"https://publicportal-api.alappeals.gov/courts/{self.court_str}/cms/case/{publicationItem['caseInstanceUUID']}/docketentrydocuments/{publicationItem['documents'][0]['documentLinkUUID']}"
                docket = publicationItem["caseNumber"]
                author = publicationItem["groupName"]
                name = publicationItem["title"]
                self.cases.append(
                    {
                        "date": date_filed,
                        "name": name,
                        "docket": docket,
                        "status": "Published",
                        "url": url,
                        "judge": author,
                    }
                )
