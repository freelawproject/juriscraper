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
    days_interval = 365

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
        """Downloads the HTML content for the current opinion page.

        :param request_dict (dict, optional): Additional request parameters.
        :return The downloaded HTML content.
        """
        if request_dict is None:
            request_dict = {}

        if not self.is_backscrape and not self.test_mode_enabled():
            self.html = super()._download(request_dict)
            self.url = self.html.xpath(self.link_xp)[-1]
        self.html = super()._download(request_dict)

        return self.html

    def _process_html(self) -> None:
        """Parses the HTML content

        :return None
        """
        date = self.html.xpath(self.date_xp)[0].strip()
        links = self.html.xpath('//a[contains(@href, ".pdf")]')
        for link in links:
            if link.getparent() is None or link.getparent().get(
                "class"
            ) not in ["a79", "a70"]:
                continue
            precedingTRs = link.xpath(
                'ancestor::tr/preceding-sibling::tr[td[@class="a50cl"]]'
            ) or link.xpath(
                'ancestor::tr/preceding-sibling::tr[td[@class="a54cl"]]'
            )

            docket, title, *_ = [
                tr_text
                for tr_text in precedingTRs[-1].xpath(".//text()")
                if tr_text.strip()
            ]

            disposition = (
                link.getparent().xpath(".//text()")[0]
                if link.getparent().get("class") == "a70"
                else ""
            )

            judge_str = (
                "".join(
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
                if disposition
                else ""
            )

            judges = re.findall(self.judge_xp, judge_str)
            if judges:
                author = judges[0]
                per_curiam = False
            else:
                author = ""
                per_curiam = True

            lower_court, lower_court_number, lower_court_id = (
                self.parse_lower_court_info(title)
            )

            title_regex = r"^(?P<name>.*?)(?=; from|(?=\([^)]*\)$))"
            title_match = re.search(title_regex, title, flags=re.MULTILINE)

            self.cases.append(
                {
                    "name": titlecase(
                        title_match.group("name") if title_match else title
                    ),
                    "disposition": disposition,
                    "url": link.get("href"),
                    "docket": docket,
                    "date": date,
                    "type": self.extract_type(link),
                    "per_curiam": per_curiam,
                    "judge": ", ".join(judges),
                    "author": author,
                    "lower_court": lower_court,
                    "lower_court_number": lower_court_number,
                    "lower_court_id": lower_court_id,
                }
            )

    @staticmethod
    def parse_lower_court_info(title: str) -> tuple[str, str, str]:
        """Parses lower court information from the title string

        :param title: a string with lower court information
        :return: values for lower_court, lower_court_number, lower_court_id
        """

        # Format when appeal comes from texapp districts. Example:
        # ' from Harris County; 1st Court of Appeals District (01-22-00182-CV, 699 SW3d 20, 03-23-23)'
        texapp_regex = r" from (?P<lower_court>.*)\s*\("

        # Format when appeal comes from other possible courts. Examples:
        #  "(U.S. Fifth Circuit 23-10804)"
        #  "(U.S. 5th Circuit 19-51012)"
        # "(BODA Cause No. 67623)"
        other_courts_regex = r"\((?P<lower_court>(BODA|U\.S\. (Fif|5)th Circuit))\s(?P<lower_number>(Cause No. )?[\d-]+)\)$"

        if match := re.search(texapp_regex, title):
            lower_court = match.group("lower_court")
            lower_court_number = title[match.end() :].split(",")[0]
            return lower_court, lower_court_number, "texapp"

        elif match := re.search(other_courts_regex, title):
            lower_court = match.group("lower_court")
            lower_court_number = match.group("lower_number")

            if lower_court == "BODA":
                lower_court = "Board of Disciplinary Appeals"
                lower_court_id = "txboda"
            else:
                # if this is not a BODA match, then it can only be a
                # Fifth Circuit match. Update this if the regex above changes
                lower_court_id = "ca5"

            return lower_court, lower_court_number, lower_court_id

        return "", "", ""

    @staticmethod
    def extract_type(link: etree.Element) -> str:
        """Determines the opinion type

        :param link (etree.Element) The anchor element containing the PDF link.
        :return str The opinion type as a string.
        """
        text = link.text.lower()
        url = link.get("href")
        if "per curiam" in text or url.endswith("pc.pdf"):
            op_type = OpinionType.UNANIMOUS
        elif "in part" in text or url.endswith("cd.pdf"):
            op_type = OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
        elif "dissenting" in text or url.endswith("d.pdf"):
            op_type = OpinionType.DISSENT
        elif "concurring" in text or url.endswith("c.pdf"):
            op_type = OpinionType.CONCURRENCE
        else:
            op_type = OpinionType.MAJORITY
        return str(op_type.value)

    def make_backscrape_iterable(self, kwargs) -> None:
        """Checks if backscrape start and end arguments have been passed

        Texas opinions page returns all opinions for a year (pagination is not needed),
        so we must filter out opinions not in the date range we are looking for

        :return None
        """
        super().make_backscrape_iterable(kwargs)

        # use the parsed values to compute the actual iterable
        start = self.back_scrape_iterable[0][0]
        end = self.back_scrape_iterable[-1][-1]

        dates = []
        for year in list(range(start.year, end.year + 1)):
            dates.append((year, start, end))
        self.back_scrape_iterable = dates

    def _download_backwards(self, analysis_window: tuple) -> None:
        """Downloads and processes opinions for a given year within a specified date range.

        :param analysis_window (tuple): A tuple containing the year (int), start date (date), and end date (date).
        :return None
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
