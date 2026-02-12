"""
Scraper for the Supreme Court of Tennessee, Workers Compensation Panel
CourtID: tenn
Court Short Name: Tenn.
"""

import re
from datetime import datetime

from lxml.html import HtmlElement

from juriscraper.opinions.united_states.state import tenn
from juriscraper.OpinionSite import OpinionSite


class Site(tenn.Site):
    first_opinion_date = datetime(1996, 3, 14)
    days_interval = 30

    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.tncourts.gov/courts/work-comp/opinions"
        self.section_selector = (
            "views-field views-field-field-opinions-case-brief"
        )

        # docket will always contain WC in the docket number
        self.docket_xpath = "text()[contains(., 'WC')]"

    def get_summary(self, section: HtmlElement) -> str:
        """Get the summary considering some XPath variations

        :param section: the html element containing the case summary
        :return the parsed summary, or an empty string
        """
        try:
            return super().get_summary(section)
        except IndexError:
            pass

        # last non empty floating text in the section
        summary = section.xpath("text()[normalize-space()]")[-1]
        # ensure we didn't pick up a judge field
        if " Judge:" not in summary:
            return summary

        # sometimes each line of the summary is inside a div
        # See 2022 case 'Sonney Summers v. RTR Transportation Services et al.'
        if containers := section.xpath("div/text()"):
            return re.sub(r"\s+", " ", " ".join(containers))

        return ""
