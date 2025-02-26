"""Scraper for Federal Circuit of Appeals
CourtID: cafc
Court Short Name: cafc
Author: Andrei Chelaru
Reviewer: mlr
History:
 - created by Andrei Chelaru, 18 July 2014
 - Updated/rewritten by mlr, 2016-04-14
 - Updated by William E. Palin, 2022-05-17
 - Updated by William E. Palin, 2023-01-26
"""

from datetime import date, timedelta

from juriscraper.AbstractSite import logger
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    days_interval = 15
    first_opinion_date = date(2003, 2, 4)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.expected_content_types = ["audio/mpeg3"]
        self.url = "https://www.cafc.uscourts.gov/home/oral-argument/listen-to-oral-arguments/"
        self.data_url = "https://www.cafc.uscourts.gov/wp-admin/admin-ajax.php?action=get_wdtable&table_id=8"
        self.request["verify"] = False
        self.start_date = None
        self.end_date = None
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Extract content from JSON response

        Each row in the json returns a list of values, see example below.
        [
          "05/06/2022",
          "21-2084",
          "<a sort=\"Best Medical International, Inc. v. Elekta Inc.\"
          href=\"https://oralarguments.cafc.uscourts.gov/default.aspx?fl=21-2084_05062022.mp3\"
          download>Best Medical International, Inc. v. Elekta Inc. (mp3)</a>"
        ]

        :return: None
        """
        if not self.test_mode_enabled():
            # Get the data JSON
            self.method = "POST"
            self._set_parameters()
            self._request_url_post(self.data_url)

        for row in self.request["response"].json()["data"]:
            _, name, _, url, _ = row[2].split('"')
            self.cases.append(
                {"date": row[0], "docket": row[1], "name": name, "url": url}
            )

    def _download_backwards(self, d: date) -> None:
        """Download a months' worth of oral arguments.

        :param d: Date to download arguments starting from
        :return: None
        """
        self.start_date, self.end_date = d
        logger.info("Backscraping for range %s %s", *d)
        self.html = self._download()
        self._process_html()

    def _set_parameters(self) -> None:
        """Set the parameters for the request.

        :return:None
        """
        wdt_nonce = self.html.xpath(
            ".//input[@id='wdtNonceFrontendServerSide_8']/@value"
        )

        self.parameters = {
            "draw": "1",
            "columns[0][data]": "0",
            "columns[0][name]": "Arg_Date",
            "columns[0][searchable]": "true",
            "columns[0][orderable]": "true",
            "columns[0][search][value]": self.get_date_filter(),
            "columns[0][search][regex]": "false",
            "columns[1][data]": "1",
            "columns[1][name]": "Appeal_Number",
            "columns[1][searchable]": "true",
            "columns[1][orderable]": "true",
            "columns[1][search][value]": "",
            "columns[1][search][regex]": "false",
            "columns[2][data]": "2",
            "columns[2][name]": "Arg_Link",
            "columns[2][searchable]": "true",
            "columns[2][orderable]": "true",
            "columns[2][search][value]": "",
            "columns[2][search][regex]": "false",
            "order[0][column]": "0",
            "order[0][dir]": "desc",
            "start": "0",
            "length": "100",
            "search[value]": "",
            "search[regex]": "false",
            "wdtNonce": wdt_nonce,
        }

    def get_date_filter(self) -> str:
        """Format date filter using backscraping attributes; or defaults"""
        if not self.start_date:
            self.end_date = date.today()
            self.start_date = self.end_date - timedelta(days=30)

        return f'{self.start_date.strftime("%m/%d/%Y")}|{self.end_date.strftime("%m/%d/%Y")}'
