"""Scraper for Second Circuit
CourtID: ca2
Author: MLR
Reviewer: MLR
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov
History:
  2016-09-09: Created by MLR
  2023-11-21: Fixed by flooie
  2023-12-11: Fixed by quevon24
  2026-01-21:Fixed by Luis-manzur
"""

import re
from datetime import datetime
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    base_url = "http://ww3.ca2.uscourts.gov"
    docket_regex = re.compile(r"\d{2}-\d{2,4}")
    date_regex = re.compile(r"\d{1,2}-\d{1,2}-\d{2}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}/decisions"

        self.method = "POST"
        self.expected_content_types = ["audio/mpeg3"]
        self.parameters = self.request["parameters"]["params"] = {
            "IW_SORT": "-DATE",
            "IW_BATCHSIZE": "50",
            "IW_FILTER_DATE_BEFORE": "",
            "IW_FILTER_DATE_AFTER": "NaNNaNNaN",
            "IW_FIELD_TEXT": "*",
            "IW_DATABASE": "Oral Args",
            "opinion": "*",
        }

        self.back_scrape_iterable = ["placeholder"]

    def _process_html(self):
        for row in self.html.xpath("//table[@border='1']"):
            link = row.xpath(".//a")[0].get("href")

            if ".mp3" not in link:
                logger.info("Skipping row without mp3 link: %s", link)
                continue  # skip bad data
            url = urljoin(self.base_url, link)

            docket = row.xpath(".//a/nobr/text()")[0]

            try: # Row may have empty date column
                name, date = row.xpath(".//td/text()")
            except ValueError:
                name = row.xpath(".//td/text()")[0]
                date = (
                    self.cases[-1]["date"]
                    if self.cases
                    else datetime.now().strftime("%-m-%d-%y")
                )  # use last case date

            if not self.docket_regex.search(docket): # Row may have mixed columns
                if self.date_regex.search(docket):
                    date = docket
                    docket = self.docket_regex.search(link).group(0)
                else:
                    docket = name
                    name = row.xpath(".//a/nobr/text()")[0]

            if docket == "GMT20230614-175136_Recording":
                continue  # skip bad data

            self.cases.append(
                {
                    "docket": docket,
                    "url": url,
                    "name": name,
                    "date": date,
                }
            )

    def _download_backwards(self, d):
        # This backscraper is hardcoded, but it will
        # work for the set number of pages
        self.method = "GET"
        for i in range(1, 33):
            self.url = f"{self.base_url}/decisions/isysquery/19342efa-bb49-4684-a054-875324b58eb9/{(i * 10) - 9}-{i * 10}/list/"
            self.html = self._download()
            self._process_html()
