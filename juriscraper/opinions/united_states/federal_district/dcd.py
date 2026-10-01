"""Scraper for United States District Court for the District of Columbia
CourtID: dcd
Court Short Name: D.D.C.
Author: V. David Zvenyach
Date created: 2014-02-27
Substantially Revised: Brian W. Carver, 2014-03-28
2024-05-03, grossir: Change base class OpinionSiteLinear
"""

import re
from datetime import date, datetime

from lxml import html

from juriscraper.Backscraper import DateBackscraper
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear, DateBackscraper):
    # Oldest opinion listed in https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl
    first_opinion_date = date(2005, 1, 3)
    date_format = "%m/%d/%Y"
    docket_document_number_regex = re.compile(r"(\?)(\d+)([a-z]+)(\d+)(-)(.*)")
    nature_of_suit_regex = re.compile(r"(\?)(\d+)([a-z]+)(\d+)(-)(.*)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?{date.today().year}"
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        """
        Some rows have mutliple documents and hence urls for each case.
        We will "pad" every other metadata field to match the urls
        """
        for row in self.html.xpath("//table[2]//tr[not(th)]"):
            case_name = titlecase(
                row.xpath("td[2]//text()[preceding-sibling::br]")[0].lower()
            )
            date_string = row.xpath("td[1]/text()")[0]
            date_filed = datetime.strptime(date_string, "%m/%d/%Y")
            docket = row.xpath("td[2]//text()[following-sibling::br]")[0]

            judge_element = row.xpath("td[3]")[0]
            judge_string = html.tostring(
                judge_element, method="text", encoding="unicode"
            )
            judge = re.search(r"(by\s)(.*)", judge_string, re.MULTILINE).group(
                2
            )

            for url in row.xpath("td[3]/a/@href"):
                doc_number = self.get_docket_document_number_from_url(url)
                self.cases.append(
                    {
                        "name": case_name,
                        "date": str(date_filed),
                        "url": url,
                        "docket": docket,
                        "docket_document_number": doc_number,
                        "judge": judge,
                    }
                )

    def get_docket_document_number_from_url(self, url: str) -> tuple[str, str]:
        """Get docket document number from the opinion URL

        :param url:
        :return:  docket document number
        """
        # In 2012 (and perhaps elsewhere) they have a few weird urls.
        match = self.docket_document_number_regex.search(url)
        doc_number = match.group(6) if match else url

        return doc_number

    async def _download_backwards(self, year: int) -> None:
        """Build URL with year input and scrape

        :param year: year to scrape
        :return None
        """
        self.url = f"https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?{year}"
        self.html = await self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Build the years to backscrape, both ends inclusive

        :param kwargs: passed when initializing the scraper; may contain
            backscrape_start and backscrape_end as "%m/%d/%Y" strings.
            Default: from `first_opinion_date` to today
        :return None
        """
        start, end = self.get_backscrape_date_range(kwargs)
        self.back_scrape_iterable = range(
            max(self.first_opinion_date.year, start.year), end.year + 1
        )
