"""Scraper for Public Interest Cases for the CADC
CourtID: cadc
Court Short Name: Court of Appeals of the District of Columbia
Author: flooie
History:
  2021-12-18: Created by flooie
"""


from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.cadc.uscourts.gov/internet/orders.nsf"
        self.base = "https://www.cadc.uscourts.gov"
        self.court_id = self.__module__

    def _process_html(self):
        """Iterate over the public interest cases.

        :return: None
        """
        for row in self.html.xpath(".//div[@class='row-entry']"):
            url = row.xpath(".//a/@href")[0]
            docket = row.xpath(".//a/span/text()")[0]
            name = row.xpath(".//div[@class='column-two']/div[1]/text()")[
                0
            ].strip()
            date = row.xpath(".//date/text()")[0]
            self.cases.append(
                {
                    "date": date,
                    "url": f"https:{url}",
                    "docket": docket,
                    "name": name,
                    "status": "Published",
                }
            )
