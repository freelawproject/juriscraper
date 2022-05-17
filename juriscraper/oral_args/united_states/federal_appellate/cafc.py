"""Scraper for Federal Circuit of Appeals
CourtID: cafc
Court Short Name: cafc
Author: Andrei Chelaru
Reviewer: mlr
History:
 - created by Andrei Chelaru, 18 July 2014
 - Updated/rewritten by mlr, 2016-04-14
 - Updated by William E. Palin, 2022-05-17
"""
from datetime import date, timedelta

from dateutil.rrule import MONTHLY, rrule

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://cafc.uscourts.gov/wp-admin/admin-ajax.php?action=get_wdtable&table_id=8"
        self.method = "POST"
        self._set_parameters()
        self.today = date.today().strftime("%m/%d/%Y")
        self.earlier = (date.today() - timedelta(days=30)).strftime("%m/%d/%Y")
        self.parameters[
            "columns[0][search][value]"
        ] = f"{self.earlier}|{self.today}"
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=date(2021, 10, 8),
                until=date(2022, 5, 17),
            )
        ]

    def _set_parameters(self) -> None:
        """Set the parameters for the request.

        :return:None
        """
        self.parameters = {
            "draw": "4",
            "columns[0][data]": "0",
            "columns[0][name]": "Arg_Date",
            "columns[0][searchable]": "true",
            "columns[0][orderable]": "true",
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
            "length": "1000",
            "search[value]": "",
            "search[regex]": "false",
            "wdtNonce": "6a2284f635",
            "sRangeSeparator": "|",
        }

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
        self.end = (d + timedelta(days=31)).strftime("%m/%d/%Y")
        self.parameters[
            "columns[0][search][value]"
        ] = f'{d.strftime("%m/%d/%Y")}|{self.end}'
        self.html = self._download()
        self._process_html()
