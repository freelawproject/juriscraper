# Scraper for Texas Supreme Court
# CourtID: tex
#Court Short Name: TX
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-10


from datetime import date
from lxml import html
import requests
from selenium import webdriver

from juriscraper.AbstractSite import logger
from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.case_date = date.today()
        #self.case_date = date(month=7, year=2014, day=11)
        self.records_nr = 0
        self.courts = {'sc': 0, 'ccrimapp': 1, 'capp_1': 2, 'capp_2': 3, 'capp_3': 4,
                       'capp_4': 5, 'capp_5': 6, 'capp_6': 7, 'capp_7': 8, 'capp_8': 9,
                       'capp_9': 10, 'capp_10': 11, 'capp_11': 12, 'capp_12': 13,
                       'capp_13': 14, 'capp_14': 15}
        self.court_name = 'sc'
        self.url = "http://www.search.txcourts.gov/CaseSearch.aspx?coa=cossup&d=1"

    def _download(self, request_dict={}):
        logger.info("Running Selenium browser PhantomJS...")
        driver = webdriver.PhantomJS(executable_path='/usr/local/phantomjs/phantomjs')
        driver.get(self.url)

        # Set the cookie
        self._cookies = driver.get_cookies()

        driver.implicitly_wait(10)
        search_court_type = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListCourts_{court_nr}".format(
            court_nr=self.courts[self.court_name])
        )
        search_court_type.click()

        search_opinions = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListDocTypes_0")
        search_opinions.click()

        search_orders = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListDocTypes_1")
        search_orders.click()

        start_date = driver.find_element_by_id("ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput")
        start_date.send_keys(self.case_date.strftime("%m/%d/%Y"))

        end_date = driver.find_element_by_id("ctl00_ContentPlaceHolder1_dtDocumentTo_dateInput")
        end_date.send_keys(self.case_date.strftime("%m/%d/%Y"))

        submit = driver.find_element_by_id("ctl00_ContentPlaceHolder1_btnSearchText")
        submit.click()
        driver.implicitly_wait(20)

        nr_of_pages = driver.find_element_by_xpath(
            '//thead//*[contains(concat(" ", normalize-space(@class), " "), " rgInfoPart ")]/strong[2]')
        records_nr = driver.find_element_by_xpath(
            '//thead//*[contains(concat(" ", normalize-space(@class), " "), " rgInfoPart ")]/strong[1]')
        if records_nr:
            self.records_nr = int(records_nr.text)
        if nr_of_pages:
            if nr_of_pages.text == '1':
                text = driver.page_source
                driver.close()

                html_tree = html.fromstring(text)
                html_tree.make_links_absolute(self.url)

                remove_anchors = lambda url: url.split('#')[0]
                html_tree.rewrite_links(remove_anchors)
                return html_tree
            else:
                html_pages = []
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
                driver.close()
                return html_pages

    def _get_case_names(self):
        def fetcher(url):
            r = requests.get(url,
                             allow_redirects=False,
                             headers={'User-Agent': 'Juriscraper'})
            r.raise_for_status()

            html_tree = html.fromstring(r.text)
            html_tree.make_links_absolute(self.url)
            plaintiff = html_tree.xpath("//text()[contains(., 'Style')]/ancestor::tr[1]/td[2]/text()")[0]
            defendant = html_tree.xpath("//text()[contains(., 'v.:')]/ancestor::tr[1]/td[2]/text()")[0]

            if defendant.strip():
                # If there's a defendant
                return titlecase('%s v. %s' % (plaintiff, defendant))
            else:
                return titlecase(plaintiff)

        seed_urls = []
        if isinstance(self.html, list):
            for html_tree in self.html:
                page_records_count = self._get_opinion_count(html_tree)
                for record in xrange(page_records_count):
                    path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[5]//@href".format(n=record)
                    seed_urls.append(html_tree.xpath(path)[0])
        else:
            seed_urls = map(self._return_seed_url, range(self.records_nr))
        if seed_urls:
            return DeferringList(seed=seed_urls, fetcher=fetcher)
        else:
            return []

    def _get_case_dates(self):
        return [self.case_date] * self.records_nr

    def _get_precedential_statuses(self):
        return ['Published'] * self.records_nr

    def _get_download_urls(self):
        if isinstance(self.html, list):
            download_urls = []
            for html_tree in self.html:
                page_records_count = self._get_opinion_count(html_tree)
                for record in xrange(page_records_count):
                    path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[4]//@href".format(n=record)
                    download_urls.append(html_tree.xpath(path)[0])
            return download_urls
        else:
            return map(self._return_download_url, range(self.records_nr))

    def _get_docket_numbers(self):
        if isinstance(self.html, list):
            docket_numbers = []
            for html_tree in self.html:
                page_records_count = self._get_opinion_count(html_tree)
                for record in xrange(page_records_count):
                    path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')" \
                           "/td[5]//text()[contains(., '-')]".format(n=record)
                    docket_numbers.append(html_tree.xpath(path)[0])
            return docket_numbers
        else:
            return map(self._return_docket_number, range(self.records_nr))

    def _return_docket_number(self, record):
        path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[5]//text()[contains(., '-')]".format(
            n=record
        )
        return self.html.xpath(path)[0]

    def _return_download_url(self, record):
        path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[4]//@href".format(n=record)
        return self.html.xpath(path)[0]

    def _return_seed_url(self, record):
        path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[5]//@href".format(n=record)
        return self.html.xpath(path)[0]

    @staticmethod
    def _get_opinion_count(html_tree):
        return int(html_tree.xpath("count(id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00')"
                                   "//tr[contains(., 'Opinion') or contains(., 'Order')])"))

    def _get_cookies(self):
        if self.status is None:
            # Run the downloader if it hasn't been run already
            self.html = self._download()
        return self._cookies