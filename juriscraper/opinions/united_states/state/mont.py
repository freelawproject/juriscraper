# Author: Michael Lissner
# Date created: 2013-06-03
# Date updated: 2020-02-25

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base = "https://juddocumentservice.mt.gov"
        self.url = f"{self.base}/getDailyOrders"
        self.download_base = f"{self.base}/getDocByCTrackId?DocId="
        self.expected_content_types = None
        self.cite_regex = r"((19|20)\d{2}\sMT\s\d{1,3}[A-Z]?)"

    def _process_html(self):
        for row in self.html:
            summary = row["documentDescription"]
            if not summary.startswith("Opinion"):
                # skip orders and just do opinions
                continue
            status = "Published" if "Published" in summary else "Unpublished"
            docket = row["caseNumber"]
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
            self.cases.append(
                {
                    "url": self.download_base + row["cTrackId"],
                    "status": status,
                    "date": row["fileDate"],
                    "name": row["title"],
                    "docket": docket,
                    "summary": summary,
                    "nature_of_suit": nature,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract citation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        first_text = scraped_text[:400]
        if match := re.search(self.cite_regex, first_text):
            return {"Citation": match.group(0)}
        return {}
