# Scraper for Texas Supreme Court
# CourtID: tex
# Court Short Name: TX
# Court Contacts:
#  - http://www.txcourts.gov/contact-us/
#  - Blake Hawthorne <Blake.Hawthorne@txcourts.gov>
#  - Eddie Murillo <Eddie.Murillo@txcourts.gov>
#  - Judicial Info <JudInfo@txcourts.gov>
# Author: Andrei Chelaru
# Reviewer: mlr
# History:
#  - 2014-07-10: Created by Andrei Chelaru
#  - 2014-11-07: Updated by mlr to account for new website.
#  - 2014-12-09: Updated by mlr to make the date range wider and more thorough.
#  - 2015-08-19: Updated by Andrei Chelaru to add backwards scraping support.
#  - 2015-08-27: Updated by Andrei Chelaru to add explicit waits
#  - 2021-12-28: Updated by flooie to remove selenium.
#  - 2024-02-21; Updated by grossir: handle dynamic backscrapes
#  - 2025-05-30; Updated by lmanzur: get opinions from the orders on causes page

import re
from datetime import date, datetime

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.first_opinion_date = datetime(2025, 1, 1)
        self.year = date.today().year
        self.url = (
            f"https://www.txcourts.gov/supreme/orders-opinions/{self.year}/"
        )
        self.make_backscrape_iterable(kwargs)
        self.status = "Published"
        self.needs_special_headers = True
        self.opinion_page = False
        self.publication_date = ""

    def _process_html(self) -> None:
        """Process HTML
        :return: None
        """
        if not self.opinion_page:
            last_publication_url = self.html.xpath(
                '//div[@class="panel-content"]//a'
            )[-2].get("href", None)
            if not last_publication_url:
                logger.info("No publication date found in the HTML.")
                return
            # If we are not on the opinion page, we need to go there
            match = re.search(
                r"/(\d{4})/([a-z]+)/([a-z]+-\d{2}-\d{4})/",
                last_publication_url,
            )
            self.publication_date = match.group(3)
            self.opinion_page = True
            self.url = last_publication_url
            self.html = self._download()

        order_causes_title_tr = self.html.xpath(
            '//div[@class="a38" and normalize-space(text())="ORDERS ON CAUSES"]/ancestor::tr[1]'
        )
        if not order_causes_title_tr:
            logger.info("No orders on causes found in the HTML.")
            return
        current_opinion = {
            "name": "",
            "docket": "",
            "lower_court": "",
            "date": self.publication_date,
            "url": "",
            "type": "",
            "author": "",
            "per_curiam": False,
            "judge": "",
        }
        for tr in order_causes_title_tr[0].itersiblings(tag="tr"):
            current_opinion["per_curiam"] = False
            current_opinion["judge"] = ""
            # get the docket number
            if tr.xpath('.//td[contains(@class, "a50cl")]'):
                current_opinion["docket"] = tr.xpath(
                    './/div[contains(@class, "a50")]/text()'
                )[0].strip()

                # get lower court and case name
                if tr.xpath('.//td[contains(@class, "a54cl")]'):
                    title = tr.xpath('.//div[contains(@class, "a54")]/text()')[
                        0
                    ]
                    # Try to extract the name and lower court docket from the title
                    match = re.match(r"^(.*?)\s*\(([\dA-Za-z\-]+),", title)
                    if match:
                        current_opinion["name"] = titlecase(
                            match.group(1).strip().split("; from")[0]
                        )
                        current_opinion["lower_court"] = match.group(2).strip()
                    else:
                        # Fallback to previous patterns if needed
                        found = False
                        for pattern in [
                            r"^(.*?)\s*\(([^,]+),.*,\s*([^)]+)\)$",
                            r"^(.*?)\s*\(([^)]+)\)$",
                        ]:
                            match = re.match(pattern, title)
                            if match:
                                current_opinion["name"] = titlecase(
                                    match.group(1).strip().split("; from")[0]
                                )
                                current_opinion["lower_court"] = match.group(
                                    2
                                ).strip()
                                found = True
                                break
                        if not found:
                            # Handle cases where there is no lower court, e.g. "v. ...; from El Paso County"
                            name_match = re.match(
                                r"^(.*?)(?:; from .*)?$", title
                            )
                            if name_match:
                                current_opinion["name"] = titlecase(
                                    name_match.group(1).strip()
                                )
                                current_opinion["lower_court"] = ""
                continue
            # get the opinion type and download URL
            if tr.xpath('.//td[contains(@class, "a72c")]'):
                download_urls = tr.xpath(
                    './/td[contains(@class, "a72c")]//span[@class="a70"]//a'
                )
                for download_url in download_urls:
                    current_opinion["url"] = download_url.get("href")
                    current_opinion["type"] = (
                        "040dissent"
                        if "d" in download_url.get("title", "").lower()
                        else "015unamimous"
                        if "pc" in download_url.get("title", "").lower()
                        else "030concurrence"
                        if "c" in download_url.get("title", "").lower()
                        else "020lead"
                    )

                    extra_info = tr.xpath(
                        './/td[contains(@class, "a72c")]//span[@class="a70"]//text()'
                    )

                    if current_opinion["type"] == "015unamimous":
                        current_opinion["per_curiam"] = True

                    if current_opinion["type"] in [
                        "030concurrence",
                        "040dissent",
                    ]:
                        for info in extra_info:
                            if "filed" in info:
                                current_opinion["author"] = info.split(
                                    "filed"
                                )[0].strip()
                    elif current_opinion["type"] in [
                        "020lead",
                        "015unamimous",
                    ]:
                        for info in extra_info:
                            if "delivered" in info:
                                current_opinion["author"] = info.split(
                                    "delivered"
                                )[0].strip()

                    for info in extra_info:
                        if "joined" in info:
                            current_opinion["judge"] = current_opinion[
                                "judge"
                            ] = (
                                info.replace("in which", "")
                                .replace("joined.", "")
                                .replace("joined", "")
                                .replace("and", ",")
                                .replace(".", "")
                                .replace(" , ", ",")
                                .strip()
                            )

                    self.cases.append(current_opinion.copy())

    def make_backscrape_iterable(self, kwargs):
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        Louisiana's opinions page returns all opinions for a year (pagination is not needed),
        so we must filter out opinions not in the date range we are looking for

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.now().date()

        self.back_scrape_iterable = [(start, end)]

    def update_parameters(self):
        """Update the date range parameter"""

        self.year = self.start_date.year
        self.month = self.start_date.strftime("%B").lower()
        self.complete_date = self.start_date.strftime("%b-%d-%Y").lower()

    def _download_backwards(self, dates):
        """Called when backscraping

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.start_date, self.end_date = dates
        self.is_backscrape = True
        logger.info(
            "Backscraping for range %s %s", self.start_date, self.end_date
        )
        self.update_parameters()

        self.url = f"https://www.txcourts.gov/supreme/orders-opinions/{self.year}/{self.month}/{self.complete_date}/"
        self.html = self._download()
        self._process_html()
