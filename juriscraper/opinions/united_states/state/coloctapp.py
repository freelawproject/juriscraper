"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.

History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by William E. Palin
    - 2023-11-04: Updated by Honey K. Joule
    - 2023-11-19: Updated by William E. Palin
"""

import datetime
import re

from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.url = f"https://www.courts.state.co.us/Courts/Court_of_Appeals/Case_Announcements/Index.cfm"
        self.status = None

    def _process_html(self):
        date = self.html.xpath("//div/p/a/text()")[0]
        for row in self.html.xpath("//p"):
            modified_string = re.sub(r"\s", "", row.text_content())
            if "PUBLISHED" == modified_string[:9]:
                self.status = "Published"
                continue
            if "UNPUBLISHED" == modified_string[:11]:
                self.status = None
                continue
            if not self.status:
                continue
            docket, name = row.text_content().split(" ", 1)
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "status": self.status,
                    "url": f"https://www.courts.state.co.us/Courts/Court_of_Appeals/Opinion/{self.year}/{docket}-PD.pdf",
                }
            )
