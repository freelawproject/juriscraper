"""
Scraper for Maryland Court of Appeals
CourtID: md
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
"""

from datetime import date, datetime

from juriscraper.OpinionSite import OpinionSite


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
        case_names = []
        for s in self.html.xpath(path):
            case_names.append(s.split('(')[0])
        return case_names

    def _get_judges(self):
        path = '//table//tr/td[4]/font/text()'
        judge_names = []
        for s in self.html.xpath(path):
            judge_names.append(s.split('(')[0])
        return judge_names

    def _get_case_dates(self):
        path = '//table//tr/td[3]/font/text()'
        return [
            datetime.strptime(
                ''.join(date_string.split()),
                '%Y-%m-%d'
            ).date() for date_string in self.html.xpath(path)
        ]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//table//tr/td[1]//text()'
        return list(self.html.xpath(path))

    def _get_west_state_citations(self):
        path = '//table//tr/td[2]/font/text()'
        return list(self.html.xpath(path))
