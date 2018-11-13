### BROKEN: Timeout #### Scraper and Back Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2015-10-30

import os
import re
from datetime import date, datetime, timedelta

from dateutil.rrule import DAILY, rrule
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.cookie_utils import normalize_cookies
from juriscraper.lib.network_utils import add_delay
from juriscraper.lib.string_utils import clean_if_py3


class Site(OpinionSite):

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court = 'Appellate+Term,+1st+Dept'
        self.interval = 365
        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            interval=self.interval,
            dtstart=date(2004, 1, 1),
            until=date(2016, 1, 1),
        )]

        self.url = 'http://iapps.courts.state.ny.us/lawReporting/Search'

        self.parameters = {
            'rbOpinionMotion': 'opinion',
            'Pty': '',
            'and_or': 'and',
            'dtStartDate': (date.today() - timedelta(days=30)).strftime("%m/%d/%Y"),
            'dtEndDate': date.today().strftime("%m/%d/%Y"),
            'court': self.court,
            'docket': '',
            'judge': '',
            'slipYear': '',
            'slipNo': '',
            'OffVol': '',
            'OffPage': '',
            'fullText': '',
            'and_or2': 'and',
            'Submit': 'Find',
            'hidden1': '',
            'hidden2': ''

        }

        self.court_id = self.__module__
        self.method = 'POST'
        self.base_path = '//tr[td[5]//a][td[7][contains(., "Opinion")]]'  # Any element with a link on the 5th column
        self.href_js = re.compile(r"funcNewWindow\(\\{0,1}'(.*\.htm)\\{0,1}'\)")
        self.href_standard = re.compile(r"http(s)?://www.nycourts.gov/(.*).htm")
        self.uses_selenium = True

    def _download(self, request_dict={}):
        """
        We use selenium to get the cookies, and then we check if we got the
        correct page. If not we retry for a total of 11 times.
        """
        if self.method == 'LOCAL':
            return super(Site, self)._download(request_dict)

        self.set_cookies()
        logger.info("Using cookies: %s" % self.cookies)
        request_dict.update({'cookies': self.cookies})

        html__ = super(Site, self)._download(request_dict)
        i = 0
        while not html__.xpath('//table') and i < 10:
            add_delay(20, 5)
            html__ = super(Site, self)._download(request_dict)
            i += 1
            logger.info("Got a bad response {} time(s)".format(i))
        return html__

    def _get_case_names(self):
        case_names = []
        for element in self.html.xpath(self.base_path):
            case_names.append(''.join(x.strip() for x in element.xpath('./td[1]//text()')))
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for element in self.html.xpath(self.base_path):
            url = ''
            for href in element.xpath('./td[5]//@href'):
                href = clean_if_py3(href)
                # Check for newer standard href
                match = self.href_standard.match(href)
                if match:
                    url = match.group(0)
                    break
                # Check for presence of legacy JavaScript href
                matches = self.href_js.findall(href)
                if matches:
                    url = url + matches[0]
            if url:
                download_urls.append(url)
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        for element in self.html.xpath("{}/td[2]//text()".format(self.base_path)):
            case_dates.append(datetime.strptime(element.strip(), '%m/%d/%Y'))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for element in self.html.xpath(self.base_path):
            docket_numbers.append(''.join(x.strip() for x in element.xpath('./td[5]//text()')))
        return docket_numbers

    def _get_judges(self):
        judges = []
        for element in self.html.xpath('{}/td[6]'.format(self.base_path, )):
            judges.append(''.join(x.strip() for x in element.xpath('.//text()')))
        return judges

    def _get_neutral_citations(self):
        neutral_citations = []
        for element in self.html.xpath('{}/td[4]'.format(self.base_path, )):
            neutral_citations.append(''.join(x.strip() for x in element.xpath('.//text()')))
        return neutral_citations

    def _download_backwards(self, d):
        self.crawl_date = d
        self.method = 'POST'
        self.parameters = {
            'rbOpinionMotion': 'opinion',
            'Pty': '',
            'and_or': 'and',
            'dtStartDate': (d - timedelta(days=self.interval)).strftime("%m/%d/%Y"),
            'dtEndDate': d.strftime("%m/%d/%Y"),
            'court': self.court,
            'docket': '',
            'judge': '',
            'slipYear': '',
            'slipNo': '',
            'OffVol': '',
            'OffPage': '',
            'fullText': '',
            'and_or2': 'and',
            'Submit': 'Find',
            'hidden1': '',
            'hidden2': ''
        }
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def set_cookies(self):
        """Hit the main URL, and get the cookies so we can use them elsewhere.

        This gets around some of their throttling mechanisms.
        """
        logger.info("Running Selenium browser PhantomJS to get the cookies...")
        add_delay(20, 5)
        driver = webdriver.PhantomJS(
            executable_path='/usr/local/phantomjs/phantomjs',
            service_log_path=os.path.devnull,  # Disable ghostdriver.log
        )

        driver.set_window_size(1920, 1080)
        driver.get(self.url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "dtEndDate"))
        )
        self.cookies = normalize_cookies(driver.get_cookies())
        driver.close()

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath('//partyblock')[0]
        return html.tostring(
            core_element,
            pretty_print=True,
            encoding='unicode'
        )
