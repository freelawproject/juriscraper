#  Scraper for Georgia Supreme Court
# CourtID: ga
# Court Short Name: ga

import re
from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    url_template = "https://www.gasupreme.us/opinions/{}-opinions/"
    first_opinion_year = 2017

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.url_template.format(date.today().year)
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        for link in self.html.xpath("//li/a[contains(@href, '.pdf')]"):
            url = link.get("href")
            # Expected title content:
            # - "S20A1505, S20A1506. PENDER v. THE STATE"
            # - "S21A0306. BELL v. RAFFENSPERGER"
            title = link.text_content()

            if not title:
                logger.info("No link title for row %s", url)
                continue

            dockets = re.findall(r"S?\d{2}\w\d{4}", title)
            if not dockets:
                # Try this only when the <a> doesn't include the docket;
                # if done always, may pick up extra info like
                # "Reinstatement issued" or "Concurral issued"
                title = link.xpath("string(..)")
                dockets = re.findall(r"S?\d{2}\w\d{4}", title)

            if not dockets or "SUMMARY" in title:
                # Skip links to weekly summaries or cases without a docket
                logger.info("Skip summary row %s", title)
                continue

            docket = ", ".join(dockets)
            name = title.split(dockets[-1])[-1].strip("., ")
            # Expected summary content:
            # - "October 19, 2021—SUMMARIES for NOTEWORTHY OPINIONS"
            # - "July 7, 2021"
            # - "February 15, 2021 – SUMMARIES for NOTEWORTHY OPINIONS"
            summary = link.xpath(
                ".//parent::li/parent::ul/preceding-sibling::h3[1]/following-sibling::p"
            )[0].text_content()
            # Character separator for dates from summary text could be:
            # - dash: "-"
            # - hyphen: "—"
            # - character U+2013: "–"
            date_str = (
                summary.split("–")[0].split("—")[0].split("-")[0].strip()
            )
            self.cases.append(
                {
                    "date": date_str,
                    "docket": docket,
                    "name": titlecase(name),
                    "url": url,
                }
            )

    def _download_backwards(self, year: int) -> None:
        self.url = self.url_template.format(year)
        logger.info("Backscraping for year %s %s", year, self.url)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict):
        if kwargs.get("backscrape_start"):
            start = int(kwargs["backscrape_start"])
        else:
            start = self.first_opinion_year

        if kwargs.get("backscrape_end"):
            end = int(kwargs["backscrape_end"])
        else:
            end = date.today().year - 1

        if start == end:
            end = start + 1

        self.back_scrape_iterable = range(start, end)

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract the state citation from the document's text

        :param scraped_text: the extracted text
        :return: a dictionary, empty or with expected Citation key
        """
        if match := re.search(r"\d+ Ga. \d+", scraped_text[:50]):
            return {"Citation": match.group(0)}
        else:
            return {}
