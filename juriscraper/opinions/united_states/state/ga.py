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
        self.last_month = today - timedelta(days=31)
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
            title = link.text_content()
            if not title:
                continue
            dockets = re.findall(r"S?\d{2}\w\d{4}", title)
            if not dockets:
                # Skip empty links in the HTML
                continue
            docket = ", ".join(dockets)
            name = title.split(dockets[-1])[-1].strip("., ")
            summary = link.xpath(
                ".//parent::li/parent::ul/preceding-sibling::p[1]"
            )[0].text_content()
            # We've got en/em dash and hyphens.
            date_str = (
                summary.split("–")[0].split("—")[0].split("-")[0].strip()
            )
            date_summary = datetime.strptime(date_str, "%B %d, %Y")
            if self.test_mode_enabled():
                self.last_month = date(year=2019, month=11, day=1)

            if date_summary.date() < self.last_month:
                # GA lists all opinions from the previous year on the same page
                # but we don't need to scrape them every time.  So cancel out
                # after 31 days.
                # This should resolve the speed warning we receive on GA.
                break
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
