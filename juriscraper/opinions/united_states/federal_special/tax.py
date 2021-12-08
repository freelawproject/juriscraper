# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://public-api-green.dawson.ustaxcourt.gov/public-api/todays-opinions/1/FILING_DATE_DESC"
        self.court_id = self.__module__

    def _process_html(self) -> None:
        """Process the html

        Iterate over each item on the page collecting our data.
        return: None
        """
        case_json = self.request["response"].json()
        for case in case_json["results"][:1]:
            url = self._get_url(case["docketNumber"], case["docketEntryId"])
            status = (
                "Precedential"
                if case["documentType"] == "T.C. Opinion"
                else "Nonprecedential"
            )
            self.cases.append(
                {
                    "judge": case["signedJudgeName"],
                    "date": case["filingDate"][:10],
                    "docket": case["docketNumber"],
                    "url": url,
                    "name": titlecase(case["caseCaption"]),
                    "status": status,
                }
            )

    def _get_url(self, docket_number: str, docketEntryId: str) -> str:
        """Fetch the PDF URL with AWS API key

        param docket_number: The Docket number
        param docketEntryId: The docket entry key for the document
        return:
        """
        get_public_pdf_url = f"https://public-api-green.dawson.ustaxcourt.gov/public-api/{docket_number}/{docketEntryId}/public-document-download-url"
        self.url = get_public_pdf_url
        pdf_url = super()._download()["url"]
        return pdf_url
