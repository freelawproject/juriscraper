"""
Scraper for Illinois Attorney General
CourtID: illinoisag
Court Short Name: Illinois AG
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
        self.year = datetime.date.today().year
        self.url = f"https://ag.state.il.us/opinions/{self.year}/index.html"

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//tr/td/ul/li"):
            url = row.xpath(".//a/@href")[0]
            name = row.xpath(".//a")[0].text_content()
            docket = name
            summary = row.xpath(".//strong/text()")[0]
            date = row.text_content().split("(")[1].split(")")[0]
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "url": url,
                    "summary": summary,
                    "date": date,
                }
            )
