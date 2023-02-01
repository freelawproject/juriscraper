"""
Scraper for Washington D.C. Attorney General
CourtID: dcag
Court Short Name: DC AG
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
        self.url = "https://oag.dc.gov/about-oag/our-structure-divisions/legal-counsel-division/opinions-attorney-general"

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//tbody/tr"):
            date = row.xpath(".//td")[0].text_content().strip()
            url = row.xpath(".//td")[1].xpath(".//a/@href")
            if not url:
                continue
            name = row.xpath(".//td")[1].xpath(".//a/span/span/text()")[0]
            self.cases.append(
                {"url": url[0], "docket": "", "name": name, "date": date}
            )
