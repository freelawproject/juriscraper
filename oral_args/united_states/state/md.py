"""Scraper for Maryland Supreme Court Oral Argument Audio
CourtID: md
Court Short Name: Md.
Author: Brian W. Carver
Reviewer: mlr
History:
  2014-10-17: Created by Brian Carver
  2014-10-20: Some tweaks by mlr
"""

from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.courts.state.md.us/coappeals/webcasts/webcastarchive.html'

    def _get_download_urls(self):
        path = "//table//tr/td[2]/strong/a/@href[not(contains(., 'baradmissions'))]"
        # This works because they usually link on docket number, but there's
        # one page where the audio must have been long and they link instead
        # on 'Part 1' and 'Part 2'. That sort of irregularity is not handled.
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        path = "//table/tr[not(contains(.//@href, 'baradmission'))]/td[1]/text()"
        for s in self.html.xpath(path):
            for date_format in ('%m-%d-%Y', '%m-%d-%y'):
                try:
                    d = datetime.strptime(s, date_format).date()
                except ValueError:
                    continue
                dates.append(d)
        return dates

    def _get_case_names(self):
        # To avoid the "Title" rows we find the siblings of the rows with links.
        path = '//table//tr/td[2]/strong/a/../../following-sibling::td/strong/text()'
        cases = []
        for case in self.html.xpath(path):
            if case.strip():
                cases.append(case)
        return cases

    def _get_docket_numbers(self):
        # This works except for on the page where one of the recordings was
        # split into Part 1 and Part 2.
        path = "//table//tr/td[2]/strong/a/text()[not(contains(., 'Admissions'))]"
        return list(self.html.xpath(path))
