"""
Scraper for Kansas Attorney General
CourtID: ksag
Court Short Name: Kansas AG
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
        self.url = f"https://ag.ks.gov/media-center/ag-opinions"

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//td/a[contains(@href, '.pdf')]/.."):
            url = row.xpath(".//a/@href")[0]
            name = row.xpath(".//a/text()")[0]
            row_content = [
                x.strip() for x in row.xpath(".//text()") if x.strip()
            ]
            self.cases.append(
                {
                    "name": name,
                    "docket": name,
                    "url": url,
                    "summary": row_content[-1],
                    "date": row.getnext().text_content(),
                }
            )
