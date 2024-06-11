# Author: Phil Ardery
# Contact: https://www.ndcourts.gov/contact-us
# Date created: 2019-02-28
# Updated: 2024-05-08, grossir: to OpinionSiteLinear and new URL
import re
from typing import Tuple
from urllib.parse import urljoin

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.ndcourts.gov/"
    ordered_fields = [
        "name",
        "docket",
        "date",
        "nature_of_suit",
        "judge",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ndcourts.gov/supreme-court/opinions?topic=&author=&searchQuery=&trialJudge=&pageSize=100&sortOrder=1"
        self.status = "Published"

    def _process_html(self) -> None:
        """Most values are inside a <p>: whitespace and
        field names need to be cleaned

        Citation used to be available, now must be got from inside
        the document's text
        """
        for row in self.html.xpath('//table//div[@class="row"]'):
            raw_values = list(map(str.strip, row.xpath("./div/p[1]/text()")))
            values = []

            for idx, txt in enumerate(raw_values[:5]):
                if idx == 0:
                    txt, extra_docket = self.clean_name(txt)
                else:
                    txt = txt.split(":", 1)[1].strip()
                values.append(txt)

            summary = (
                " ".join(raw_values[5:]).strip() if len(raw_values) > 5 else ""
            )
            url = urljoin(
                self.base_url,
                row.xpath(".//button[@onclick]/@onclick")[0].split("'")[1],
            )
            case = dict(zip(self.ordered_fields, values[:5]))
            case["summary"] = summary
            case["url"] = url

            # There is a per_curiam field on the CL Opinion model,
            # but we don't process it if sent by the scraper
            if "Per Curiam" in case["judge"]:
                case["judge"] = ""

            self.cases.append(case)

    def _get_nature_of_suit(self):
        return [case["nature_of_suit"] for case in self.cases]

    def clean_name(self, name: str) -> Tuple[str, str]:
        """Cleans case name

        Some case names list the consolidated docket or a
        (CONFIDENTIAL) parentheses

        :param name: raw case name
        :return: cleaned name and extra_docket numbers
        """
        other_dockets = ""
        if "(consolidated w/" in name:
            other_dockets = ",".join(re.findall(r"\d{8}", name))
            name = name.split("(consolidated w/")[0]
        if "(CONFIDENTIAL" in name:
            name = name.split("(CONFIDENTIAL")[0]

        return name.strip(), other_dockets

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract Citation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        regex = r"(?P<vol>20\d{2})\sND\s(?P<page>\d+)"
        match = re.search(regex, scraped_text[:1000])

        if match:
            return {
                "Citation": {
                    "volume": match.group("vol"),
                    "reporter": "ND",
                    "page": match.group("page"),
                    "type": 8,  # NEUTRAL in courtlistener Citation model
                },
            }
        return {}
