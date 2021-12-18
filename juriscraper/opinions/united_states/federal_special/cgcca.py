"""Scraper for US Coast Guard Court of Criminal Appeals
CourtID: cgcca
Court Short Name: C.G. Ct. Crim. App.

Author: Evando Blanco
Reviewer: flooie
History:
    2021-03-29: Created by Evando Blanco
    2021-12-17: Updated by flooie for OpinionSiteLinear
"""


import re
from typing import List

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.citation_regex = (
            r"(?P<MJ>\(?\d{2} M\.J\. \d+\)?)|(?P<WL>\(?\d{4} (WL|Wl) \d+\)?)"
        )
        self.url = "https://www.uscg.mil/Resources/Legal/Court-of-Criminal-Appeals/CGCCA-Opinions/smdsort15701/publicationdate/smdorder15701/desc/"

    def _process_html(self) -> None:
        """Process the HTML

        :return: None
        """
        path = "//table[@class='Dashboard']/tbody/tr"
        for item in self.html.xpath(path):
            url = item.xpath(".//td/a/@href")[0]
            first_cell = item.xpath(".//td/a/text()")[0]
            docket = re.sub(
                r"Docket Nos?\.", "", item.xpath(".//td[2]/text()")[0]
            )
            date_string = item.xpath(".//td[3]/text()")[0]
            m = re.search(self.citation_regex, first_cell)
            if m:
                mj = m.group("MJ") if m.group("MJ") else ""
                wl = m.group("WL") if m.group("WL") else ""
            else:
                mj = ""
                wl = ""

            status = "Published" if m and mj else "Unpublished"

            # Sometimes the title has misc. information in parentheses
            name = first_cell.replace(mj, "").replace(wl, "").strip()
            name = re.sub(r"\(Merits\)|\(Per Curiam\)", "", name, flags=re.I)
            name = name.replace("( )", "")

            self.cases.append(
                {
                    "name": titlecase(name),
                    "date": date_string,
                    "docket": docket,
                    "url": url,
                    "status": status,
                    "west_state_citation": wl.strip("()"),
                    "neutral_citation": mj.strip("()"),
                }
            )

    def _get_west_citations(self) -> List[str]:
        """Get West Citations

        :return: List of citations if any
        """
        return [c["west_state_citation"].strip("()") for c in self.cases]
