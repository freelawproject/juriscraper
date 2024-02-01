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

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.url = "https://www.courts.state.co.us/Courts/Court_of_Appeals/Case_Announcements/Index.cfm"
        self.status = None

    def _process_html(self) -> None:
        """Parses html into case dictionaries

        :return None
        """
        if self.test_mode_enabled():
            self.year = "2023"

        date_xpath = (
            "//span[text()='Future Case Announcements']/following-sibling::p"
        )
        date = self.html.xpath(date_xpath)[0].text_content()

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

            pattern = re.compile(r"\b[0-9A-Z& ]{5,}\b")
            matches = re.findall(pattern, row.text_content())
            if not matches:
                continue

            docket = matches[0].strip()
            name = row.text_content().replace(docket, "").strip()
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "status": self.status,
                    "url": f"https://www.courts.state.co.us/Courts/Court_of_Appeals/Opinion/{self.year}/{docket}-PD.pdf",
                }
            )
