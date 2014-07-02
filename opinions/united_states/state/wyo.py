"""Scraper for Wyoming Supreme Court
CourtID: wyo
Court Short Name: Wyo.
Author: mlr
2014-07-02: Created new version when court got new website.
"""

from juriscraper.OpinionSite import OpinionSite
from datetime import datetime


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.state.wy.us/Home/Opinions'
        self.court_id = self.__module__

    def _get_case_names(self):
        return list(self.html.xpath("id('tblOpinions')//tr/td[3]/text()"))

    def _get_download_urls(self):
        return [href for href in
                self.html.xpath("id('tblOpinions')//tr/td[1]//@href")]

    def _get_case_dates(self):
        path = "id('tblOpinions')//tr/td[2]/text()"
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        return list(self.html.xpath("id('tblOpinions')//tr/td[5]/text()"))

    def _get_neutral_citations(self):
        return list(self.html.xpath("id('tblOpinions')//tr/td[1]//text()"))

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
