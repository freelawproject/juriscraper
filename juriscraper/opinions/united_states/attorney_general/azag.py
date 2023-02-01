"""
Scraper for Arizona Attorney General
CourtID: azaag
Court Short Name: Arizona AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        year = datetime.date.today().year
        # year = 2022
        self.url = f"https://www.azag.gov/opinions/{year}"

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//div/div/span/a/../../.."):
            url = row.xpath(".//a/@href")[0]
            name = row.xpath(".//a/text()")[0]
            date = row.xpath(".//time/text()")
            if not date:
                continue
            date = str(
                datetime.datetime.strptime(date[0], "%A, %B %d, %Y").date()
            )
            docket = url.split("/")[-1].upper()
            self.cases.append(
                {
                    "name": name,
                    "docket": f"No. {docket}",
                    "url": url,
                    "date": date,
                }
            )
