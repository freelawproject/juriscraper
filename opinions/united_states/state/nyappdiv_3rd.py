# Scraper for New York Appellate Divisions 3rd Dept.
#CourtID: nyappdiv_3rd
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-04
import calendar

from lxml import html
from requests.exceptions import HTTPError

from juriscraper.opinions.united_states.state import ny
import re
import time
from datetime import date


class Site(ny.Site):
    def __init__(self):
        super(Site, self).__init__()
        d = date.today()
        self.url = 'http://decisions.courts.state.ny.us/ad3/CalendarPages/nc{month_nr}{day_nr}{year}.htm'.format(
            month_nr=d.strftime("%m"),
            day_nr=d.strftime("%d"),
            year=d.year
        )
        # self.url = 'http://decisions.courts.state.ny.us/ad3/CalendarPages/nc07032014.htm'
        self.court_id = self.__module__

    def _download(self, request_dict={}):
        """Overrides the download function so that we can catch 404 errors silently.
        This is necessary because these web pages appear only on a Thursday.
        """
        try:
            return super(Site, self)._download()
        except HTTPError, e:
            d = date.today()
            week_day = calendar.weekday(d.year, d.month, d.day)
            got_404 = e.response.status_code == 404
            if got_404 and week_day != 3:
                # Do nothing; abort the crawler
                self.status = 200
                # We need the body tag here so that xpath works elsewhere.
                html_tree = html.fromstring('<html><body></body></html>')
                return html_tree
            else:
                raise e

    def _get_case_names(self):
        path = '''//td[2]//a[contains(./@href, 'Decisions')]/text()'''
        case_names = []
        for text in self.html.xpath(path):
            # Uses a negative look ahead to make sure to get the last occurrence of a docket number.
            text = re.sub('[\t\n]', '', text)
            match_case_name = re.search('(\d{6}(?!.*\d{6})|.{1}-\d{2}-\d{2})\s*(.*)', text)
            case_names.extend([match_case_name.group(2)])
        return case_names

    def _get_download_urls(self):
        path = '''//td[2]//a[contains(./@href, 'Decisions')]/@href'''
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//title/text()'
        case_date = re.search('((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s(?:\d|\d{2}),\s\d{4})',
                              self.html.xpath(path)[0]).group(1)
        case_dates = []
        path_2 = "count(//td[2]//a[contains(./@href, 'Decisions')]/text())"
        d = date.fromtimestamp(time.mktime(time.strptime(case_date, '%b %d, %Y')))
        case_dates.extend([d] * int(self.html.xpath(path_2)))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//td[2]//a[contains(./@href, 'Decisions')]/text()'''
        docket_numbers = []
        for text in self.html.xpath(path):
            match_docket_nr = re.search('(.*\d{6}|.{1}-\d{2}-\d{2})\s*(.*)', text)
            docket_numbers.append(match_docket_nr.group(1))
        return docket_numbers