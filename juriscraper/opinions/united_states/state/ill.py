# -*- coding: utf-8 -*-
"""
Contact: webmaster@illinoiscourts.gov, 217-558-4490, 312-793-3250
 History:
   2013-08-16: Created by Krist Jin
   2014-12-02: Updated by Mike Lissner to remove the summaries code.
   2016-02-26: Updated by arderyp: simplified thanks to new id attribute identifying decisions table
   2016-03-27: Updated by arderyp: fixed to handled non-standard formatting
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from urllib.parse import quote
import re


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.illinoiscourts.gov/top-level-opinions?type=supreme"
        )

    def _process_html(self):
        for row in self.html.xpath("//table[@id='ctl04_gvDecisions']//tr"):
            cells = row.xpath(".//td")
            if len(cells) == 7:
                try:
                    decision_type = get_row_column_text(row, 5)
                    status = get_row_column_text(row, 6)
                    if decision_type == "Rule 23":
                        status = "Unpublished"
                    elif status == "Published":
                        status = "Published"
                    else:
                        status = "Unnknown"
                    name = get_row_column_text(row, 1)
                    citation = get_row_column_text(row, 2)
                    date = get_row_column_text(row, 3)
                    url = get_row_column_links(row, 1)
                except IndexError:
                    # If the opinion file's information is missing (as with
                    # withdrawn opinions), skip record
                    continue
                docket = self.extract_docket(citation)
                self.cases.append(
                    {
                        "date": date,
                        "docket": docket,
                        "name": name,
                        "neutral_citation": citation,
                        "url": url,
                        "status": status,
                    }
                )

    def extract_docket(self, case_citation):
        # RegEx: "{YYYY: year_4_digit} IL {docket_number}"
        search = re.search(r"(?:[0-9]{4}\s+IL\s+)([0-9]+)", case_citation)
        if search:
            docket = search.group(1)
        else:
            docket = ""
            logger.warning(f"Docket not found: {case_citation}")
        return docket
