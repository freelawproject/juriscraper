"""
Scraper for Montana Attorney General
CourtID: montag
Court Short Name: Montana AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://dojmt.gov/agooffice/attorney-generals-opinions/"

    def _process_html(self):
        """Process html

        :return: None
        """
        if not self.test_mode_enabled():
            self.url = self.html.xpath(
                ".//li[contains(./@class, 'page_item')]/a/@href"
            )[0]
            self.html = super()._download()

        # from lxml.html import tostring
        # print(tostring(self.html).decode())

        for row in self.html.xpath(".//tr"):
            if not row.xpath(".//td/text()"):
                continue
            url = row.xpath(".//a/@href")[0]
            docket = row.xpath(".//a/text()")[0]
            summary, date = row.xpath(".//td/text()")
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": docket,
                    "summary": summary,
                    "date": date,
                }
            )
