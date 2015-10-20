# Scraper for Minnesota Supreme Court
#CourtID: minn
#Court Short Name: MN
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-03

from datetime import date
import time

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.date_utils import quarter, is_first_month_in_quarter
from lxml import html
import re
from requests.exceptions import HTTPError


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        self.url = 'http://mn.gov/lawlib/archive/sct{short_year}q{quarter}.html'.format(
            short_year=d.strftime("%y"),
            quarter=quarter(d.month)
        )
        # self.url = 'http://mn.gov/lawlib/archive/sct14q3.html'

    def _download(self, request_dict={}):
        """Overrides the download function so that we can catch 404 errors
        silently. This is necessary because these web pages simply do not exist
        for several days at the beginning of each quarter.
        """
        try:
            return super(Site, self)._download()
        except HTTPError, e:
            is_first_days_of_the_quarter = (
                date.today().day <= 15 and
                is_first_month_in_quarter(date.today().month)
            )
            got_404 = (e.response.status_code == 404)
            if got_404 and is_first_days_of_the_quarter:
                # Do nothing; abort the crawler
                self.status = 200
                # We need the body tag here so that xpath works elsewhere.
                html_tree = html.fromstring('<html><body></body></html>')
                return html_tree
            else:
                raise e

    def _get_case_names(self):
        path = '''//ul//li[not(contains(text(), 'ORDER') or
                               contains(text(), 'NO OPINIONS'))]/text()'''

        return list(self.html.xpath(path))

    def _get_download_urls(self):
        path = '''//ul//li[not(contains(text(), 'ORDER') or
                               contains(text(), 'NO OPINIONS'))]//@href'''
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '''//ul//h4/text()'''
        dates = self.html.xpath(path)
        last_date_index = len(dates) - 1
        case_dates = []
        for index, date_element in enumerate(dates):
            if index < last_date_index:
                path_2 = ("//h4[{c}]/following-sibling::li/text()[count("
                          "  .|//h4[{n}]/preceding-sibling::li/text())="
                          "count("
                          "    //h4[{n}]/preceding-sibling::li/text()"
                          ") and not("
                          "    contains(., 'ORDER') or"
                          "    contains(., 'NO OPINIONS')"
                          ")]".format(c=index + 1,
                                      n=index + 2))
            else:
                path_2 = ("//h4[{c}]/following-sibling::li/text()[not("
                          "  contains(., 'ORDER') or"
                          "  contains(., 'NO OPINIONS'))]").format(c=index + 1)
            d = date.fromtimestamp(time.mktime(time.strptime(re.sub(' ', '', str(date_element)), '%B%d,%Y')))
            case_dates.extend([d] * len(self.html.xpath(path_2)))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//ul//li[not(contains(text(), 'ORDER') or
                               contains(text(), 'NO OPINIONS'))]/a/text()'''
        return list(self.html.xpath(path))
