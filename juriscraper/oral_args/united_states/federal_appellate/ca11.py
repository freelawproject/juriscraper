"""Scraper for Eleventh Circuit of Appeals
CourtID: ca11
Court Short Name: ca11
Author: Jon Andersen
Reviewer: mlr
Date created: 28 Aug 2018
"""

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    base_url = "https://www.ca11.uscourts.gov/oral-argument-recordings"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.back_scrape_iterable = [i for i in range(0, 52)]

    def _process_html(self):
        for row in self.html.xpath("//tr[not(th)]"):
            # normalize docket numbers
            # get rid of "consolidated with" text
            # parse docket numbers like docketnum1 & docketnum2
            # also handle docketnum1\ndocketnum2\ndocketnum3
            # Return comma joined string like docketnum1, docketnum2
            docket = row.xpath("td[1]/text()")[0]
            docket = ", ".join(
                docket.strip()
                .upper()
                .replace("&", "\n")
                .replace(" AND ", "\n")
                .replace(",", "\n")
                .replace("CONS. WITH", "\n")
                .replace("CONSOLIDATED WITH", "\n")
                .split()
            )
            name = row.xpath("td[2]/text()")[0]
            date = row.xpath("td[3]/text()")[0]
            url = row.xpath("td[5]//@href")[0]
            self.cases.append(
                {"name": name, "url": url, "date": date, "docket": docket}
            )

    def _download_backwards(self, i):
        self.url = f"{self.base_url}?page={i}"
        self.html = self._download()
        self._process_html()
