"""Scraper for Maryland Supreme Court Oral Argument Audio
CourtID: md
Court Short Name: Md.
Author: Brian W. Carver
Date created: 2014-10-17
"""

from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.courts.state.md.us/coappeals/webcasts/webcastarchive.html'

    def _get_download_urls(self):
        # This excludes the recordings of "Bar Admissions" which aren't cases.
        path = "//table//tr/td[2]/strong/a/@href[not(contains(., 'baradmissions'))]"
        # This works because they usually link on docket number, but there's
        # one page where the audio must have been long and they link instead
        # on 'Part 1' and 'Part 2'. That sort of irregularity is not handled.
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        # We have to exclude the Bar Admissions lines.
        dates = []
        rowpath = '//table/tr'
        urlpath = './td[2]/strong/a/@href'
        datepath = './td[1]/text()'
        for row in self.html.xpath(rowpath):
            urls = row.xpath(urlpath)
            for url in urls:
                if 'baradmissions' in url:
                    continue
                else:
                    # The site is not consistent re date formats. We try a few:
                    for date_string in row.xpath(datepath):
                        try:
                            date_obj = datetime.strptime(date_string, '%m-%d-%Y').date()
                        except ValueError:
                            date_obj = datetime.strptime(date_string, '%m-%d-%y').date()
                        dates.append(date_obj)
        return dates

    def _get_case_names(self):
        # To avoid the "Title" rows we find the siblings of the rows with links.
        path = '//table//tr/td[2]/strong/a/../../following-sibling::td/strong/text()'
        cases = []
        for case in self.html.xpath(path):
            # Many results contain only a newline and must be discarded
            if case.strip() is '':
                continue
            else:
                cases.append(case)
        return cases

    def _get_docket_numbers(self):
        # This works except for on the page where one of the recordings was
        # split into Part 1 and Part 2.
        path = "//table//tr/td[2]/strong/a/text()[not(contains(., 'Admissions'))]"
        return list(self.html.xpath(path))
