"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl.

Notes:
    Scraper adapted for new website as of February 20, 2014.
    2024-10-23, grossir: implemented new site
"""

import json

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
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

            # Append a "V" as seen in the opinions PDF for the vaccine
            # claims. This will help disambiguation, in case docket
            # number collide
            if self.is_vaccine and not docket.lower().endswith("v"):
                docket += "V"

            judge = judges_mapper.get(opinion["judge"], "")
            self.cases.append(
                {
                    "url": opinion["link"],
                    "summary": opinion["text"],
                    "date": opinion["date"],
                    "status": (
                        "Unpublished"
                        if opinion["criteria"] == "unreported"
                        else "Published"
                    ),
                    "judge": judge,
                    "name": titlecase(name),
                    "docket": docket,
                }
            )
