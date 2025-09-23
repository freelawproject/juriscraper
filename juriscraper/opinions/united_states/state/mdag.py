"""Scraper for the Maryland Attorney General
CourtID: mdag
Court Short Name: Maryland Attorney General
"""

import re
from datetime import date

from dateutil import parser

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://oag.maryland.gov/resources-info/_api/web/lists/getbytitle('Search-Opinions')/items?$top=100&$select=Title,Year,Summary,Attachment,Created_x0020_Date"
        )
        self.year = date.today().year

        self.method = "GET"
        self.request["headers"] = {
            "Accept": "application/json;odata=verbose",
        }
        self.needs_special_headers = True
        self.status = "Published"

    def _process_html(self):
        self.json = self.html
        for row in self.json["d"]["results"]:

            # created_x0020_date looks like this 0;#2021-11-09 14:29:09
            datetime_string = row["Created_x0020_Date"]
            date = re.findall(r"\d{4}-\d{2}-\d{2}", datetime_string)[0]
            title = row["Title"]
            year = row["Year"]
            attachment = row["Attachment"]

            self.cases.append(
                {
                    "docket": title,
                    "summary": row["Summary"],
                    "name": title,
                    "url": f"https://oag.maryland.gov/resources-info/Documents/pdfs/Opinions/{year}/{attachment}.pdf",
                    "date": date,
                    "date_filed_is_approximate": True,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract the exact date(s) from the scraped text."""
        pattern = r"([A-Z][a-z]+ \d{1,2}, \d{4})"

        if matches:= re.findall(pattern, scraped_text):
            date_string = parser.parse(matches[0]).strftime("%Y-%m-%d")
            # Return the first date found
            return {
                "OpinionCluster": {
                    "date_filed": date_string,
                    "date_filed_is_approximate": False,
                }
            }
        else:
            return {}
