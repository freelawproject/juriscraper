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
"""
from lxml import html

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca2.uscourts.gov/decisions"
        self.method = "POST"
        self.base_xpath = '//tr[contains(.//a/@href, "mp3")]'
        self.parameters = {
            "IW_SORT": "-DATE",
            "IW_BATCHSIZE": "50",
            "IW_FILTER_DATE_BEFORE": "",
            "IW_FILTER_DATE_AFTER": "NaNNaNNaN",
            "IW_FIELD_TEXT": "*",
            "IW_DATABASE": "Oral Args",
            "opinion": "*",
        }

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            self.html = super()._download()
            return self.html
        r = self.request["session"].post(self.url, params=self.parameters)
        return html.fromstring(r.content)

    def _process_html(self):
        for row in self.html.xpath("//table[@border='1']"):
            link = row.xpath(".//a")[0].get("href")
            docket = row.xpath(".//a/nobr/text()")[0]
            name, date = row.xpath(".//td/text()")
            self.cases.append(
                {"docket": docket, "url": link, "name": name, "date": date}
            )
