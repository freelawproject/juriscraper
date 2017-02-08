from datetime import datetime, timedelta, date

import os
from lxml import html
from dateutil.rrule import DAILY, rrule
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.cookie_utils import normalize_cookies


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.ca5.uscourts.gov/electronic-case-filing/case-information/current-opinions'
        self.court_id = self.__module__
        self.interval = 5
        self.case_date = datetime.today()
        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            interval=self.interval,  # Every interval days
            dtstart=date(1992, 5, 14),
            until=date(2015, 1, 1),
        )]
        self.uses_selenium = True

    def _download(self, request_dict={}):
        if self.method == 'LOCAL':
            html_tree_list = [
                super(Site, self)._download(request_dict=request_dict)]
            self.records_nr = len(html_tree_list[0].xpath(
                "//tr[contains(concat('', @id, ''), 'ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00')]")
            )
            return html_tree_list
        else:
            logger.info("Running Selenium browser PhantomJS...")
            driver = webdriver.PhantomJS(
                executable_path='/usr/local/phantomjs/phantomjs',
                service_log_path=os.path.devnull,  # Disable ghostdriver.log
            )

            driver.set_window_size(1920, 1080)
            driver.get(self.url)
            # Get a screenshot in testing
            # driver.save_screenshot('out.png')

            # Set the cookie
            self.cookies = normalize_cookies(driver.get_cookies())
            # driver.save_screenshot('screenie.png')
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.ID, "ctl00_Body_C010_ctl00_ctl00_endDate_dateInput")
                )
            )

            start_date = driver.find_element_by_id("ctl00_Body_C010_ctl00_ctl00_startDate_dateInput")
            start_date.send_keys((self.case_date - timedelta(days=self.interval)).strftime("%m/%d/%Y"))

            end_date = driver.find_element_by_id("ctl00_Body_C010_ctl00_ctl00_endDate_dateInput")
            end_date.send_keys(self.case_date.strftime("%m/%d/%Y"))
            #driver.save_screenshot('%s.png' % self.case_date)

            submit = driver.find_element_by_id("Body_C010_ctl00_ctl00_btnSearch")
            submit.click()

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00"))
            )
            self.status = 200
            # driver.save_screenshot('%s.png' % self.case_date)

            try:
                nr_of_pages = driver.find_element_by_xpath(
                    '//div[contains(concat(" ", @class, " "), "rgInfoPart")]/strong[2]')
                records_nr = driver.find_element_by_xpath(
                    '//div[contains(concat(" ", @class, " "), "rgInfoPart")]/strong[1]')
                self.records_nr = int(records_nr.text)
                nr_of_pages = int(nr_of_pages.text)
            except NoSuchElementException:
                try:
                    self.records_nr = len(driver.find_elements_by_xpath(
                        "//tr[contains(concat('', @id, ''), 'ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00')]")
                    )
                    nr_of_pages = 1
                except NoSuchElementException:
                    driver.quit()
                    return []
            html_pages = []
            logger.info("records: {}, pages: {}".format(self.records_nr, nr_of_pages))
            if nr_of_pages == 1:
                text = driver.page_source
                driver.quit()

                html_tree = html.fromstring(text)
                html_tree.make_links_absolute(self.url)

                remove_anchors = lambda url: url.split('#')[0]
                html_tree.rewrite_links(remove_anchors)
                html_pages.append(html_tree)
            else:
                logger.info("Paginating through %s pages of results." %
                            nr_of_pages)
                logger.info("  Getting page 1")
                text = driver.page_source

                html_tree = html.fromstring(text)
                html_tree.make_links_absolute(self.url)

                remove_anchors = lambda url: url.split('#')[0]
                html_tree.rewrite_links(remove_anchors)
                html_pages.append(html_tree)

                for i in range(nr_of_pages - 1):
                    logger.info("  Getting page %s" % (i + 2))
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
        case_names = []
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00__{n}')/td[4]/text()".format(
                    n=record
                )
                case_names.append(html_tree.xpath(path)[0])
        return case_names

    def _get_download_urls(self):
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00__{n}')/td[2]/a/@href".format(
                    n=record
                )
                yield html_tree.xpath(path)[0]

    def _get_case_dates(self):
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00__{n}')/td[3]/text()".format(
                    n=record
                )
                yield datetime.strptime(html_tree.xpath(path)[0], '%m/%d/%Y')

    def _get_docket_numbers(self):
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00__{n}')/td[2]/a/text()".format(
                    n=record
                )
                yield html_tree.xpath(path)[0]

    def _get_precedential_statuses(self):
        for html_tree in self.html:
            page_records_count = self._get_opinion_count(html_tree)
            for record in range(page_records_count):
                path = "id('ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00__{n}')/td[5]/text()".format(
                    n=record
                )
                yield 'Unpublished' if 'unpub' in html_tree.xpath(path)[0] else 'Published'

    @staticmethod
    def _get_opinion_count(html_tree):
        return int(html_tree.xpath(
            "count(//tr[contains(concat('', @id, ''), 'ctl00_Body_C010_ctl00_ctl00_radGridOpinions_ctl00')])")
        )

    def _download_backwards(self, d):
        self.case_date = d
        logger.info("Running backscraper with date range: %s to %s" % (
            self.case_date - timedelta(days=self.interval),
            self.case_date,
        ))
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
