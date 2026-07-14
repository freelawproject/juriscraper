#  Scraper for Third Circuit of Appeals
# CourtID: ca3
# Court Short Name: ca3
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 18 July 2014
# History:
#  - 2026-07-11: The court replaced its RSS feed and .aspx file lists
#    with plain HTML file lists; rewritten to parse those.

import re
from urllib.parse import unquote

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import fix_camel_case
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    docket_regex = r"\d{2}-\d{3,4}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Files posted in the last 30 days. OralArgContents7.html and
        # OralArgContentsAll.html list the last 7 days and everything
        self.url = "https://www2.ca3.uscourts.gov/OralArgContents30.html"

    def _process_html(self) -> None:
        """Parse the file-list table

        Each row holds a link to an audio file and the datetime it was
        posted. Dockets and the case name are packed into the file name,
        e.g. '20-3216_20-3242_25-2003_USAvMiner_Wootton_Miner.mp3'

        :return None
        """
        for row in self.html.xpath("//table//tr[td]"):
            links = row.xpath(".//a/@href")
            dates = row.xpath("./td[2]/text()")
            if not links or not dates:
                logger.warning(
                    "ca3: skipping row without link or date: %s",
                    " ".join(row.text_content().split()),
                )
                continue

            url = links[0]
            stem = unquote(url.split("/")[-1]).rsplit(".", 1)[0]
            # Drop trailing re-upload markers, e.g.
            # '24-3226_USAvHodges_a.mp3' is a re-upload of the same audio
            # as '24-3226_USAvHodges.mp3' (see #2019). Both entries are
            # ingested; stripping the marker keeps the case name clean
            # and makes the duplicates easy to spot upstream
            stem = re.sub(r"_[a-z]$", "", stem)

            # Dockets are packed at the front of the name, usually
            # underscore-separated, sometimes glued to the case name
            leading_dockets = re.match(rf"(?:{self.docket_regex}[_&]*)+", stem)
            if leading_dockets:
                dockets = re.findall(
                    self.docket_regex, leading_dockets.group(0)
                )
                name_str = stem[leading_dockets.end() :].strip("_ ")
            else:
                dockets = []
                name_str = stem

            name = " ".join(fix_camel_case(name_str).replace("_", " ").split())

            self.cases.append(
                {
                    "url": url,
                    "docket": ", ".join(dockets),
                    "name": name,
                    # e.g. '6/26/2026 9:37:40 AM'; keep the date only
                    "date": dates[0].split()[0],
                }
            )
