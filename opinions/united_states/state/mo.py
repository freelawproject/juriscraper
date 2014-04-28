"""Scraper for Missouri
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
"""

# import re
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite
# from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):

    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'https://www.courts.mo.gov/page.jsp?id=12086&dist=Opinions&date=all&year=2014#all'

    def _get_download_urls(self):
        # the case overview/summary links have 'b' element children; exclude those 'b's to get actual case links
        path = '//*[@id="info"]/div/form/table/tr/td/table/tr/td/*[not(b)]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//*[@id="info"]/div/form/table/tr/td/table/tr/td/a/text()'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s)
        return case_names

    def _get_case_dates(self):
        cases_grouped_by_date = self.html.xpath('//div/form/table/tr')
        def case_count_by_date(lst):
            for c in lst:
                if len(c.xpath('.//td/child::table')): # only add ones that aren't zero/empty list
                    yield len(c.xpath('.//td/child::table')), c.xpath('.//td/input/@value')

        case_generator = case_count_by_date(cases_grouped_by_date)

        cases_that_day = []
        for ct, dt in case_generator:
            for n in range(0, ct):
                cases_that_day.extend(dt)

        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in cases_that_day]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//path/to/text/text()'):
            statuses.append('Published')
        return statuses

    def _get_docket_numbers(self):

        docket_numbers = self.html.xpath('//*[@id="info"]/div/form/table/tr/td/table/tr/td/*[(starts-with(text(),"SD") or starts-with(text(), "WD") or starts-with(text(), "ED") or starts-with(text(), "SC")) and contains(text(), ":")]/text()')
        return docket_numbers

    def _get_judges(self):
        authors = []
        cases = self.html.xpath('body/div/div/div/div/div/div/form/table/tr/td/table/*')
        actual_authors = self.html.xpath('//*[@id="info"]/div/form/table/tr/td/table/tr/td/*[starts-with(text(), "Author:")]/following-sibling::text()[1]')
        for case in cases:
            if case.xpath('.//*[starts-with(text(), "Author:")]'):
                authors.extend(case.xpath('.//*[starts-with(text(), "Author:")]/following-sibling::text()[1]'))
            else:
                authors.extend([' '])
        return authors


    def _get_dispositions(self):
        votes = []
        cases = self.html.xpath('body/div/div/div/div/div/div/form/table/tr/td/table/*')
        actual_votes = self.html.xpath('//*[@id="info"]/div/form/table/tr/td/table/tr/td/*[starts-with(text(), "Vote:")]/following-sibling::text()[1]')
        for case in cases:
            if case.xpath('.//*[starts-with(text(), "Vote:")]'):
                votes.extend(case.xpath('.//*[starts-with(text(), "Vote:")]/following-sibling::text()[1]'))
            else:
                votes.extend([' '])
        return votes

    """
      Optional method used for downloading multiple pages of a court site.
    """
    def _download_backwards(self, date_str):
        """ This is a simple method that can be used to generate Site objects
            that can be used to paginate through a court's entire website.

            This method is usually called by a backscraper caller (see the
            one in CourtListener/alert/scrapers for details), and typically
            modifies aspects of the Site object's attributes such as Site.url.

            A simple example has been provided below. The idea is that the
            caller runs this method with a different variable on each iteration.
            That variable is often a date that is getting iterated or is simply
            a index (i), that we iterate upon.

            This can also be used to hold notes useful to future backscraper
            development.
        """
        self.url = 'http://example.com/new/url/%s' % date_str
        self.html = self._download()
