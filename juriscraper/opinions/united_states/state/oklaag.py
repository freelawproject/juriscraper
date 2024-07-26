# Scraper for Oklahoma Attorney General Opinions
# CourtID: oklaag
# Court Short Name: OK
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

from datetime import datetime

from juriscraper.opinions.united_states.state import okla


class Site(okla.Site):
    # Inherit cleanup_content from Okla
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = datetime.today().year
        self.url = f"https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKAG&year={year}&level=1"
        self.status = "Published"
        self.expected_content_types = ["text/html"]

    def _process_html(self):
        for row in self.html.xpath("//div/p['@class=document']")[::-1]:
            if "OK" not in row.text_content() or "EMAIL" in row.text_content():
                continue
            citation, date, name = row.text_content().split(",", 2)
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "docket": "",
                    "url": row.xpath(".//a")[0].get("href"),
                    "citation": citation,
                }
            )
