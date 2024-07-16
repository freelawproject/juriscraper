# Scraper for Supreme Court of Oklahoma
# CourtID: okla
# Court Short Name: OK
# Court Contact: webmaster@oscn.net
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05


import re
from datetime import datetime
from typing import Any, Dict

from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = datetime.today().year
        self.url = f"https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSSC&year={year}&level=1"
        self.status = "Published"
        self.expected_content_types = ["text/html"]

    def _process_html(self):
        rows = self.html.xpath("//div/p['@class=document']")[::-1]
        for index, row in enumerate(rows):
            date_filed_is_approximate = False
            row_text = row.text_content()
            if "OK" not in row_text or "EMAIL" in row_text:
                continue
            if "P.3d" in row_text:
                citation1, citation2, date, name = row_text.split(",", 3)
                citation = f"{citation1} {citation2}"
            elif re.search(r"\d{2}/\d{2}/\d{4}", row_text):
                citation, date, name = row_text.split(",", 2)
            else:
                citation, name = row_text.split(",", 1)
                date_filed_is_approximate = True
                if index > 0:
                    date = self.cases[-1]["date"]
                else:
                    date = datetime(datetime.now().year, 7, 1)

            self.cases.append(
                {
                    "date": date,
                    "date_filed_is_approximate": date_filed_is_approximate,
                    "name": name,
                    "docket": citation,
                    "url": row.xpath(".//a")[0].get("href"),
                    "citation": citation,
                }
            )

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath("//*[@id='oscn-content']")[0]
        return html.tostring(
            core_element, pretty_print=True, encoding="unicode"
        ).encode("utf-8")

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extract docket number from first section of downloaded HTML

        Examples on oklacrimapp: F-2022-247, RE-2022-638, S-2023-720
        Examples on oklacivapp: 120813
        Examples on okla:  SCBD-7522

        :param scraped_text: Text of scraped content
        :return: Dict in the format expected by courtlistener,
                 containing Docket.docket_number
        """
        docket_match = re.search(
            r"Case Number:\s+(?P<docket>[\w\d-]+)", scraped_text[:1000]
        )
        if docket_match:
            return {
                "Docket": {"docket_number": docket_match.group("docket")},
            }

        return {}
