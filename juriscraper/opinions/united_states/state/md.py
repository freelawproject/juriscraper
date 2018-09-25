"""
Scraper for Maryland Court of Appeals
CourtID: md
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
Court Support: webmaster@mdcourts.gov, mdlaw.library@mdcourts.gov
"""

from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.mdcourts.gov/cgi-bin/indexlist.pl?court=coa&year={current_year}&order=bydate&submit=Submit'.format(current_year=date.today().year)
        self.court_id = self.__module__

    def _get_download_urls(self):
        path = "//table//tr/td[1]//@href[contains(.,'pdf')]"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//table//tr/td[5]/font/text()'
        return [s.split('(')[0] for s in self.html.xpath(path)]

    def _get_judges(self):
        path = '//table//tr/td[4]/font/text()'
        return [s.split('(')[0] for s in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//table//tr/td[3]/font/text()'
        return [convert_date_string(date_string) for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//table//tr/td[1]//text()'
        return list(self.html.xpath(path))

    def _get_west_state_citations(self):
        path = '//table//tr/td[2]/font/text()'
        cites = []
        for c in list(self.html.xpath(path)):
            if c == '.':
                cites.append('')
            else:
                cites.append(c)
        return cites
