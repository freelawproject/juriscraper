# Scraper for New York Appellate Divisions 4th Dept.
#CourtID: nyappdiv_4th
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-04

from datetime import date

from lxml import html
from requests.exceptions import HTTPError
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.crawl_date = date.today()
        # self.url = 'http://www.nycourts.gov/courts/ad4/Clerk/Decisions/2014/07-03-14/alpha-07-03-14.html'
        self.url = 'http://www.nycourts.gov/courts/ad4/Clerk/Decisions/{year_long}/{month}-{day}-{year_short}/alpha-{month}-{day}-{year_short}.html'.format(
            month=self.crawl_date.strftime("%m"),
            year_short=self.crawl_date.strftime("%y"),
            day=self.crawl_date.strftime("%d"),
            year_long=self.crawl_date.year
        )
        self.court_id = self.__module__

    def _download(self, request_dict={}):
        """Overrides the download function so that we can catch 404 errors
        silently.

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
        path_2 = "count(//tr[count(td)=4][contains(.//@href, ./td[2]/text())])"
        return [self.crawl_date] * int(self.html.xpath(path_2))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//tr[count(td)=4][contains(.//@href, ./td[2]/text())]/td[3]/text()'''
        return list(self.html.xpath(path))
