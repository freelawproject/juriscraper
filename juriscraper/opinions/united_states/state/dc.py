"""Scraper for the D.C. Court of Appeals
CourtID: dc
Court Short Name: D.C.
Author: V. David Zvenyach
Date created:2014-02-21
"""

from datetime import datetime

import requests
from lxml import html

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # self.url = "https://www.dccourts.gov/court-of-appeals/opinions-memorandum-of-judgments?page={}"
        self.url = "https://www.dccourts.gov/court-of-appeals/opinions-memorandum-of-judgments?page={}"
        self.page = 0
        qualifier_no_opinions = (
            'not(contains(td[2]/span/text(), "NO OPINIONS"))'
        )
        qualifier_has_pdf_link = 'contains(.//td[1]/a/@href, ".pdf")'
        self.base_path = "//table//tr[{} and {}]".format(
            qualifier_no_opinions,
            qualifier_has_pdf_link,
        )

    def fetch_html(self, page_number):
        """Fetch the HTML content of a given page."""
        url = self.url.format(page_number)
        response = requests.get(url)
        if response.status_code == 200:
            return html.fromstring(response.content)
        else:
            raise Exception(
                f"Failed to load page {page_number}. HTTP Status: {response.status_code}")

    def parse_page(self, page_number):
        """Parse the content of a specific page and return case details."""
        self.html = self.fetch_html(page_number)
        docket_numbers = self._get_docket_numbers()
        download_urls = self._get_download_urls()
        case_names = self._get_case_names()
        case_dates = self._get_case_dates()
        statuses = self._get_precedential_statuses()

        cases = []
        for i, case_date in enumerate(case_dates):
            case = {
                'docket_number': docket_numbers[i],
                'download_url': download_urls[i],
                'case_name': case_names[i],
                'case_date': case_date,
                'precedential_status': statuses[i],
            }
            cases.append(case)
        return cases
    def _get_docket_numbers(self):
        path = f"{self.base_path}/td[1]/a"
        return [cell.text_content().strip() for cell in self.html.xpath(path)]

    def _get_download_urls(self):
        path = f"{self.base_path}/td[1]/a/@href"
        return [href for href in self.html.xpath(path)]

    def _get_case_names(self):
        path = f"{self.base_path}/td[2]"
        return [cell.text_content() for cell in self.html.xpath(path)]

    def _get_case_dates(self):
        path = f"{self.base_path}/td[3]"
        return [
            convert_date_string(cell.text_content())
            for cell in self.html.xpath(path)
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:

        self.parse()
        filtered_opinions = []
        start_date = start_date.date()
        end_date = end_date.date()

        while True:
            cases = self.parse_page(self.page)
            if not cases:
                break

            for case in cases:
                if start_date <= case['case_date'] <= end_date:
                    filtered_opinions.append(case)

            # Break if there are no more cases on this page
            if len(cases) < 20:  # Assuming each page has 20 cases
                break

            self.page += 1

        return len(filtered_opinions)

        # start_date = start_date.date()
        # end_date = end_date.date()
        # case_dates = self._get_case_dates()
        # filtered_opinions = []
        #
        # # filet cases based in date range
        # for i, case_date in enumerate(case_dates):
        #     if start_date <= case_date <= end_date:
        #         opinion ={
        #             'docket_number':self._get_docket_numbers()[i],
        #             'download_url': self._get_download_urls()[i],
        #             'case_name': self._get_case_names()[i],
        #             'case_date': case_date,
        #             'precedential_status': self._get_precedential_statuses()[i],
        #         }
        #         filtered_opinions.append(opinion)
        # # for opinion in filtered_opinions:
        # #     print(opinion)
        # return len(filtered_opinions)

    def get_class_name(self):
        return "dc"

    def get_court_name(self):
        return "D.C. Court of Appeals"

    def get_state_name(self):
        return "District Of Columbia"

    def get_court_type(self):
        return "state"
