"""Scraper for South Carolina Supreme Court
CourtID: sc
Court Short Name: S.C.
Author: TBM <-- Who art thou TBM? ONLY MLR gets to be initials!
History:
 - 04-18-2014: Created.
 - 09-18-2014: Updated by mlr.
 - 10-17-2014: Updated by mlr to fix InsanityError
 - 2017-10-04: Updated by mlr to deal with their anti-bot system. Crux of change
               is to ensure that we get a cookie in our session by visiting the
               homepage before we go and scrape. Dumb.
 - 2019-02-26: Restructured completely by arderyp
 - 2024-09-18: Update to OpinionSiteLinear, implement backscraper,
    support unpublished opinions, by @grossir
- 2025-09-03: Retrieve lower_court in extract_from_text by @luism

Contact information:
 - Help desk: (803) 734-1193, Travis
 - Security desk: 803-734-5906, Joe Hilke
 - Web Developer (who can help with firewall issues): 803-734-0373, Winkie Clark
"""

import re
from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # Full URL example:
    # https://www.sccourts.org/opinions-orders/opinions/published-opinions/supreme-court/?term=2024-09
    base_url = (
        "https://www.sccourts.org/opinions-orders/opinions/{}/{}/?term={}-{}"
    )
    opinion_status = "published-opinions"
    court = "supreme-court"
    days_interval = 27  # guarantees picking each month
    first_opinion_date = date(2000, 1, 1)
    docket_regex = r"Appellate Case No. (?P<docket>\d{4}-\d+)"
    lower_court_regex = re.compile(
        r"Appeals? [Ff]rom (the )?(?P<lower_court>.+?)\n"
        r"(?P<judge>.+?),?\s*(?:Circuit|PCR|Master-in-Equity|Family)[^\n]*\n",
        re.MULTILINE,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.make_backscrape_iterable(kwargs)
        self.url = self.make_url_from_date(date.today())
        if self.opinion_status == "published-opinions":
            self.status = "Published"
        else:
            self.status = "Unpublished"

    def _process_html(self):
        xpath = ".//p[contains(@class, '{}')]/text()"
        for row in self.html.xpath("//div[contains(@class,'case-result')]"):
            date_filed = row.xpath("preceding-sibling::div[h3]/h3/text()")[-1]
            docket = row.xpath(xpath.format("case-number"))[0]
            name = row.xpath(xpath.format("case-name"))[0]

            summary = row.xpath(".//div[@class='result-info']/p/text()")
            if summary:
                summary = summary[0]
            else:
                # Unpublished opinions don't have a summary
                summary = ""

            url = row.xpath(".//a/@href")[0]
            self.cases.append(
                {
                    "docket": docket,
                    "name": name,
                    "summary": summary,
                    "url": url,
                    "date": date_filed,
                }
            )

    def make_backscrape_iterable(
        self, kwargs: dict
    ) -> list[tuple[date, date]]:
        """Reuse base function to get a sequence of date objects for
        each month in the interval. Then, convert them to target URLs
        and replace the self.back_scrape_iterable
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )

    def _download_backwards(self, date_obj: date) -> None:
        """Downloads an older page, and parses it

        Opinions from terms older than 2012-06 are in HTML
        format, which needs updating the
        self.expected_content_types attribute.

        Only do it for the backscraper to prevent ingesting
        bad data in the present day

        :param date_obj: date object to build the URL
        :return None
        """
        if date_obj.year <= 2012:
            self.expected_content_types.append("text/html")

        self.url = self.make_url_from_date(date_obj)
        logger.info("Backscraping URL: %s", self.url)
        self.html = self._download()
        self._process_html()

    def make_url_from_date(self, date_obj: date) -> str:
        """Builds the target URL from a date object and
        class attributes

        :param date_obj: a date
        :return: the formatted URL
        """
        return self.base_url.format(
            self.opinion_status,
            self.court,
            date_obj.year,
            str(date_obj.month).zfill(2),
        )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract docket number from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        results: dict[str, dict] = {}
        if match := self.lower_court_regex.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            results.setdefault("Docket", {})["appeal_from_str"] = lower_court
            judge = match.group("judge").strip()
            if judge:
                results["OriginatingCourtInformation"] = {
                    "assigned_to_str": judge
                }

        if match := re.search(self.docket_regex, scraped_text):
            results.setdefault("Docket", {})["docket_number"] = match.group(
                "docket"
            )
        return results
