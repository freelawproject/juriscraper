"""Scraper for the Maryland Attorney General
CourtID: mdag
Court Short Name: Maryland Attorney General
"""

import re
from datetime import date

from dateutil import parser

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://oag.maryland.gov/resources-info/_api/web/lists/getbytitle('Search-Opinions')/items?$top=100&$select=Title,Year,Summary,Attachment,Created_x0020_Date&$orderby=Year desc"
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
            date_filed = re.findall(r"\d{4}-\d{2}-\d{2}", datetime_string)[0]

            docket_number = row["Title"]
            title = "Maryland Attorney General Opinion " + docket_number
            year = row["Year"]
            attachment = row["Attachment"]


            citation = ""
            citation_pattern = r'(\d+)\s*OAG\s*(\d+)'
            if match := re.search(citation_pattern, docket_number):
                citation = f"{match.group(1)} Op. Atty Gen. Md. {match.group(2)}"

            self.cases.append(
                {
                    "docket": docket_number,
                    "name": title,
                    "url": f"https://oag.maryland.gov/resources-info/Documents/pdfs/Opinions/{year}/{attachment}.pdf",
                    "date": date_filed,
                    "date_filed_is_approximate": True,
                    "citation": citation,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract the exact date(s) from the scraped text."""
        pattern = r"([A-Z][a-z]+ \d{1,2}, \d{4})"

        if matches := re.findall(pattern, scraped_text):
            date_string = parser.parse(matches[0]).strftime("%Y-%m-%d")

            # Find the paragraph before the date
            date_index = scraped_text.find(matches[0])
            before_text = scraped_text[:date_index].rstrip()
            paragraphs = [p for p in before_text.split('\n\n') if p.strip()]

            syllabus = ""
            if paragraphs:
                last_paragraph = paragraphs[-1]
                first_newline = last_paragraph.find('\n')
                if first_newline != -1:
                    syllabus_text = last_paragraph[first_newline + 1 :]
                else:
                    syllabus_text = last_paragraph
                syllabus = re.sub(r"\s{2,}", " ", syllabus_text.replace("\n", "").strip())
            return {
                "OpinionCluster": {
                    "date_filed": date_string,
                    "date_filed_is_approximate": False,
                    "syllabus": titlecase(syllabus),
                }
            }
        return {}
