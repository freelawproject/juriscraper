"""Scraper for Louisiana Court of Appeal, Third Circuit
CourtID: lactapp_3
Court Short Name: La. Ct. App. 3rd Cir.
Author: Luis-manzur
History:
  2025-10-06: Created by Luis-manzur
"""

from datetime import date, datetime
from urllib.parse import urljoin

from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2003, 9, 3)
    days_interval = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.la3circuit.org"
        self.url = urljoin(self.base_url, "index.aspx")
        current_year = str(datetime.today().year)
        current_month = datetime.today().strftime("%B")
        self.status = "Published"
        self.method = "POST"
        self.parameters = {
            "__EVENTTARGET": "ctl00$MainContent$btnSearchOpinionsByMonthYear",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": "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",
            "__VIEWSTATEGENERATOR": "90059987",
            "__EVENTVALIDATION": "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",
            "ctl00$MainContent$ddlSearchOpinions1_Year": current_year,
            "ctl00$MainContent$ddlSearchOpinions2_Year": current_year,
            "ctl00$MainContent$ddlSearchOpinions2_Month": current_month,
        }
        self.use_proxy = True
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Process the HTML to extract case details.

        :return None
        """

        rows = self.html.xpath(
            "(//table[contains(@class, 'table table-striped table-responsive')])[6]//tr"
        )

        for row in rows:
            hrefs = row.xpath(
                ".//a[contains(text(), 'Download Opinion')]/@href"
            )
            if not hrefs:
                continue
            download_url = urljoin(self.base_url, hrefs[0])
            docket = row.xpath(".//strong[1]/text()")[0]
            date_raw = row.xpath(
                ".//strong[contains(text(), 'Opinion Date:')]/following-sibling::text()[1]"
            )[0].strip()
            date = f"{date_raw[:2]}/{date_raw[2:4]}/{date_raw[4:]}"
            name = row.xpath(
                ".//strong[contains(text(), 'Case Title:')]/following-sibling::text()[1]"
            )[0].strip()
            lower_court = row.xpath(
                ".//strong[contains(text(), 'Lower Court:')]/following-sibling::text()[1]"
            )[0].strip()

            self.cases.append(
                {
                    "docket": docket,
                    "date": date,
                    "name": titlecase(name),
                    "lower_court": lower_court,
                    "url": download_url,
                }
            )

    def _download_backwards(self, search_date: date) -> None:
        """Download and process HTML for a given target date.

        :param search_date (date): The date for which to download and process opinions.
        :return None; sets the target date, downloads the corresponding HTML
        and processes the HTML to extract case details.
        """

        self.parameters.update(
            {
                "ctl00$MainContent$ddlSearchOpinions1_Year": str(
                    search_date.year
                ),
                "ctl00$MainContent$ddlSearchOpinions2_Year": str(
                    search_date.year
                ),
                "ctl00$MainContent$ddlSearchOpinions2_Month": search_date.strftime(
                    "%B"
                ),
            }
        )
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
