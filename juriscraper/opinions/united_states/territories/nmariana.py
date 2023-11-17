"""Scraper for Supreme Court of Northern Mariana Islands
CourtID: nmi
Court Short Name: NMI
Author: William Edward Palin
History:
  2023-01-21: Created by William Palin
"""
import re
from datetime import date
from typing import Any, Dict

from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = str(date.today().year)[-2:]
        self.url = f"https://www.cnmilaw.org/spm{year}.php#gsc.tab=0"
        self.status = "Published"

    def _cleanup_judge_names(self, judges: str) -> [str]:
        """Extract judge panel

        Because of a judge Torres,Jr. - and the various permutations of his
        Jr with and without commas and spacing we do a bit of cleanup to
        get his and the other judges corretly.  Additionally the author is
        sometimes denoted by a *.  This is cleaned up.

        :param judges: Content of the panel as a string
        :return: Judges as a string list
        """
        judges = [
            j.replace(" Jr.", "Jr.").strip(" *") for j in judges.split(",")
        ]
        judges = [j.replace("Jr.", " Jr.") for j in judges]
        return judges

    def _fetch_author(self, judges: str) -> str:
        """Parse the author from the judge text

        :param judges: Cell content
        :return: The author
        """
        if "*" not in judges:
            author = "Per Curiam"
        else:
            author = [j for j in judges.split(",") if "*" in j][0].strip("*")
        return author

    def _process_html(self):
        for s in self.html.xpath(".//td/a/@href[contains(., 'pdf')]/../../.."):
            cells = s.xpath(".//td")
            judge_text = cells[3].text_content()
            self.cases.append(
                {
                    "name": cells[0].text_content(),
                    "citation": cells[1].text_content(),
                    "date": cells[2].text_content(),
                    "judges": self._cleanup_judge_names(judge_text),
                    "author": self._fetch_author(judge_text),
                    "url": s.xpath(".//td/a/@href")[0],
                    "docket": "",
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata containing the docket number
        """
        normalized_content = normalize_dashes(scraped_text)
        match = re.findall(r"Case No\.: (.*)", normalized_content)
        docket_number = match[0] if match else ""
        metadata = {
            "Docket": {
                "docket_number": docket_number,
            },
        }
        return metadata
