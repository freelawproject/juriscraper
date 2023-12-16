"""
Scraper for the United States Bankruptcy Appellate Panel for the First Circuit
CourtID: bap1
Court Short Name: 1st Cir. BAP
"""
from typing import Dict
from datetime import datetime, timedelta

from lxml.html import HtmlElement

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # See issue #828 on Github for extraction reference
    lower_court_to_abbreviation = {
        "USBC - District of New Hampshire": "NH",
        "USBC - District of Massachusetts (Worcester)": "MW",
        "USBC - District of Puerto Rico": "PR",
        "USBC - District of Massachusetts (Boston)": "MB",
        "USBC - District of Maine (Portland)": "EP",
        "USBC - District of Rhode Island": "RI",
        "Bankrupcty Court of ME - Bangor": "EB",
        "Bankruptcy Court of MA - Boston": "MB",
        "Bankruptcy Court of MA - Springfield": "MS",
        "Bankruptcy Court of ME - Portland": "EP",
        "Bankruptcy Court - Rhode Island": "RI",
        "Bankruptcy Court - San Juan Puerto Rico": "PR",
        "Bankruptcy Court of MA - Worcester": "MW",
        "Bankruptcy Court - Ponce Puerto Rico": "PR",
        "Bankruptcy Court of NH, Concord": "NH",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = self.url = "https://www.bap1.uscourts.gov/bapopn"
        self.court_id = self.__module__

        self.set_date_filter_parameters()

        # There are 29 pages as of development in Dec 2023 (source indexes from 0)
        self.back_scrape_iterable = range(29)

    def _download(self, request_dict: Dict = {}) -> HtmlElement:
        return super()._download(self.parameters)

    def _process_html(self) -> None:
        for row in self.html.xpath("//tr[td]"):
            opinion_name = row.xpath("td[1]")[0].text_content().strip()
            status = self.get_status_from_opinion_name(opinion_name)

            lower_court = row.xpath("td[4]/span")[0].text_content().strip()
            docket_number = row.xpath("td[2]")[0].text_content().strip()

            case = {
                "status": status,
                "url": row.xpath("td[1]/a/@href")[0],  # opinion url
                "docket": self.build_full_docket_number(
                    docket_number, lower_court
                ),
                # Pub Date
                "date": row.xpath("td[3]")[0].text_content().strip(),
                # short title
                "name": row.xpath("td[4]")[0].text.strip(),
                # district
                "lower_court": lower_court,
            }

            self.cases.append(case)

    def set_date_filter_parameters(self):
        """
        Limit search to get fresh data and avoid overloading the court server
        Default: last month
        """
        date_filter_end = datetime.today()
        date_filter_start = date_filter_end - timedelta(30)
        self.parameters = {
            "params": {
                "opn": "",
                "field_opn_short_title_value": "",
                "field_opn_issdate_value[min][date]": date_filter_start.strftime(
                    "%m/%d/%Y"
                ),
                "field_opn_issdate_value[max][date]": date_filter_end.strftime(
                    "%m/%d/%Y"
                ),
            }
        }

    def _download_backwards(self, page_number: int) -> None:
        self.parameters = {}  # delete date filters used in normal scraper
        self.url = (
            f"{self.base_url}?page={page_number}"
            if page_number > 0
            else self.base_url
        )
        self.html = self._download()
        self._process_html()

    def build_full_docket_number(
        self, docket_number: str, lower_court: str
    ) -> str:
        """
        Full docket number has the lower court abbreviation in it
        For each unique lower court in the opinions available on the source,
        the linked opinion PDF was opened and the abbrevation extracted
        """
        lower_court_abbreviation = self.lower_court_to_abbreviation.get(
            lower_court, ""
        )

        return f"BAP No. {lower_court_abbreviation} {docket_number}"

    @staticmethod
    def get_status_from_opinion_name(opinion_name: str) -> str:
        if opinion_name.endswith("U"):
            status = "Unpublished"
        elif opinion_name.endswith("P"):
            status = "Published"
        else:
            status = "Unknown"

        return status
