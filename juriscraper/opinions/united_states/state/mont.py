# Author: Michael Lissner
# Date created: 2013-06-03
# Date updated: 2020-02-25

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://juddocumentservice.mt.gov/getDailyOrders"
        self.download_base = (
            "https://juddocumentservice.mt.gov/getDocByCTrackId?DocId="
        )

    def _get_download_urls(self):
        return [f"{self.download_base}{row['cTrackId']}" for row in self.html]

    def _get_case_names(self):
        return [f"{row['title']}" for row in self.html]

    def _get_case_dates(self):
        return [convert_date_string(f"{row['fileDate']}") for row in self.html]

    def _get_precedential_statuses(self):
        return [
            "Published"
            if "Published" in row["documentDescription"]
            else "Unpublished"
            for row in self.html
        ]

    def _get_docket_numbers(self):
        return [f"{row['caseNumber']}" for row in self.html]

    def _get_summaries(self):
        return [f"{row['documentDescription']}" for row in self.html]

    def _get_nature_of_suit(self):
        natures = []

        for docket in self.docket_numbers:
            if docket.startswith("DA"):
                nature = "Direct Appeal"
            elif docket.startswith("OP"):
                nature = "Original Proceeding"
            elif docket.startswith("PR"):
                nature = "Professional Regulation"
            elif docket.startswith("AF"):
                nature = "Administrative File"
            else:
                nature = "Unknown"
            natures.append(nature)
        return natures
