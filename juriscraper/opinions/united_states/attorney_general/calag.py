"""Scraper for the California Attorney General
CourtID: calag
Court Short Name: California Attorney General
"""

import datetime

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.url_base = "https://oag.ca.gov/opinions/yearly-index?conclusion-year[value][year]="
        self.url = self.url_base + str(self.year)
        self.back_scrape_iterable = list(range(1985, self.year + 1))
        self.rows_path = '//tbody/tr[contains(./td[1]//a/@href, ".pdf")]'
        self.cell_path = f"{self.rows_path}/td[%d]"

    def _get_case_names(self):
        """No case names available"""
        return ["Untitled California Attorney General Opinion"] * len(
            self.html.xpath(self.rows_path)
        )

    def _get_download_urls(self):
        path = f"{self.cell_path % 1}//a/@href"
        return [href for href in self.html.xpath(path)]

    def _get_case_dates(self):
        dates = []
        for cell in self.html.xpath(self.cell_path % 4):
            date_raw = cell.text_content().replace(r"\n", "").strip()
            dates.append(convert_date_string(date_raw))
        return dates

    def _get_docket_numbers(self):
        return [
            cell.text_content().strip()
            for cell in self.html.xpath(self.cell_path % 1)
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_summaries(self):
        """Combine the Questions and Conclusions Columns"""
        summaries = []
        for row in self.html.xpath(self.rows_path):
            questions = row.xpath("./td[2]")[0].text_content()
            conclusions = row.xpath("./td[3]")[0].text_content()
            summaries.append(
                f"QUESTIONS: {questions} CONCLUSIONS: {conclusions}"
            )
        return summaries

    def _download_backwards(self, year):
        self.url = self.url_base + str(year)
        print(self.url)
        self.html = self._download()
