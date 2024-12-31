"""
CourtID: cadc
Court Short Name: Court of Appeals of the District of Columbia
Author: mlissner
History:
    2014-07-31, mlissner: commited first version
    2024-12-31, grossir: Implemented new site
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # https://media.cadc.uscourts.gov/opinions/
        self.url = "https://media.cadc.uscourts.gov/opinions/bydate/recent"
        self.status = "Published"

    def _process_html(self):
        link_xpath = "a[contains(@href, '.pdf')]"
        for row in self.html.xpath(f"//div[div[div[div[{link_xpath}]]]]"):
            self.cases.append(
                {
                    "url": row.xpath(f".//{link_xpath}/@href")[0],
                    "docket": row.xpath(f".//{link_xpath}/text()")[0],
                    "name": row.xpath("div[2]/div/div/text()")[0],
                    "date": row.xpath(".//span/text()")[-1],
                }
            )
