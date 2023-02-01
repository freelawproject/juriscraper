"""
Scraper for West Virginia Attorney General
CourtID: wvaag
Court Short Name: WVA AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
from datetime import datetime as dt

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://ago.wv.gov/publicresources/Attorney%20General%20Opinions/Pages/default.aspx"
        self.year = dt.today().year

    def _process_html(self):
        """Process html

        :return: None
        """
        if not self.test_mode_enabled():
            self.url = self.html.xpath(".//a[@class='button button2']/@href")[
                0
            ]
            self.html = super()._download()

        for row in self.html.xpath(".//a[contains(@href, '.pdf')]"):
            url = row.xpath(".//@href")[0]
            name = row.text_content().split("(")[0]
            date = url.split("/")[-1].split("%20")[0]
            self.cases.append(
                {"url": url, "docket": "", "name": name, "date": date}
            )
