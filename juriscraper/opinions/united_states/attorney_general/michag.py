"""
Scraper for Michigan Attorney General
CourtID: michag
Court Short Name: Michigan AG
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
        self.url = "https://www.ag.state.mi.us/opinion/op_allbydate.aspx"
        self.seeds = []

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//a/..")[5:]:
            docket = row.xpath(".//a/text()")[0]
            url = row.xpath(".//a/@href")[0]
            date = row.xpath(".//span/text()")
            if not date:
                continue
            date = date[0]
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": f"AG Opinion - {docket}",
                    "date": date,
                }
            )
