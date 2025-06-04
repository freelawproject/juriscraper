# Scraper for Texas Supreme Court
# CourtID: tex
# Court Short Name: TX
# Court Contacts:
#  - http://www.txcourts.gov/contact-us/
#  - Blake Hawthorne <Blake.Hawthorne@txcourts.gov>
#  - Eddie Murillo <Eddie.Murillo@txcourts.gov>
#  - Judicial Info <JudInfo@txcourts.gov>
# author: Andrei Chelaru
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

from datetime import date, datetime

from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.type_utils import OpinionType
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.txcourts.gov/supreme/orders-opinions/{}/"
    dispo_xpath = ".//span[contains(@class, 'a70')]/node()[following-sibling::br]/descendant-or-self::text()"
    judge_xpath = ".//span[contains(@class, 'a70')]/br[1]/following-sibling::node()/descendant-or-self::text()"
    first_opinion_date = date(2014, 10, 3)
    current_opinion_date = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.current_year = date.today().year
        self.url = self.base_url.format(self.current_year)
        self.status = "Published"
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)

    def _download(self, request_dict=None):
        if request_dict is None:
            request_dict = {}

        if not self.is_backscrape and not self.test_mode_enabled():
            self.html = super()._download(request_dict)
            self.url = self.html.xpath(
                '//*[@id="MainContent"]/div/div/div/ul/li/a/@href'
            )[-1]
            self.current_opinion_date = self.html.xpath(
                '//*[@id="MainContent"]/div/div/div/ul/li/a/text()'
            )[-1]
            return super()._download(request_dict)
        else:
            if self.test_mode_enabled():
                self.current_opinion_date = "May 23, 2025"
            self.html = super()._download(request_dict)
            return self.html

    def _process_html(self):
        pdf_table_rows = self.html.xpath(
            '//a[contains(@href, ".pdf")]/ancestor::tr'
        )
        for row in pdf_table_rows:
            links = row.xpath('.//a[contains(@href, ".pdf")]')
            for link in links:
                url, name, docket = None, None, None
                docket_paths = row.xpath(
                    'preceding-sibling::tr[.//td[@class="a50cl"]][1]'
                )
                name_paths = row.xpath(
                    'preceding-sibling::tr[.//td[@class="a54cl"]][1]'
                )
                if docket_paths == [] or name_paths == []:
                    continue

                if link.text is None:
                    continue

                url = link.xpath("@href")[-1]
                docket = docket_paths[0].xpath(".//div[@class='a50']/text()")[
                    0
                ]
                name = titlecase(
                    name_paths[0]
                    .xpath(".//div[@class='a54']/text()")[0]
                    .split(";")[0]
                )
                type, per_curiam = self.extract_type(url)
                dispositions = row.xpath(self.dispo_xpath)
                if not dispositions:
                    continue
                judges_str = "".join(row.xpath(self.judge_xpath))
                judge = "" if per_curiam else judges_str.split("delivered")[0]
                joined_by = (
                    judges_str.split("in which")[-1]
                    if "in which" in judges_str
                    else ""
                )
                joined_by = (
                    joined_by.replace("joined.", "")
                    .replace("and", ",")
                    .replace(".", "")
                    .replace(" , ", ",")
                    .strip()
                )

                self.cases.append(
                    {
                        "name": name,
                        "disposition": dispositions[0],
                        "url": url,
                        "docket": docket,
                        "date": self.current_opinion_date,
                        "type": type,
                        "per_curiam": per_curiam,
                        "judge": judge,
                        "joined_by": joined_by,
                    }
                )

    def _download_backwards(self, target_date: date) -> None:
        """Method used by backscraper to download historical records

        :param target_date: an element of self.back_scrape_iterable
        :return: None
        """
        self.is_backscrape = True
        self.url = self.base_url.format(target_date)
        self.html = self._download()
        for link in self.html.xpath(
            '//*[@id="MainContent"]/div/div/div/ul/li/a'
        ):
            self.current_opinion_date = link.xpath("text()")[0]
            link_date = datetime.strptime(
                self.current_opinion_date, "%B %d, %Y"
            ).date()
            if self.start <= link_date <= self.end:
                self.url = link.xpath("@href")[0]
                self._download()
                self._process_html()

    def extract_type(self, url: str) -> tuple[OpinionType, bool]:
        """

        Rules:
        - Ends with 'pc.pdf' → UNANIMOUS + per curiam
        - Ends with 'd.pdf'  → DISSENT
        - Ends with 'c.pdf'  → CONCURRENCE
        - Otherwise          → MAJORITY
        """
        per_curiam = False
        if url.endswith("pc.pdf"):
            op_type, per_curiam = OpinionType.UNANIMOUS, True
        elif url.endswith("d.pdf"):
            op_type = OpinionType.DISSENT
        elif url.endswith("c.pdf"):
            op_type = OpinionType.CONCURRENCE
        else:
            op_type = OpinionType.MAJORITY
        return (op_type, per_curiam)


def make_backscrape_iterable(self, kwargs):
    """
    Initializes the backscrape iterable based on optional start and end dates.

    Args:
        kwargs (dict): Dictionary that may contain 'backscrape_start' and 'backscrape_end'
            as strings in the format 'YYYY/MM/DD'.

    Sets:
        self.start (date): The start date for backscraping.
        self.end (date): The end date for backscraping.
        self.back_scrape_iterable (list): List of years between start and end (inclusive).
    """
    start = kwargs.get("backscrape_start")
    end = kwargs.get("backscrape_end")

    if start:
        self.start = datetime.strptime(start, "%Y/%m/%d").date()
    else:
        self.start = self.first_opinion_date
    if end:
        self.end = datetime.strptime(end, "%Y/%m/%d").date()
    else:
        self.end = datetime.now().date()

    years = list(range(self.start.year, self.end.year + 1))

    self.back_scrape_iterable = years
