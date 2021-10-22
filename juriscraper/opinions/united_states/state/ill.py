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
                status = get_row_column_text(row, 6)
                if status == "NRel":
                    status = "Unpublished"
                else:
                    status = "Published"
                name = get_row_column_text(row, 1)
                citation = get_row_column_text(row, 2)
                redirect_url = get_row_column_links(row, 1)
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
        case_uuid = raw_url.lstrip(
            "https://www.illinoiscourts.gov/resources/"
        ).rstrip("/file")
        file_name = quote(f"{case_name}, {case_citation}.pdf")
        return f"https://ilcourtsaudio.blob.core.windows.net/antilles-resources/resources/{case_uuid}/{file_name}"

    def extract_docket(self, case_citation):
        # RegEx: "{YYYY: year_4_digit} IL {docket_number}"
        search = re.search(r"(?:[0-9]{4}\s+IL\s+)([0-9]+)", case_citation)
        if search:
            docket = search.group(1)
        else:
            docket = ""
        return docket
