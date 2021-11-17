"""
Contact: webmaster@illinoiscourts.gov, 217-558-4490, 312-793-3250
History:
  2013-08-16: Created by Krist Jin
  2014-12-02: Updated by Mike Lissner to remove the summaries code.
  2016-02-26: Updated by arderyp: simplified thanks to new id attribute identifying decisions table
  2016-03-27: Updated by arderyp: fixed to handled non-standard formatting
  2021-11-02: Updated by satsuki-chan: Updated to new page design.
"""
import re
from typing import List

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
            r"(?P<docket>\d{5,10})-?U?[BCD]?"
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

            name = get_row_column_text(row, 1)
            date = get_row_column_text(row, 3)
            citation = get_row_column_text(row, 2)
            try:
                url = get_row_column_links(row, 1)
            except IndexError:
                # If the opinion file's information is missing (as with
                # links to withdrawn opinions), skip record
                continue
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "neutral_citation": citation,
                    "url": url,
                }
            )

    def _get_precedential_statuses(self) -> List[str]:
        """Extract the precedential status

        If citation contains -U - mark case as unpublished.

        Return: List of precedential statuses
        """
        return [
            "Unpublished" if "-U" in case["neutral_citation"] else "Published"
            for case in self.cases
        ]

    def _get_docket_numbers(self) -> List[str]:
        """Get the docket number from citation.

        Returns: List of docket numbers
        """
        dockets_numbers = []
        for case in self.cases:
            m = re.search(self.docket_re, case["neutral_citation"])
            dockets_numbers.append(m.group("docket"))
        return dockets_numbers
