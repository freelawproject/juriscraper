"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig <asadullahbeg@outlook.com>
History:
    - 2014-07-11: created
    - 2014-08-08, mlr: updated to fix InsanityError on case_dates
    - 2014-09-18, mlr: updated XPath to fix InsanityError on docket_numbers
    - 2015-06-17, mlr: made it more lenient about date formatting
    - 2016-07-21, arderyp: fixed to handle altered site format
    - 2017-01-10, arderyp: restructured to handle new format use case that includes opinions without dates and flagged for 'future' publication
    - 2022-02-02, satsuki-chan: Fixed docket and name separator, changed super class to OpinionSiteLinear
    - 2023-11-04, flooie: Fix scraper
"""

import re
from datetime import date

from juriscraper.lib.network_utils import SSLAdapter
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().strftime("%y")
        self.url = f"http://www.jud.ct.gov/external/supapp/archiveAROsup{self.year}.htm"
        self.status = "Published"
        self._mount_ssl_adapter()

    def _mount_ssl_adapter(self):
        """Configures and mounts an SSL adapter to a given session

        :return: None
        """
        self.request["session"].mount(
            "https://", SSLAdapter(ciphers="AES256-SHA256")
        )

    def fetch_docket_numbers(self, text):
        """Find docket numbers in row

        :param text: the row text
        :return: return a list of docket numbers matches
        """
        matches = re.findall(r"SC\d+", text)
        return matches

    def make_case_name(self, cleaned_text, url):
        """Generate the case name identifying opinion type

        :param cleaned_text: the row text without excess whitespace
        :param url: the url of the document
        :return: Update case name
        """
        name = cleaned_text.split("-", 1)[1].strip()
        if url[-5].upper() == "A":
            name = f"{name} (Concurrence)"
        elif url[-5].upper() == "B":
            name = f"{name} (Second Concurrence)"
        elif url[-5].upper() == "E":
            name = f"{name} (Dissent)"
        return name.strip()

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        begin = False
        date = None
        for row in self.html.xpath(
            "//table[@id='AutoNumber1']//*[text() and not(./*[text()])]"
        ):
            if "Published" in row.text_content():
                begin = True
            if not begin:
                continue
            if "Published" in row.text_content():
                date = row.text_content().split("of")[-1][:-1].strip()
                continue
            if row.text_content().strip() == "Return to Top":
                return
            if row.tag == "a":
                url = row.get("href")
                text = row.getparent().text_content().strip()
                cleaned_text = re.sub(r"\s+", " ", text)
                name = self.make_case_name(cleaned_text, url)
                docket = self.fetch_docket_numbers(cleaned_text)

                if not date:
                    continue
                self.cases.append(
                    {
                        "date": date,
                        "url": url,
                        "docket": ",".join(docket),
                        "name": name,
                    }
                )
