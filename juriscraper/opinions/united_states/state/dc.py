"""Scraper for the D.C. Court of Appeals
CourtID: dc
Court Short Name: D.C.
Author: V. David Zvenyach
Date created:2014-02-21
"""

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.dccourts.gov/court-of-appeals/opinions-memorandum-of-judgments"
        qualifier_no_opinions = (
            'not(contains(td[2]/span/text(), "NO OPINIONS"))'
        )
        qualifier_has_pdf_link = 'contains(.//td[1]/a/@href, ".pdf")'
        self.base_path = "//table//tr[{} and {}]".format(
            qualifier_no_opinions,
            qualifier_has_pdf_link,
        )

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
