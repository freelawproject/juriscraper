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

from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.lib.test_utils import MockRequest
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    start_year = 1997
    current_year = 2024
    court = "sc"
    court_number = 1
    base_url = "http://appellate.nccourts.org/opinion-filings/?c={}&year={}"
    headnote_test_url = (
        "tests/examples/opinions/united_states/nc_headnote.html"
    )
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

        Iterates over each row in the HTML, extracting the title, link, summary, headnote,
        docket, status, author, per curiam status, date, and citation for each opinion.
        Handles cases where opinions may be withdrawn (no link), and parses additional
        information from the headnote HTML if available.

        Appends a dictionary of extracted case data to self.cases for each valid row.
        """
        for row in self.html.xpath(self.row_xpath):
            title = row.xpath("string(span[@class='title'])")

            link = row.xpath("span[@class='title']/@onclick")
            if not link:
                # some opinions may be withdrawn
                logger.warning("No link for row %s", title)
                continue

            url = link[0].split('("')[1].strip('")')

            summary = (
                row.xpath("string(span[@class='desc'])")
                if self.collect_summary
                else ""
            )
            headnote = (
                ""
                if self.collect_summary
                else row.xpath("string(span[@class='desc'])")
            )

            url = url.replace("http:", "https:")
            divs = self.headnote_html.xpath(
                f'(//a[@href="{url}"]/ancestor::p)[1]'
            )
            if divs:
                p_elt = divs[0]
                all_text = p_elt.xpath("text()")

                summary = "".join(
                    text.replace("—", "")
                    for text in all_text
                    if not (text.startswith("<b>") or text.startswith("<a"))
                ).strip()
                headnote = p_elt.xpath("./b//text()")[0]

            match = re.search(self.title_regex, title)
            name = title[: match.start()].strip(" ,")

            state_cite = ""
            if cite_match := re.search(self.state_cite_regex, name):
                state_cite = cite_match.group(0)
                name = name[: cite_match.start()].strip(" ,")

            docket = match.group("docket")
            status = match.group("status")

            author = row.xpath("string(span[@class='author']/i)").strip()
            per_curiam = False
            if author.lower() == "per curiam":
                per_curiam = True
                author = ""

            # pick the last preceding-sibling, the most recent date block
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
                    "author": author,
                    "per_curiam": per_curiam,
                    "summary": summary,
                    "headnote": headnote,
                    "status": status,
                    "docket": docket,
                    "name": name,
                    "url": url,
                    "date": date,
                    "citation": state_cite,
                }
            )

    def _download_backwards(self, year: int) -> None:
        """Build year URL and scrape

        :param year: year to scrape
        :return None
        """
        self.url = self.base_url.format(self.court, year)
        self.html = self._download()

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

    def _download(self, request_dict=None):
        """
        Download and parse the headnote HTML for the current court and year.

        This method fetches the digested index page for the specified court and year,
        parses the HTML to extract headnote information, and stores it in `self.headnote_html`.
        If test mode is enabled, it uses a mock request and a test HTML file.

        Args:
            request_dict (dict, optional): Additional request parameters. Defaults to None.

        Returns:
            The result of the superclass's _download method.
        """
        if request_dict is None:
            request_dict = {}

        if self.html is None:
            url = f"https://appellate.nccourts.org/opinion-filings/digested-index.php?iCourtNumber={self.court_number}&sFilingYear={self.current_year}"

        if self.test_mode_enabled():
            self.request["url"] = self.headnote_test_url
            r = self.request["response"] = MockRequest(
                url=self.headnote_test_url
            ).get()
        else:
            r = self.request["session"].get(url)
        self.headnote_html = fromstring(r.text)
        return super()._download(request_dict)
