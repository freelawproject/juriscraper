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
#  - 2026-07-11; Fix date extraction after order page layout change

import re
from datetime import date
from datetime import datetime as dt

from lxml import etree

from juriscraper.AbstractSite import logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.type_utils import OpinionType


class Site(ClusterSite):
    base_url = "https://www.txcourts.gov/supreme/orders-opinions/{}/"
    # link_xp targets the year-index page's bullet list of dated order
    # subpages (one <li><a> per date); date_xp targets the "Orders
    # Pronounced …" header on a single day's order page. It is anchored
    # on that text rather than the page layout, which changed in
    # June 2026.
    link_xp = '//*[@id="MainContent"]/div/div/div/ul/li/a/@href'
    date_xp = '//div[contains(text(), "Orders Pronounced")]/text()'
    date_regex = r"Orders Pronounced\s+(?P<date>.+)"
    judge_regex = r"(?:Chief\s)?Justice\s([A-Z][a-zA-Z]+)"
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

    async def _download(self, request_dict=None):
        """Downloads the HTML content for the current opinion page.

        :param request_dict (dict, optional): Additional request parameters.
        :return The downloaded HTML content.
        """
        if request_dict is None:
            request_dict = {}

        if not self.is_backscrape and not self.test_mode_enabled():
            self.html = await super()._download(request_dict)
            links = self.html.xpath(self.link_xp)
            if not links:
                # No orders posted yet (common in early January)
                self.html = None
                logger.error("tex: no date list on opinions page")
                return None
            self.url = links[-1]

        self.html = await super()._download(request_dict)
        return self.html

    async def _process_html(self) -> None:
        """Parses the HTML content

        :return None
        """
        if self.html is None:
            return

        date_strings = self.html.xpath(self.date_xp)
        if not date_strings:
            logger.error("tex: no 'Orders Pronounced' header on order page")
            return
        date_match = re.search(self.date_regex, date_strings[0])
        if not date_match:
            logger.error(
                "tex: unable to parse date from 'Orders Pronounced' header"
            )
            return
        date = date_match.group("date").strip()
        # Each day's page contains many PDF links; only those inside a
        # <span class="a70"> (court opinion + disposition cell) or
        # <span class="a79"> (separate opinion cell — concurrence /
        # dissent) belong to an opinion. Everything else (orders PDF,
        # case summaries, admin docs) gets filtered out below.
        links = self.html.xpath('//a[contains(@href, ".pdf")]')
        for link in links:
            if link.getparent() is None or link.getparent().get(
                "class"
            ) not in ["a79", "a70"]:
                logger.info(
                    "Skipping row with link %s", link.attrib.get("href")
                )
                continue

            # The page's table interleaves header rows with cells of
            # class "a50cl" (docket number) and "a54cl" (case title)
            # before each opinion row. Walk back from the opinion's row
            # to find the most recent header row — its last entry is
            # the docket+title pair belonging to this opinion.
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

            parent = link.getparent()
            # When the first element under <span class="a70"> is the
            # link itself, the cell has no disposition prose — the
            # parent's .text is the judge intro, not the disposition.
            has_disposition = (
                parent.get("class") == "a70" and parent[0].tag != "a"
            )
            disposition = (
                parent.xpath(".//text()")[0] if has_disposition else ""
            )

            # Judge intro text sits on the preceding sibling's tail when
            # a <br> separates entries, but on the parent's own .text
            # when this is the first link in the cell.
            previous = link.getprevious()
            leading = previous.tail if previous is not None else parent.text
            judge_str = (
                "".join(x for x in [leading, link.text, link.tail] if x)
                if parent.get("class") == "a70"
                else ""
            )

            author = ""
            joined_by = ""
            judge = ""

            judges = re.findall(self.judge_regex, judge_str)
            if judges:
                author = judges[0]
                judge = "; ".join(judges)
            if len(judges) > 1:
                joined_by = "; ".join(judges[1:])

            per_curiam = "per curiam" in link.text_content().lower()

            lower_court, lower_court_number, lower_court_id = (
                self.parse_lower_court_info(title)
            )

            title_regex = r"^(?P<name>.*?)(?=; from|(?=\([^)]*\)$))"
            title_match = re.search(title_regex, title, flags=re.MULTILINE)
            case_dict = {
                "name": titlecase(
                    title_match.group("name") if title_match else title
                ),
                "disposition": disposition,
                "url": link.get("href"),
                "docket": docket,
                "date": date,
                "type": self.extract_type(link),
                "per_curiam": per_curiam,
                "judge": judge,
                "author": author,
                "joined_by": joined_by,
                "lower_court": lower_court,
                "lower_court_number": lower_court_number,
                "lower_court_id": lower_court_id,
            }

            if cluster := self.cluster_opinions(case_dict, self.cases):
                cluster["judge"] += f"; {case_dict['judge']}"
            else:
                self.cases.append(case_dict)

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
        elif "statement" in text:
            # e.g. "Statement of Justice Devine respecting the denial of
            # the petition for writ of mandamus". CourtListener has no
            # statement type; a non-dissenting separate writing is
            # closest to a concurrence
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

    async def _download_backwards(
        self, analysis_window: tuple[int, date, date]
    ) -> None:
        """Downloads and processes opinions for a given year within a specified date range.

        :param analysis_window (tuple): A tuple containing the year (int), start date (date), and end date (date).
        :return None
        """
        self.is_backscrape = True
        year, start, end = analysis_window
        self.url = self.base_url.format(year)
        await self._download()

        for path in self.html.xpath(self.link_xp):
            if "historical" in path:
                # in 2014 they have an extra link for pre-2014 ops
                continue
            date_str = path.strip("/").split("/")[-1]
            date_obj = dt.strptime(date_str, "%B-%d-%Y").date()

            if not (start <= date_obj <= end):
                continue

            self.url = path
            await self._download()
            await self._process_html()
