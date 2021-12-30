#  Scraper for Georgia Supreme Court
# CourtID: ga
# Court Short Name: ga

import re
from datetime import date, datetime, timedelta

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = self._get_url(today.year)
        self.status = "Published"
        self.back_scrape_iterable = range(2016, 2022)

    def _get_url(self, year: int) -> str:
        """Generate the GA URL for a given year.

        :param year: Year to scrape
        :return: URL for the given year
        """
        return f"https://www.gasupreme.us/opinions/{year}-opinions/"

    def _process_html(self) -> None:
        for link in self.html.xpath("//li/a[contains(@href, '.pdf')]"):
            url = link.get("href")
            # Expected title content:
            # - "S20A1505, S20A1506. PENDER v. THE STATE"
            # - "S21A0306. BELL v. RAFFENSPERGER"
            title = link.text_content()
            if not title:
                continue
            dockets = re.findall(r"S?\d{2}\w\d{4}", title)
            if not dockets:
                # Skip links to weekly summaries or cases without a docket
                continue
            docket = ", ".join(dockets)
            name = title.split(dockets[-1])[-1].strip("., ")
            # Expected summary content:
            # - "October 19, 2021—SUMMARIES for NOTEWORTHY OPINIONS"
            # - "July 7, 2021"
            # - "February 15, 2021 – SUMMARIES for NOTEWORTHY OPINIONS"
            summary = link.xpath(
                ".//parent::li/parent::ul/preceding-sibling::p[1]"
            )[0].text_content()
            # Character separator for dates from summary text could be:
            # - dash: "-"
            # - hyphen: "—"
            # - character U+2013: "–"
            date_str = (
                summary.split("–")[0].split("—")[0].split("-")[0].strip()
            )
            date_summary = datetime.strptime(date_str, "%B %d, %Y")
            self.cases.append(
                {
                    "date": date_str,
                    "docket": docket,
                    "name": titlecase(name),
                    "url": url,
                }
            )

    def _download_backwards(self, year) -> None:
        self.url = self._get_url(year)
        logger.info(f"Backscraping for year {year}: {self.url}")
        self.html = self._download()

        # Setting status is important because it prevents the download
        # function from being run a second time by the parse method.
        if self.html is not None:
            self.status = 200
            self._process_html()
