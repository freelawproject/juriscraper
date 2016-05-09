"""Scraper for Missouri
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
"""

from datetime import date
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = 'https://www.courts.mo.gov/page.jsp?id=12086&dist=Opinions Supreme&date=all&year=%s#all' % today.year

    def _get_download_urls(self):
        # the case overview/summary links have 'b' element children; exclude those 'b's to get actual case links
        path = '//div[@id="info"]/div/form/table/tr/td/table/tr/td/*[not(b)]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        return list(self.html.xpath('//div[@id="info"]/div/form/table/tr/td/table/tr/td/a/text()'))

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
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = ('//div[@id="info"]/div/form/table/tr/td/table/tr/td/*[('
                    'starts-with(text(), "SD") or '
                    'starts-with(text(), "WD") or '
                    'starts-with(text(), "ED") or '
                    'starts-with(text(), "SC")'
                ') and contains(text(), ":")]/text()')
        docket_numbers = []
        for t in self.html.xpath(path):
            docket_numbers.append(t.strip(':'))
        return docket_numbers

    def _get_judges(self):
        authors = []
        cases = self.html.xpath('//div[@id="info"]/div/form/table/tr/td/table/*')
        for case in cases:
            sub_path = './/*[starts-with(text(), "Author:")]'  # Any sub-node with text() starting with "Author"
            if case.xpath(sub_path):
                authors.extend(case.xpath('.//*[starts-with(text(), "Author:")]/following-sibling::text()[1]'))
            else:
                authors.extend([' '])
        return authors

    def _get_dispositions(self):
        votes = []
        cases = self.html.xpath('//div[@id="info"]/div/form/table/tr/td/table/*')
        for case in cases:
            sub_path = './/*[starts-with(text(), "Vote:")]'  # Any subnode with text() starting with "Vote"
            if case.xpath(sub_path):
                votes.extend(case.xpath('.//*[starts-with(text(), "Vote:")]/following-sibling::text()[1]'))
            else:
                votes.extend([' '])
        return votes
