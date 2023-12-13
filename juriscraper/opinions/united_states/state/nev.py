"""Scraper for Nevada Supreme Court
CourtID: nev

History:
    - 2023-12-13: Updated by William E. Palin
"""


from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/AdvanceOpinions"
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

    def _process_html(self):
        for case in self.html:
            if "COA" in case["caseNumber"]:
                continue
            self.cases.append(
                {
                    "name": case["caseTitle"],
                    "docket": case["caseNumber"],
                    "date": case["date"],
                    "url": case["docurl"],
                }
            )
