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
                    status = get_row_column_text(row, 6)
                    # NRel = Not Published
                    if status == "NRel":
                        status = "Unpublished"
                    else:
                        status = "Published"
                    name = get_row_column_text(row, 1)
                    citation = get_row_column_text(row, 2)
                    redirect_url = get_row_column_links(row, 1)
                except IndexError:
                    # If the opinion file's information is missing, skip record
                    continue

                url = self.set_file_url(redirect_url, name, citation)
                docket = self.extract_docket(citation)
                self.cases.append(
                    {
                        "date": get_row_column_text(row, 3),
                        "docket": docket,
                        "name": name,
                        "neutral_citation": citation,
                        "url": url,
                        "status": status,
                    }
                )

    def set_file_url(self, raw_url, case_name, case_citation):
        # Opinions' URL redirect to the real PDF files' URL, this redirection
        # might cause problems when downloading files in CourtListener
        search = re.search(
            r"(?:.*\/resources\/)([0-9A-Za-z]{8}-[0-9A-Za-z]{4}-4[0-9A-Za-z]{3}-[89ABab][0-9A-Za-z]{3}-[0-9A-Za-z]{12})(?:\/file)",
            raw_url,
        )
        if search:
            case_uuid = search.group(1)
            file_name = quote(f"{case_name}, {case_citation}.pdf")
            url = f"https://ilcourtsaudio.blob.core.windows.net/antilles-resources/resources/{case_uuid}/{file_name}"
        else:
            url = ""
            logger.warning(f"Case UUID not found: {raw_url}")
        return url

    def extract_docket(self, case_citation):
        # RegEx: "{YYYY: year_4_digit} IL {docket_number}"
        search = re.search(r"(?:[0-9]{4}\s+IL\s+)([0-9]+)", case_citation)
        if search:
            docket = search.group(1)
        else:
            docket = ""
            logger.warning(f"Docket not found: {case_citation}")
        return docket
