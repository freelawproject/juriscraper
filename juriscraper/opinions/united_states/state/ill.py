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
  2021-12-30: Updated by satsuki-chan: Added validation when citation is missing.
"""
import re
from typing import List

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.illinoiscourts.gov/top-level-opinions?type=supreme"
        )
        self.docket_re = (
            r"(?P<year>\d{4})? ?"
            r"(?P<court>(IL App)|(IL)) "
            r"(\(?(?P<district>[1-5])\w{1,2}\))? ?"
            r"(?P<docket>\d{5,10}\w{1,2})-?U?[BCD]?"
        )

    def _process_html(self) -> None:
        """Process HTML

        Iterate over each table row.
        If a table row does not have a link - skip it and assume
        the opinion has been withdrawn.

        Return: None
        """
        for row in self.html.xpath("//table[@id='ctl04_gvDecisions']/tr"):
            cells = row.xpath(".//td")
            # Don't parse pagination rows or headers or footers
            if len(cells) != 7 or row.xpath(".//table"):
                continue
            try:
                url = get_row_column_links(row, 1)
            except IndexError:
                logger.info(f"Opinion without URL to file: '{str(row)}'")
                # If the opinion file's information is missing (as with
                # links to withdrawn opinions), skip record
                continue
            citation = get_row_column_text(row, 2)
            if not citation:
                logger.info(f"Opinion without citation: '{str(row)}'")
                # If the opinion citation is missing, skip record
                continue
            name = get_row_column_text(row, 1)
            date = get_row_column_text(row, 3)
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "citation": citation,
                    "url": url,
                }
            )

    def _get_precedential_statuses(self) -> List[str]:
        """Extract the precedential status

        If citation contains -U - mark case as unpublished.

        Return: List of precedential statuses
        """
        return [
            "Unpublished" if "-U" in case["citation"] else "Published"
            for case in self.cases
        ]

    def _get_docket_numbers(self) -> List[str]:
        """Get the docket number from citation.
        Examples:
            Citation         - Docket
            "2019 IL 123318" - 123318
            "2020 IL 124831" - 124831
            "2021 IL 126432" - 126432
        Returns: List of docket numbers
        """
        dockets_numbers = []
        for case in self.cases:
            match = re.search(self.docket_re, case["neutral_citation"])
            if match:
                dockets_numbers.append(match.group("docket"))
            else:
                logger.critical(f"Could not find docket for case: '{case}'")
                raise InsanityException(
                    f"Could not find docket for case: '{case}'"
                )
        return dockets_numbers
