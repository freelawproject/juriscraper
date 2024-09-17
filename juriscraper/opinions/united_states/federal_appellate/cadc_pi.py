"""Scraper for Public Interest Cases for the CADC
CourtID: cadc
Court Short Name: Court of Appeals of the District of Columbia
Author: flooie
History:
  2021-12-18: Created by flooie
  2023-01-12: Fixed requests.exceptions.InvalidURL error by grossir
"""
from datetime import datetime
from time import strftime
from urllib.parse import urljoin

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.cadc.uscourts.gov/internet/orders.nsf"
        self.base = "https://www.cadc.uscourts.gov"
        self.court_id = self.__module__

    def _process_html(self) -> None:
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
            date_obj = datetime.strptime(date,'%m/%d/%Y')
            formatted_date = date_obj.strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(formatted_date, self.crawled_till)
            if (res == 1):
                self.crawled_till = formatted_date
            self.cases.append(
                {
                    "date": date,
                    "url": urljoin("https:", url),
                    "docket": docket,
                    "name": name,
                    "status": "Published",
                }
            )
    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0
