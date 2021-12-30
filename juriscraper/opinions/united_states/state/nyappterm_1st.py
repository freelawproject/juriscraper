# Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY

import re
from datetime import date, timedelta
from typing import Any, Dict

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Appellate Term, 1st Dept"
        self.court_id = self.__module__
        self.url = "https://iapps.courts.state.ny.us/lawReporting/Search?searchType=opinion"
        self.method = "POST"
        self._set_parameters()

    def _set_parameters(self):
        self.parameters = {
            "rbOpinionMotion": "opinion",
            "Pty": "",
            "and_or": "and",
            "dtStartDate": (date.today() - timedelta(days=30)).strftime(
                "%m/%d/%Y"
            ),
            "dtEndDate": date.today().strftime("%m/%d/%Y"),
            "court": self.court,
            "docket": "",
            "judge": "",
            "slipYear": "",
            "slipNo": "",
            "OffVol": "",
            "Rptr": "",
            "OffPage": "",
            "fullText": "",
            "and_or2": "and",
            "Order_By": "Party Name",
            "Submit": "Find",
            "hidden1": "",
            "hidden2": "",
        }

    def _process_html(self):
        for row in self.html.xpath(".//table")[-1].xpath(".//tr")[1:]:
            docket = " ".join(row.xpath("./td[5]//text()"))
            citation = " ".join(row.xpath("./td[4]//text()"))
            url = row.xpath(".//a")[0].get("href")
            url = re.findall(r"(http.*htm)", url)[0]
            self.cases.append(
                {
                    "name": row.xpath(".//td")[0].text_content(),
                    "date": row.xpath(".//td")[1].text_content(),
                    "url": url,
                    "status": "Published"
                    if "(U)" not in docket
                    else "Unpublished",
                    "docket": "",
                    "neutral_citation": docket,
                    "west_citation": citation,
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        # Ny App Term 1st Dept. 2nd and Sup Ct all have different varying
        # docket number types.
        # ie. 123413/03 vs. 51706 vs. 2003-718 Q C or 2003-1288 K C

        dockets = re.findall(
            r"^(\d+\/\d+)|^(\d{5,})|^(\d+-\d+ \w+\s\w+)", scraped_text
        )
        dockets = [list(filter(None, x)) for x in dockets]
        metadata = {
            "Docket": {
                "docket_number": dockets[0][0] if dockets else "",
            },
        }
        return metadata
