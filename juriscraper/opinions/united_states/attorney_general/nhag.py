"""
Scraper for New Hampshire Attorney General
CourtID: nhag
Court Short Name: New Hampshire AG
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
        self.url = "https://www.doj.nh.gov/public-documents/opinions.htm"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//a"):
            if (
                row.xpath(".//@href")
                and "/documents/" not in row.xpath(".//@href")[0]
            ):
                continue
            url = row.xpath(".//@href")
            if not url:
                continue

            docket = row.text_content()
            name = docket
            self.cases.append(
                {
                    "url": url[0],
                    "docket": docket,
                    "name": name,
                    "date": url[0].split("opinion-")[1][:4],
                    "date_filed_is_approximate": True,
                }
            )
