"""Scraper for North Carolina Court of Appeals
CourtID: ncctapp
Court Short Name: N.C. Ct. App.
Author: Jon Andersen
History:
    2014-08-04: Created by Jon Andersen
"""

import re

from juriscraper.opinions.united_states.state import nc


class Site(nc.Site):
    court = "coa"
    unpub_date_xpath = (
        "../preceding-sibling::tr/td[contains(text(), 'Rule 30e')]"
    )
    date_xpath = f"{nc.Site.date_xpath} | {unpub_date_xpath}"
    secondary_date_regex = re.compile(
        r"(?P<date>\d[\d \w]+)[\t\xa0\n]+- Rule 30e", flags=re.MULTILINE
    )

    # For `ncctapp` opinions (last available in 2012, as of April 2025)
    state_cite_regex = r"\d+ NC App \d+"
