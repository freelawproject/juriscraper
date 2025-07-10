"""
Author: Michael Lissner
Date created: 2013-04-05
Revised by Taliah Mirmalek on 2014-02-07
Scraper for the Supreme Court of Arizona
CourtID: ariz
Court Short Name: Ariz.
"""

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.azcourts.gov/opinions/SearchOpinionsMemoDecs.aspx?court=999"
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        self.cases = []

        # Extract download URLs
        download_urls_path = '//a[contains(@id , "hypCaseNum")]/@href'
        download_urls = [
            href.replace(
                "http://www.azcourts.gov", "https://opinions.azcourts.gov"
            )
            for href in self.html.xpath(download_urls_path)
        ]

        # Extract case names
        case_names_path = '//span[contains(@id , "lblTitle")]//text()'
        case_names = [
            titlecase(t.upper()) for t in self.html.xpath(case_names_path)
        ]

        # Extract case dates
        case_dates_path = '//span[contains(@id , "FilingDate")]//text()'
        case_dates = list(self.html.xpath(case_dates_path))

        # Extract precedential statuses
        precedential_statuses = []
        precedential_statuses_path = '//*[contains(@id, "DecType")]/text()'
        for s in self.html.xpath(precedential_statuses_path):
            if "OPINION" in s:
                precedential_statuses.append("Published")
            elif "MEMORANDUM" in s:
                precedential_statuses.append("Unpublished")
            else:
                precedential_statuses.append("Unknown")

        # Extract docket numbers
        docket_numbers_path = '//a[contains(@id , "hypCaseNum")]//text()'
        docket_numbers = list(self.html.xpath(docket_numbers_path))

        # Build cases list
        for i in range(len(download_urls)):
            case = {
                "name": case_names[i],
                "date": case_dates[i],
                "status": precedential_statuses[i],
                "docket": docket_numbers[i],
                "url": download_urls[i],
            }
            self.cases.append(case)
