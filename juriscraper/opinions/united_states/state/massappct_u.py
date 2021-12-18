"""
Scraper for Massachusetts Appeals Court Rule 23.0 (formerly Rule 1:28)
CourtID: massappct
Court Short Name: Mass App Ct
Author: William Palin
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer:
Date: 2020-02-27
"""

from datetime import date, timedelta
from urllib.parse import urlencode

from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_date = date.today()
        self.backwards_days = 14
        self.url = "https://128archive.com"
        self.court_id = self.__module__
        self.court_identifier = "AC"

    def set_parameters(self):
        """Build the urls to query

        :return:
        """
        start_date = self.case_date - timedelta(days=self.backwards_days)
        first_date = start_date.strftime("%m/%d/%Y")
        end_date = self.case_date.strftime("%m/%d/%Y")
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
            ("CurrentPageNo", "1"),
            ("Pages", "1"),
            ("PageSize", "100"),
        )
        return urlencode(self.parameters)

    def _download(self, request_dict={}) -> html.HtmlElement:
        """Download the HTML

        :param request_dict:
        :return: The HTML
        """
        self.url = f"{self.url}/?{self.set_parameters()}"
        html = super()._download(request_dict)
        return html

    def _process_html(self) -> None:
        """Process the data

        :return:
        """
        for row in self.html.xpath("//div[@data-rowtype='True']"):
            docket, name, date = row.xpath(
                ".//div[@class='col-md-7 font-bold']/text()"
            )
            url = row.xpath(".//div/div/a/@href")[0]

            self.cases.append(
                {
                    "date": date.strip(),
                    "docket": docket.strip(),
                    "name": name.strip(),
                    "url": url,
                    "status": "Unpublished",
                }
            )
