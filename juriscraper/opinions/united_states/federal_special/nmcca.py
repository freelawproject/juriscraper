"""Scraper for the Navy-Marine Corps Court of Criminal Appeals
CourtID: nmcca
Court Short Name:
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://www.jag.navy.mil/api/tables/decisions-opinions/data/"
        )
        self.court_id = self.__module__
        self.request["verify"] = False

    def _process_html(self):
        for row in self.html["results"]:
            date, docket, notes, name = list(row["data"].values())
            url = row["documents"][0]["document"]["download_url"]
            if notes == "Unpublished":
                status = "Unpublished"
            else:
                status = "Published"
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "status": status,
                    "docket": docket,
                }
            )
