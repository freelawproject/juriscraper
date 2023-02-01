"""
Scraper for Missouri Attorney General
CourtID: moag
Court Short Name: Missouri AG
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
        self.url = f"https://ago.mo.gov/other-resources/ag-opinions/opinions-2020---2029/"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//tr/td/.."):
            url = row.xpath(".//td/a/@href")[0]
            docket = row.xpath(".//td/a/text()")[0]
            date = row.xpath(".//td")[1].text_content()
            summary = row.xpath(".//td/text()")[-1]
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": f"OPINION LETTER NO. {docket}",
                    "summary": summary,
                    "date": f"{date}, {docket.split('-')[1]}",
                }
            )
