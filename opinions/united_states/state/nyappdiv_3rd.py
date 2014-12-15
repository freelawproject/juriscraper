# Scraper for New York Appellate Divisions 3rd Dept.
# CourtID: nyappdiv_3rd
# Court Short Name: NY
# History:
#   2014-07-04: Created by Andrei Chelaru
#   2014-07-05: Reviewed by mlr
#   2014-12-15: Updated to fix regex and insanity errors.

import re
from datetime import date

from dateutil.relativedelta import relativedelta, TH
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        # Last thursday, this court publishes weekly
        self.crawl_date = date.today() + relativedelta(weekday=TH(-1))
        self.url = 'http://decisions.courts.state.ny.us/ad3/CalendarPages/nc{month_nr}{day_nr}{year}.htm'.format(
            month_nr=self.crawl_date.strftime("%m"),
            day_nr=self.crawl_date.strftime("%d"),
            year=self.crawl_date.year
        )
        # self.url = 'http://decisions.courts.state.ny.us/ad3/CalendarPages/nc07032014.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '''//td[2]//a[contains(./@href, 'Decisions')]/text()'''
        case_names = []
        for text in self.html.xpath(path):
            # Uses a negative look ahead (assert that something is not followed
            # by something else) to make sure to get the last occurrence of a
            # docket number.
            text = ' '.join(text.split())
            if text.strip():
                match_case_name = re.search('(\d{6}(?!.*\d{6})|.-\d{2}-\d{2})\s*(.*)', text)
                case_names.append(match_case_name.group(2))
        return case_names

    def _get_download_urls(self):
        path = '''//td[2]//a[contains(./@href, 'Decisions')]/@href'''
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "count(//td[2]//a[contains(./@href, 'Decisions')]/@href)"
        return [self.crawl_date] * int(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//td[2]//a[contains(./@href, 'Decisions')]/text()'''
        docket_numbers = []
        for text in self.html.xpath(path):
            if text.strip():
                match_docket_nr = re.search('(.*\d{6}|.-\d{2}-\d{2})\s*(.*)', text)
                docket_numbers.append(match_docket_nr.group(1))
        return docket_numbers
