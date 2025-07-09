"""
Scraper for Indiana Supreme Court
CourtID: ind
Court Short Name: Ind.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-03: Created by Jon Andersen
    2025-07-09: Updated bt luism add new fields for lower court details and judge names
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "Supreme Court"
        self.status = "Published"
        self.url = "https://public.courts.in.gov/Decisions/api/Search"

    def _process_html(self):
        for case in self.html:
            if case["courtName"] != self.court_name:
                continue
            self.cases.append(
                {
                    "name": case["style"],
                    "docket": case["caseNumber"],
                    "date": case["date"],
                    "url": f"https://public.courts.in.gov/Decisions/{case['opinionUrl']}",
                    "disposition": case["decision"],
                    "lower_court": ", ".join(
                        court["name"]
                        for court in case["courts"]
                        if court["name"] != self.court_name
                    ),
                    "lower_court_number": ", ".join(
                        court["number"]
                        for court in case["courts"]
                        if court["name"] != self.court_name
                    ),
                    "judge": ", ".join(
                        vote["judge"].split(",")[-1].replace(".", "")
                        for vote in case["opinion"]["votes"]
                    ),
                }
            )
