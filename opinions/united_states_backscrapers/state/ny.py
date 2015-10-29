"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2015-10-27  Created by Andrei Chelaru
"""
from juriscraper.lib.cookie_utils import normalize_cookies
import os
import re
from datetime import date, datetime, timedelta
from juriscraper.OpinionSite import OpinionSite
from dateutil.rrule import rrule, DAILY
from juriscraper.AbstractSite import logger
from lxml import html
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from lib.html_utils import add_delay


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.crawl_date = date.today()
        self.interval = 200
        # self.url = 'http://iapps.courts.state.ny.us/lawReporting/Search'
        self.url = 'http://iapps.courts.state.ny.us/lawReporting/CourtOfAppealsSearch?searchType=opinion&dtStartDate=10/01/2015&dtEndDate=10/27/2015&Submit=true'
        self.court_id = self.__module__
        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            interval=self.interval,
            dtstart=date(2005, 1, 1),
            # dtstart=date(2005, 1, 1),
            until=date(2016, 1, 1),
        )]
        self.method = 'POST'
        self.base_path = '//tr[td[4]//a][td[6][contains(., "Opinion")]]'  # Any element with a link on the 5th column
        self.download_regex = re.compile("funcNewWindow\('(.*\.htm)'\)")
        self.court = 'Court of Appeals'
        self.parameters = {}
        self.use_sessions = True

    # def _download(self, request_dict={}):
    #     if self.method == 'LOCAL':
    #         html_tree_list = [
    #             super(Site, self)._download(request_dict=request_dict)]
    #         return html_tree_list
    #     else:
    #         logger.info("Running Selenium browser PhantomJS...")
    #         driver = webdriver.PhantomJS(
    #             executable_path='/usr/local/phantomjs/phantomjs',
    #             service_log_path=os.path.devnull,  # Disable ghostdriver.log
    #         )
    #
    #         driver.set_window_size(1920, 1080)
    #         driver.get(self.url)
    #
    #         WebDriverWait(driver, 30).until(
    #             EC.presence_of_element_located((By.NAME, "dtEndDate"))
    #         )
    #         # Get a screenshot in testing
    #         # driver.save_screenshot('out.png')
    #
    #         search_court_type = Select(driver.find_element_by_xpath("//select[@name='court']"))
    #         search_court_type.select_by_visible_text(self.court)
    #
    #         search_opinions = driver.find_element_by_xpath("//input[@value='opinion']")
    #         ActionChains(driver).click(search_opinions).perform()
    #
    #         start_date = driver.find_element_by_id("dtStartDate")
    #         sd = (self.crawl_date - timedelta(days=self.interval)).strftime("%m/%d/%Y")
    #         driver.execute_script("arguments[0].value = '{}';".format(sd), start_date)
    #         # driver.save_screenshot('out12.png')
    #
    #         end_date = driver.find_element_by_id("dtEndDate")
    #         ed = self.crawl_date.strftime("%m/%d/%Y")
    #         driver.execute_script("arguments[0].value = '{}';".format(ed), end_date)
    #         # driver.save_screenshot('out2.png')
    #
    #         submit = driver.find_element_by_name("Submit")
    #         ActionChains(driver).click(submit).perform()
    #
    #         WebDriverWait(driver, 60).until(
    #             EC.presence_of_element_located((By.NAME, "again"))
    #         )
    #         self.status = 200
    #         # driver.save_screenshot('out3.png')
    #
    #         text = driver.page_source
    #         driver.quit()
    #
    #         html_tree = html.fromstring(text)
    #         html_tree.make_links_absolute(self.url)
    #
    #         remove_anchors = lambda url: url.split('#')[0]
    #         html_tree.rewrite_links(remove_anchors)
    #         return html_tree

    def _get_case_names(self):
        print(html.tostring(self.html))
        case_names = []
        for element in self.html.xpath(self.base_path):
            logger.info('1')
            case_names.append(''.join(x.strip() for x in element.xpath('./td[1]//text()')))
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for element in self.html.xpath(self.base_path):
            download_urls.append(''.join(self.download_regex.findall(x)[0] for x in element.xpath('./td[4]//@href')))
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
            docket_numbers.append(''.join(x.strip() for x in element.xpath('./td[4]//text()')))
        return docket_numbers

    def _get_judges(self):
        judges = []
        for element in self.html.xpath('{}/td[5]'.format(self.base_path, )):
            judges.append(''.join(x.strip() for x in element.xpath('.//text()')))
        return judges

    def _get_neutral_citations(self):
        neutral_citations = []
        for element in self.html.xpath('{}/td[3]'.format(self.base_path, )):
            neutral_citations.append(''.join(x.strip() for x in element.xpath('.//text()')))
        return neutral_citations

    def _download_backwards(self, d):
        add_delay(20, 5)
        self.crawl_date = d
        self.url = 'http://iapps.courts.state.ny.us/lawReporting/CourtOfAppealsSearch'
        # self.url = 'http://iapps.courts.state.ny.us/lawReporting/CourtOfAppealsSearch?rbOpinionMotion=opinion&Pty=&and_or=and&dtStartDate={}&dtEndDate={}&docket=&judge=&slipYear=&slipNo=&OffVol=&OffPage=&fullText=&and_or2=and&Submit=Find&hidden1=&hidden2='.format(
        #     (d - timedelta(days=self.interval)).strftime("%m/%d/%Y"),
        #     d.strftime("%m/%d/%Y")
        # )
        self.method = 'POST'
        self.parameters = {
            'rbOpinionMotion': 'opinion',
            'Pty': '',
            'and_or': 'and',
            'dtStartDate': (d - timedelta(days=self.interval)).strftime("%m/%d/%Y"),
            'dtEndDate': d.strftime("%m/%d/%Y"),
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
        cookies = self.get_cookies()
        logger.info(str(cookies))
        self.html = self._download(request_dict={'cookies': cookies})

        i = 0
        while not self.html.xpath('//table') and i < 10:
            add_delay(20, 5)
            self.html = self._download(request_dict={'cookies': cookies})
            i += 1
            logger.info("Bad responce {}".format(i))

        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def get_cookies(self, new=False):
        """
        if new is True it will open the self.url using selenium and return the cookies
        else it returns self.cookies
        """

        # if not self.cookies or new:
        logger.info("Running Selenium browser PhantomJS to get the cookies...")
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

        return self.cookies
