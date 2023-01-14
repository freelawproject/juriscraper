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

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.docket_re = r"\d{4} IL (?P<docket>\d+)"
        self.url = (
            f"https://www.illinoiscourts.gov/top-level-opinions?type=supreme"
        )
        self.status = "Published"

    def _get_docket(self, match):
        return match.group("docket")

    def _get_status(self, citation):
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
            date = get_row_column_text(row, 3)
            match = re.search(self.docket_re, citation)
            try:
                url = get_row_column_links(row, 1)
            except IndexError:
                logger.warning(
                    f"Opinion '{citation}' has no URL. (Likely a withdrawn opinion)."
                )
                continue

            if not match:
                logger.warning(f"Opinion '{citation}' has no docket.")
                continue

            docket = self._get_docket(match)
            status = self._get_status(citation)

            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "citation": citation,
                    "url": url,
                    "docket": docket,
                    "status": status,
                }
            )
