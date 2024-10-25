"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl.

Notes:
    Scraper adapted for new website as of February 20, 2014.
    2024-10-23, grossir: implemented new site
"""

import json
import re

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    judge_regex = re.compile(r"Signed by[\w\s]+(Master|Judge)(?P<judge>.+?)\(")
    other_date_regex = re.compile(r"\([Oo]riginally filed:?[\d\s/]+\)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://ecf.cofc.uscourts.gov/cgi-bin/CFC_RecentOpinionsOfTheCourt.pl"
        self.court_id = self.__module__
        self.is_vaccine = "uscfc_vaccine" in self.court_id

    def _process_html(self):
        """The site returns a page with all opinions for this time period
        The opinions are inside a <script> tag, as a Javascript constant
        that will be parsed using json.loads
        """
        judges_mapper = {
            option.get("value"): option.text_content()
            for option in self.html.xpath("//select[@name='judge']//option")
        }
        judges_mapper.pop("UNKNOWN", "")
        judges_mapper.pop("all", "")

        raw_data = (
            self.html.xpath("//script")[0]
            .text_content()
            .strip()
            .strip("; ")
            .split("= ", 1)[1]
        )

        for opinion in json.loads(raw_data):
            docket, name = opinion["title"].split(" &bull; ", 1)

            summary = opinion["text"]
            if judge_match := self.judge_regex.search(summary):
                judge = judge_match.group("judge").strip(" .()")
                # Remove: "Signed by ... . Service on parties made"
                summary = summary[: judge_match.start()].strip(", .()")
            else:
                judge = judges_mapper.get(opinion["judge"], "")

            other_date = ""
            if other_date_match := self.other_date_regex.search(summary):
                other_date = other_date_match.group(0).strip("() ")
                summary = re.sub(self.other_date_regex, "", summary)

            if opinion["criteria"] == "unreported":
                status = "Unpublished"
            elif opinion["criteria"] == "reported":
                status = "Published"
            else:
                status = "Unknown"

            parsed_case = {
                "url": opinion["link"],
                "date": opinion["date"],
                "other_date": other_date,
                "status": status,
                "summary": summary,
                "judge": judge,
                "name": titlecase(name),
                "docket": docket,
            }

            # Append a "V" as seen in the opinions PDF for the vaccine
            # claims. This will help disambiguation, in case docket
            # numbers collide
            if self.is_vaccine:
                if not docket.lower().endswith("v"):
                    yy, number = docket.split("-")
                    parsed_case["docket"] = f"{yy}-{number.zfill(4)}V"

            self.cases.append(parsed_case)
