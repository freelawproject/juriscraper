"""
Scraper for Massachusetts Appeals Court Rule 23.0 (formerly Rule 1:28)
CourtID: massappct
Court Short Name: Mass App Ct
Author: William Palin
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer:
Date: 2020-02-27
"""

from datetime import date, timedelta, datetime
from urllib.parse import urlencode

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backwards_days = 14
        self.court_id = self.__module__
        self.DEFAULT_PAGE_SIZE = 1
        self.DEFAULT_PAGE_NUMBER = 1
        self.expected_content_types = ["text"]

    def make_url(self,start_date, end_date, page_no, total_pages) -> str:
        """Build the urls to query

        :return: The url parameters (encoded)
        """
        first_date = start_date.strftime("%m/%d/%Y")
        end_date = end_date.strftime("%m/%d/%Y")
        self.parameters = (
            ("Action", "search"),
            ("DocketNumber", ""),
            ("PartyName", ""),
            ("ReleaseDateFrom", first_date),
            ("ReleaseDateTo", end_date),
            ("Keywords", ""),
            (
                "SortColumnName",
                [
                    "Release Date Descending Order",
                    "Release Date Descending Order",
                ],
            ),
            ("SortOrder", ""),
            ("CurrentPageNo", str(page_no)),
            ("Pages", str(total_pages)),
            ("PageSize", "100"),
        )
        return f"{self.base}/?{urlencode(self.parameters)}"

    def _process_html(self) -> None:
        """Process the data

        :return: None
        """
        for row in self.html.xpath("//div[@data-rowtype]"):
            docket, name, date = row.xpath(
                ".//div[@class='col-md-7 font-bold']/text()"
            )
            path = row.xpath(".//div/div/a/@href")[0]
            self.cases.append(
                {
                    "date": date.strip(),
                    "docket": [docket.strip()],
                    "name": titlecase(name.strip()),
                    "url": path,
                    "status": "Unpublished",
                }
            )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.from_date=start_date
        self.to_date=end_date
        self.base = "https://128archive.com"
        self.url = self.make_url(start_date,end_date,self.DEFAULT_PAGE_NUMBER,self.DEFAULT_PAGE_SIZE)
        self.html=self._download()
        panel = self.html.xpath("//h3[@class='panel-title']/span[2]")
        txt = str(panel[0].text)
        total_pages = int(txt[txt.index('of') + 2:txt.__len__()].strip()) // 100 + 1
        page=1
        while page<=total_pages:
            self.downloader_executed=False
            self.url=self.make_url(start_date,end_date,page,total_pages)
            self.parse()
            page=page+1
        return 0

    def get_court_name(self):
        return "Massachusetts Appeals Court"

    def get_class_name(self):
        return "massappct_u"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Massachusetts"
