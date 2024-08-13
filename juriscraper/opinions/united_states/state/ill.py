"""
Scraper for Illinois Supreme Court
CourtID: ill
Contact: webmaster@illinoiscourts.gov, 217-558-4490, 312-793-3250
History:
  2013-08-16: Created by Krist Jin
  2014-12-02: Updated by Mike Lissner to remove the summaries code.
  2016-02-26: Updated by arderyp: simplified thanks to new id attribute identifying decisions table
  2016-03-27: Updated by arderyp: fixed to handled non-standard formatting
  2021-11-02: Updated by satsuki-chan: Updated to new page design.
  2022-01-21: Updated by satsuki-chan: Added validation when citation is missing.
"""

import re
from datetime import date, datetime
from typing import Tuple

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    days_interval = 200
    first_opinion_date = datetime(1996, 5, 22)
    court_filter = "Supreme Court"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.docket_re = r"\d{4} IL (?P<docket>\d+)"
        self.url = (
            "https://www.illinoiscourts.gov/top-level-opinions?type=supreme"
        )
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _get_docket(self, match: re.match) -> str:
        """Get docket_number from a regex match

        This is overriden in `illappct`

        :param match: a regex match object
        :return: docket_number
        """
        return match.group("docket")

    def _get_status(self, citation: str) -> str:
        """Deduct status from the citation string

        :param citation: citation string

        :return: status Published or Unpublished
        """
        if "-U" in citation:
            return "Unpublished"
        return "Published"

    def _process_html(self) -> None:
        """Process HTML

        Iterate over each table row.
        If a table row does not have a link - skip it and assume
        the opinion has been withdrawn.

        Return: None
        """
        rows = self.html.xpath("//table[@id='ctl04_gvDecisions']/tr")[1:]
        for row in rows:
            # Don't parse rows for pagination, headers, footers or announcements
            if len(row.xpath(".//td")) != 7 or row.xpath(".//table"):
                continue

            name = get_row_column_text(row, 1)
            citation = get_row_column_text(row, 2)
            date_filed = get_row_column_text(row, 3)
            match = re.search(self.docket_re, citation)
            try:
                url = get_row_column_links(row, 1)
            except IndexError:
                logger.warning(
                    "Opinion '%s' has no URL. (Likely a withdrawn opinion).",
                    citation,
                )
                continue

            # For illappct: From 2010 to the past, most rows have no
            # citation string. We would have to implement extract_from_text
            # to get it. However, document formats are different
            if not match:
                logger.warning("Opinion '%s' has no docket.", citation)
                continue

            docket = self._get_docket(match)
            status = self._get_status(citation)

            self.cases.append(
                {
                    "date": date_filed,
                    "name": name,
                    "citation": citation,
                    "url": url,
                    "docket": docket,
                    "status": status,
                }
            )

        if len(rows) - 2 >= 150:
            logger.warning(
                "This source paginates at 150 results. There are 150 results for this page. Some opinions may be lost"
            )

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range POST request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        # Make first request to get hidden input values
        self.method = "GET"
        self.html = self._download()

        self.method = "POST"
        logger.info("Backscraping for range %s %s", *dates)
        self.get_target_page(dates)
        self._process_html()

    def get_target_page(self, dates: Tuple[date]) -> None:
        """Makes requests until target page is loaded
        The number of requests is variable on the "__VIEWSTATE"

        :param dates: start and end date for backscrape

        :return: dictionary with required values
        """
        self.parameters = {
            "__EVENTTARGET": "ctl00$ctl04$ddlFilterFilingDate",
            "ctl00$ctl04$txtFilterPostingFrom": "3/22/2014",
            "ctl00$ctl04$txtFilterPostingTo": "3/22/2025",
            "ctl00$ctl04$ddlFilterFilingDate": "Custom Date Range",
            "ctl00$ctl04$ddlFilterCourtType": self.court_filter,
            "ctl00$ctl04$hdnSortField": "FilingDate",
            "ctl00$ctl04$hdnSortDirection": "DESC",
            "ctl00$ctl04$txtFilterFilingFrom": dates[0].strftime("%-m/%d/%Y"),
            "ctl00$ctl04$txtFilterFilingTo": dates[1].strftime("%-m/%d/%Y"),
        }

        # if this is the first time loading the Custom Date Range filters
        # we need to do 2 requests. Otherwise, 1 is enough.
        # Due to the `site_yielder` used when backscraping, each backscrape
        # iterable seed uses a new scraper object, so we can't reuse viewstates
        for _ in range(2):
            vs = self.html.xpath("//input[@name='__VIEWSTATE']/@value")[0]
            self.parameters["__VIEWSTATE"] = vs
            self.html = self._download()
