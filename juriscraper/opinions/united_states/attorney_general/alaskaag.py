"""
Scraper for Alaska AG
CourtID: alaskaag
Court Short Name: Alaska AG
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
        self.url = "https://law.alaska.gov/doclibrary/opinions-index/opinions_chron.html"

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//li/a[contains(@href, '.pdf')]/.."):
            date, other = row.text_content().split(" ", 1)
            name = other.split("(PDF")[0].strip(" -")
            url = row.xpath(".//a/@href")[0]
            dn = url.split("_")[-1][:-4]
            docket = f"AGO No. {dn}"
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "url": url,
                    "date": date,
                }
            )
