"""Scraper for North Carolina Supreme Court
CourtID: nc
Court Short Name: N.C.
Reviewer:
History:
    2014-05-01: Created by Brian Carver
    2014-08-04: Rewritten by Jon Andersen with complete backscraper
    2025-04-22: grossir, Update to OpinionSiteLinear
"""

import re
from datetime import datetime

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    start_year = 1997
    current_year = datetime.today().year
    court = "sc"
    court_number = 1
    base_url = "http://appellate.nccourts.org/opinion-filings/?c={}&year={}"

    row_xpath = "//span[span[@class='title']] | //td[span[@class='title']]"
    title_regex = r"\((?P<docket>[\dA-Z-]+)\s+- (?P<status>(Unp|P)ublished)"
    collect_summary = True

    # in the browser inspector the tr-td containers do not appear for `nc`
    # but they do exist in the source inspected as text
    date_xpath = (
        "../../preceding-sibling::tr//strong[contains(text()[1], 'Filed:')] "
    )
    date_regex = r"Filed: (?P<date>[\d\w ]+)"
    secondary_date_regex = None

    # For `nc` opinions (last available in 2022, as of April 2025)
    state_cite_regex = r"\d+ NC \d+"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url.format(self.court, self.current_year)
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        """
        Process the HTML content of the court opinions page and extract case details.
        """
        for row in self.html.xpath(self.row_xpath):
            title = row.xpath("string(span[@class='title'])")
            links = row.xpath("span[@class='title']/@onclick")
            summary = (
                row.xpath("string(span[@class='desc'])")
                if self.collect_summary
                else ""
            )
            if not links:
                logger.warning("No link for row %s", title)
                continue
            url = links[0][13:-2].replace("http:", "https:")
            m = re.search(
                r"(?P<name>.*),?\s?(?P<cite>\d+ NC \d+)? \((?P<docket>.*) - (?P<status>.*)\)",
                title,
            )
            name, citation, docket, status = m.groups()
            author = row.xpath("string(span[@class='author']/i)").strip()
            per_curiam = author == "Per Curiam"
            date_block = row.xpath(self.date_xpath)[-1].text_content()
            if match := re.search(self.date_regex, date_block):
                date = match.group("date")
            else:
                # # for ncctapp unpublished opinions
                date = self.secondary_date_regex.search(date_block).group(
                    "date"
                )
            self.cases.append(
                {
                    "per_curiam": per_curiam,
                    "author": "" if per_curiam else author,
                    "docket": docket,
                    "status": status,
                    "name": name,
                    "url": url,
                    "date": date,
                    "summary": summary,
                    "citation": citation or "",
                }
            )

    def _download_backwards(self, year: int) -> None:
        """Build year URL and scrape

        :param year: year to scrape
        :return None
        """
        self.url = self.base_url.format(self.court, year)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if start else self.start_year
        end = int(end) + 1 if end else self.current_year

        self.back_scrape_iterable = range(start, end)
