"""
Scraper for Maryland Court of Appeals
CourtID: md
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
Court Support: webmaster@mdcourts.gov, mdlaw.library@mdcourts.gov
"""

from datetime import date

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.mdcourts.gov/cgi-bin/indexlist.pl?court=coa&year={current_year}&order=bydate&submit=Submit".format(
            current_year=date.today().year
        )
        self.court_id = self.__module__

    def _get_download_urls(self):
        path = "//table//tr/td[1]//@href[contains(.,'pdf')]"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "//table//tr/td[5]/font/text()"
        return [s.split("(")[0] for s in self.html.xpath(path)]

    def _get_judges(self):
        path = "//table//tr/td[4]/font/text()"
        return [s.split("(")[0] for s in self.html.xpath(path)]

    def _get_case_dates(self):
        dates = []
        path = "//table//tr/td[3]/font/text()"
        for date_string in self.html.xpath(path):
            # Logic in line below handles use case where date cell shows text
            # like '2019-11-14 corrected 2019-11-19' instead of '2019-11-19'.
            # See: mdctspecapp_example_2.html
            date_string = date_string.split()[-1]
            date_ = convert_date_string(date_string)
            dates.append(date_)
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "//table//tr/td[1]//text()"
        return list(self.html.xpath(path))

    def _get_west_state_citations(self):
        path = "//table//tr/td[2]/font/text()"
        cites = []
        for c in list(self.html.xpath(path)):
            if c == ".":
                cites.append("")
            else:
                cites.append(c)
        return cites
