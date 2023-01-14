# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1
import json
from datetime import date, timedelta

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://public-api-blue.dawson.ustaxcourt.gov/public-api/opinion-search"
        self.court_id = self.__module__
        self.td = date.today()
        today = self.td.strftime("%m/%d/%Y")
        self.method = "GET"

        last_month = (self.td - timedelta(days=31)).strftime("%m/%d/%Y")
        self.params = {
            "dateRange": "customDates",
            "startDate": last_month,
            "endDate": today,
            "opinionTypes": "MOP,SOP,TCOP",
        }

    def _download(self, request_dict={}):
        print(self.url)
        if self.test_mode_enabled():
            self.json = json.load(open(self.url))
        else:
            self.json = (
                self.request["session"]
                .get(
                    self.url,
                    params=self.params,
                )
                .json()
            )

    def _process_html(self) -> None:
        """Process the html

        Iterate over each item on the page collecting our data.
        return: None
        """
        for case in self.json:
            url = self._get_url(case["docketNumber"], case["docketEntryId"])
            status = (
                "Published"
                if case["documentType"] == "T.C. Opinion"
                else "Unpublished"
            )
            self.cases.append(
                {
                    "judge": case.get("signedJudgeName", ""),
                    "date": case["filingDate"][:10],
                    "docket": case["docketNumber"],
                    "url": url,
                    "name": titlecase(case["caseCaption"]),
                    "status": status,
                }
            )

    def _get_url(self, docket_number: str, docketEntryId: str) -> str:
        """Fetch the PDF URL with AWS API key

        param docket_number: The docket number
        param docketEntryId: The docket entry id
        return: The URL to the PDF
        """
        self.url = f"https://public-api-blue.dawson.ustaxcourt.gov/public-api/{docket_number}/{docketEntryId}/public-document-download-url"
        if self.test_mode_enabled():
            # Don't fetch urls when running tests.  Because it requires
            # a second api request.
            return self.url
        pdf_url = super()._download()["url"]
        return pdf_url
