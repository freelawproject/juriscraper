# Scraper for Texas Supreme Court
# CourtID: tex
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer: mlr
# History:
#  - 2014-07-10: Created by Andrei Chelaru
#  - 2014-11-07: Updated by mlr to account for new website.
#  - 2014-12-09: Updated by mlr to make the date range wider and more thorough.
#  - 2015-08-19: Updated by Andrei Chelaru to add backwards scraping support.
#  - 2015-08-27: Updated by Andrei Chelaru to add explicit waits
from datetime import date, timedelta, datetime

from dateutil.rrule import rrule, YEARLY
import certifi
import os
import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from juriscraper.AbstractSite import logger
from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.cookie_utils import normalize_cookies
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    back_scrape_iterable = [i.date() for i in rrule(
        YEARLY,
        dtstart=date(1981, 1, 1),
        until=date(2016, 1, 1),
    )]

    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.case_date = date.today()
        self.backwards_days = 5

        #self.case_date = date(month=7, year=2014, day=11)
        self.records_nr = 0
        self.courts = {'sc': 0, 'ccrimapp': 1, 'capp_1': 2, 'capp_2': 3, 'capp_3': 4,
                       'capp_4': 5, 'capp_5': 6, 'capp_6': 7, 'capp_7': 8, 'capp_8': 9,
                       'capp_9': 10, 'capp_10': 11, 'capp_11': 12, 'capp_12': 13,
                       'capp_13': 14, 'capp_14': 15}
        self.court_name = 'sc'
        self.url = "http://www.search.txcourts.gov/CaseSearch.aspx?coa=cossup&d=1"

    def _download(self, request_dict={}):
        if self.method == 'LOCAL':
            html_tree_list = [
                super(Site, self)._download(request_dict=request_dict)]
            self.records_nr = len(html_tree_list[0].xpath("//tr[@class='rgRow' or @class='rgAltRow']"))
            return html_tree_list
        else:
            html_pages = []
            logger.info("Running Selenium browser PhantomJS...")
            driver = webdriver.PhantomJS(
                executable_path='/usr/local/phantomjs/phantomjs',
                service_log_path=os.path.devnull,  # Disable ghostdriver.log
            )

            driver.get(self.url)
            # Get a screenshot in testing
            # driver.save_screenshot('out.png')

            # Set the cookie
            self.cookies = normalize_cookies(driver.get_cookies())

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_chkListDocTypes_0"))
            )
            if self.court_name == 'sc':
                # Supreme Court is checked by default, so we don't want to
                # check it again.
                pass
            else:
                search_court_type = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListCourts_{court_nr}".format(
                    court_nr=self.courts[self.court_name])
                )
                search_court_type.click()

            search_opinions = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListDocTypes_0")
            search_opinions.click()

            search_orders = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListDocTypes_1")
            search_orders.click()

            start_date = driver.find_element_by_id("ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput")
            start_date.send_keys((self.case_date - timedelta(days=self.backwards_days)).strftime("%m/%d/%Y"))

            end_date = driver.find_element_by_id("ctl00_ContentPlaceHolder1_dtDocumentTo_dateInput")
            end_date.send_keys(self.case_date.strftime("%m/%d/%Y"))
            # driver.save_screenshot('out2.png')

            submit = driver.find_element_by_id("ctl00_ContentPlaceHolder1_btnSearchText")
            submit.click()

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_grdDocuments"))
            )
            self.status = 200
            # driver.save_screenshot('out3.png')

            nr_of_pages = driver.find_element_by_xpath(
                '//thead//*[contains(concat(" ", normalize-space(@class), " "), " rgInfoPart ")]/strong[2]')
            records_nr = driver.find_element_by_xpath(
                '//thead//*[contains(concat(" ", normalize-space(@class), " "), " rgInfoPart ")]/strong[1]')
            if records_nr:
                self.records_nr = int(records_nr.text)
            if nr_of_pages:
                if nr_of_pages.text == '1':
                    text = driver.page_source
                    driver.quit()

                    html_tree = html.fromstring(text)
                    html_tree.make_links_absolute(self.url)

                    remove_anchors = lambda url: url.split('#')[0]
                    html_tree.rewrite_links(remove_anchors)
                    html_pages.append(html_tree)
                else:
                    text = driver.page_source

                    html_tree = html.fromstring(text)
                    html_tree.make_links_absolute(self.url)

                    remove_anchors = lambda url: url.split('#')[0]
                    html_tree.rewrite_links(remove_anchors)
                    html_pages.append(html_tree)

                    for i in xrange(int(nr_of_pages.text) - 1):
                        next_page = driver.find_element_by_class_name('rgPageNext')
                        next_page.click()
                        driver.implicitly_wait(5)

                        text = driver.page_source

                        html_tree = html.fromstring(text)
                        html_tree.make_links_absolute(self.url)

                        remove_anchors = lambda url: url.split('#')[0]
                        html_tree.rewrite_links(remove_anchors)
                        html_pages.append(html_tree)
            driver.quit()
            return html_pages

    def _get_case_names(self):
        def fetcher(url):
            if self.method == 'LOCAL':
                return "No case names fetched during tests."
            else:
                r = requests.get(
                    url,
                    allow_redirects=True,
                    headers={'User-Agent': 'Juriscraper'},
                    verify=certifi.where(),
                )
                r.raise_for_status()

                html_tree = html.fromstring(r.text)
                html_tree.make_links_absolute(self.url)
                plaintiff = html_tree.xpath(
                    "//text()[contains(., 'Style:')]/ancestor::div[@class='span2']/following-sibling::div/text()"
                )[0]
                defendant = html_tree.xpath(
                    "//text()[contains(., 'v.:')]/ancestor::div[@class='span2']/following-sibling::div/text()"
                )[0]

                if defendant.strip():
                    # If there's a defendant
                    return titlecase('%s v. %s' % (plaintiff, defendant))
                else:
                    return titlecase(plaintiff)

        seed_urls = []
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[5]//@href".format(
                    n=record
                )
                seed_urls.append(html_tree.xpath(path)[0])
        if seed_urls:
            return DeferringList(seed=seed_urls, fetcher=fetcher)
        else:
            return []

    def _get_case_dates(self):
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[2]/text()".format(
                    n=record
                )
                yield datetime.strptime(html_tree.xpath(path)[0], '%m/%d/%Y')

    def _get_precedential_statuses(self):
        return ['Published'] * self.records_nr

    def _get_download_urls(self):
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[4]//@href".format(
                    n=record
                )
                yield html_tree.xpath(path)[0]

    def _get_docket_numbers(self):
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[5]//text()[contains(., '-')]".format(
                    n=record
                )
                yield html_tree.xpath(path)[0]

    @staticmethod
    def _get_opinion_count(html_tree):
        return int(html_tree.xpath("count(id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00')"
                                   "//tr[contains(., 'Opinion') or contains(., 'Order')])"))

    def _download_backwards(self, d):
        self.crawl_date = d
        logger.info("Running backscraper with date: %s" % d)
        self.case_date = d
        self.backwards_days = 365
