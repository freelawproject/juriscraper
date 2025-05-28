"""
Scraper for the Supreme Court of Tennessee
CourtID: tenn
Court Short Name: Tenn.
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.tncourts.gov/courts/supreme-court/opinions"
        self.court_id = self.__module__
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath("//tr"):
            date = (
                row.xpath(
                    ".//td[contains(@class, 'views-field-field-opinions-date-filed')]"
                )[0]
                .text_content()
                .strip()
            )
            lower_court = (
                row.xpath(
                    ".//td[contains(@class, 'views-field-field-opinions-county')]"
                )[0]
                .text_content()
                .strip()
            )
            section = row.xpath(
                ".//td[contains(@class, 'views-field-field-opinions-case-number')]"
            )[0]
            url = section.xpath(".//a")[0].get("href")

            name_text = section.xpath(".//a")[0].text_content()
            type_match = re.search(r"\(([^)]+)\)", name_text)
            type_raw = type_match.group(1).lower() if type_match else ""

            if "concurring" in type_raw:
                type = "030concurrence"
            elif "in part" in type_raw:
                type = "035concurrenceinpart"
            elif "dissenting" in type_raw:
                type = "040dissent"
            else:
                type = type_raw

            name = re.sub(r"\s*\([^)]+\)", "", name_text).strip()
            rows = [
                row.strip()
                for row in section.text_content().strip().split("\n", 4)
            ]

            judge = (
                rows[2].split(": ")[1] if "judge" in rows[2].lower() else ""
            )
            summary = rows[-1] if "Judge" not in rows[-1] else ""
            per_curiam = False
            if "curiam" in judge.lower():
                judge = ""
                per_curiam = True

            self.cases.append(
                {
                    "date": date,
                    "lower_court": lower_court,
                    "url": url,
                    "name": name,
                    "docket": rows[1],
                    "judge": judge,
                    "summary": summary,
                    "per_curiam": per_curiam,
                    "type": type,
                }
            )
