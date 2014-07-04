# Scraper for New York Appellate Divisions 4th Dept.
#CourtID: nyappdiv_4th
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
        self.url = 'http://www.nycourts.gov/courts/ad4/Clerk/Decisions/{year}/{month_nr}-{day_nr}-{year_sh}/alpha-{month_nr}-{day_nr}-{year_sh}.html'.format(
            month_nr=d.strftime("%m"),
            month_nr=d.strftime("%y"),
            day_nr=d.strftime("%d"),
            year=d.year
        )
        # self.url = 'http://www.nycourts.gov/courts/ad4/Clerk/Decisions/2014/07-03-14/alpha-07-03-14.html'
        self.court_id = self.__module__

    def _download(self, request_dict={}):
        """Overrides the download function so that we can catch 404 errors silently.
        This is necessary because these web pages appear randomly.
        """
        try:
            return super(Site, self)._download()
        except HTTPError, e:
            got_404 = e.response.status_code == 404
            if got_404:
                # Do nothing; abort the crawler
                self.status = 200
                # We need the body tag here so that xpath works elsewhere.
                html_tree = html.fromstring('<html><body></body></html>')
                return html_tree
            else:
                raise e

    def _get_case_names(self):
        path = '''//tr[count(td)=4][contains(.//@href, ./td[2]/text())]/td[1]//text()'''
        return list(self.html.xpath(path))

    def _get_download_urls(self):
        path = '''//tr[count(td)=4][contains(.//@href, ./td[2]/text())]/td[1]//@href'''
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "id('page_content')//text()[contains(., 'Decisions')]"

        case_date = re.search('((?:January|February|March|April|May|June|July|August|September|October|November|December).(?:\d|\d{2}),.\d{4})',
                              re.sub(r'\xa0', ' ', self.html.xpath(path)[0])).group(1)
        case_dates = []
        path_2 = "count(//tr[count(td)=4][contains(.//@href, ./td[2]/text())])"
        d = date.fromtimestamp(time.mktime(time.strptime(case_date, '%B %d, %Y')))
        case_dates.extend([d] * int(self.html.xpath(path_2)))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//tr[count(td)=4][contains(.//@href, ./td[2]/text())]/td[3]/text()'''
        return list(self.html.xpath(path))