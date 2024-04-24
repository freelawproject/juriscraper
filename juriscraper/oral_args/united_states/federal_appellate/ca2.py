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
"""

from lxml import html

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "http://www.ca2.uscourts.gov"
        self.url = f"{self.base_url}/decisions"
        self.method = "POST"
        self.expected_content_types = ["audio/mpeg3"]
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
        self.backscraper = False
        self.back_scrape_iterable = ["placeholder"]

    def _process_html(self):
        for row in self.html.xpath("//table[@border='1']"):
            link = row.xpath(".//a")[0].get("href")
            if ".mp3" not in link:
                continue  # skip bad data
            docket = row.xpath(".//a/nobr/text()")[0]
            name, date = row.xpath(".//td/text()")
            url = self._build_url(link)
            if docket == "GMT20230614-175136_Recording":
                continue  # skip bad data
            self.cases.append(
                {"docket": docket, "url": url, "name": name, "date": date}
            )

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            self.html = super()._download()
            return self.html
        if self.backscraper:
            return super()._download()
        r = self.request["session"].post(self.url, params=self.parameters)
        return html.fromstring(r.content)

    def _build_url(self, link):
        if self.backscraper:
            url = link
        else:
            url = f"{self.base_url}{link}"
        return url

    def _download_backwards(self, d):
        self.backscraper = True
        self.method = "GET"
        for i in range(1, 33):
            self.url = f"{self.base_url}/decisions/isysquery/19342efa-bb49-4684-a054-875324b58eb9/{(i*10)-9}-{i*10}/list/"
            self.html = self._download()
            self._process_html()
