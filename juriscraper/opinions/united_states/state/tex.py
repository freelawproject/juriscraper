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
from datetime import date
from datetime import datetime as dt

from lxml import etree

from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.type_utils import OpinionType
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.txcourts.gov/supreme/orders-opinions/{}/"
    link_xp = '//*[@id="MainContent"]/div/div/div/ul/li/a/@href'
    date_xp = '//*[@id="MainContent"]/div/div[1]/div/text()'
    judge_xp = r"(?:Chief\s)?Justice\s([A-Z][a-zA-Z]+)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.first_opinion_date = date(2014, 10, 3)
        self.current_year = date.today().year
        self.url = self.base_url.format(self.current_year)
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)
        self.is_backscrape = False

    def _download(self, request_dict=None):
        """
        Downloads the HTML content for the current opinion page.

        If not in backscrape mode and not in test mode, it first downloads the main page,
        updates the URL to the latest opinion link, and then downloads that page.
        Otherwise, it simply downloads the page at the current URL.

        Args:
            request_dict (dict, optional): Additional request parameters.

        Returns:
            The downloaded HTML content.
        """
        if request_dict is None:
            request_dict = {}

        if not self.is_backscrape and not self.test_mode_enabled():
            self.html = super()._download(request_dict)
            self.url = self.html.xpath(self.link_xp)[-1]
        self.html = super()._download(request_dict)

        return self.html

    def _process_html(self) -> None:
        """
        Parses the HTML content of the current opinion page and extracts case details.

        This method locates all PDF links representing opinions, then for each link:
          - Finds the associated docket number and case title from preceding table rows.
          - Extracts the disposition from the parent element.
          - Attempts to identify the authoring judge using a regex.
          - Determines if the opinion is per curiam.
          - Appends a dictionary with all extracted information to self.cases.

        Returns:
            None
        """
        date = self.html.xpath(self.date_xp)[0].strip()
        links = self.html.xpath('//a[contains(@href, ".pdf")]')
        for link in links:
            if link.getprevious() is not None:
                precedingTRs = link.xpath(
                    'ancestor::tr/preceding-sibling::tr[td[@class="a50cl"]]'
                ) or link.xpath(
                    'ancestor::tr/preceding-sibling::tr[td[@class="a54cl"]]'
                )
                docket, title, *_ = [
                    x for x in precedingTRs[-1].xpath(".//text()") if x.strip()
                ]
                disposition = link.getparent().xpath(".//text()")[0]
                judge_str = "".join(
                    [
                        x
                        for x in [
                            link.getprevious().tail,
                            link.text,
                            link.tail,
                        ]
                        if x
                    ]
                )
                judges = re.findall(self.judge_xp, judge_str)
                if judges:
                    author = judges[0]
                    per_curiam = False
                else:
                    author = ""
                    per_curiam = True

                self.cases.append(
                    {
                        "name": titlecase(title.split(";")[0]),
                        "disposition": disposition,
                        "url": link.get("href"),
                        "docket": docket,
                        "date": date,
                        "type": self.extract_type(link),
                        "per_curiam": per_curiam,
                        "judge": ", ".join(judges),
                        "author": author,
                    }
                )

    @staticmethod
    def extract_type(link: etree.Element) -> str:
        """
        Determines the opinion type based on the PDF file name in the link.

        Args:
            link (etree.Element): The anchor element containing the PDF link.

        Returns:
            tuple[OpinionType, bool]: The opinion type, as defined in OpinionType.
        """
        url = link.get("href")
        if url.endswith("pc.pdf"):
            op_type = OpinionType.UNANIMOUS
        elif url.endswith("cd.pdf"):
            op_type = OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
        elif url.endswith("d.pdf"):
            op_type = OpinionType.DISSENT
        elif url.endswith("c.pdf"):
            op_type = OpinionType.CONCURRENCE
        else:
            op_type = OpinionType.MAJORITY
        return str(op_type.value)

    def make_backscrape_iterable(self, kwargs) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        Texas opinions page returns all opinions for a year (pagination is not needed),
        so we must filter out opinions not in the date range we are looking for

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = (
            dt.strptime(start, "%Y/%m/%d").date()
            if start
            else self.first_opinion_date
        )
        end = dt.strptime(end, "%Y/%m/%d").date() if end else date.today()

        dates = []
        for year in list(range(start.year, end.year + 1)):
            dates.append((year, start, end))
        self.back_scrape_iterable = dates

    def _download_backwards(self, analysis_window: tuple) -> None:
        """
        Downloads and processes opinions for a given year within a specified date range.

        Args:
            analysis_window (tuple): A tuple containing the year (int), start date (date), and end date (date).

        This method sets the scraper to backscrape mode, constructs the URL for the specified year,
        and iterates through all opinion links on the page. For each link, it parses the date from the URL,
        filters out links not within the specified date range, and processes the HTML for valid links.
        """
        self.is_backscrape = True
        year, start, end = analysis_window
        self.url = self.base_url.format(year)
        self._download()

        for path in self.html.xpath(self.link_xp):
            if "historical" in path:
                # in 2014 they have an extra link for pre-2014 ops
                continue
            date_str = path.strip("/").split("/")[-1]
            date_obj = dt.strptime(date_str, "%B-%d-%Y").date()

            if not (start <= date_obj <= end):
                continue

            self.url = path
            self._download()
            self._process_html()
