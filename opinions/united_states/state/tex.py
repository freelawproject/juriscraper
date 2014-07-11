# Scraper for Texas Supreme Court
# CourtID: tex
#Court Short Name: TX
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-10


from datetime import date
from lxml import html
from selenium import webdriver

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.case_date = date.today()
        self.records_nr = 0
        self.courts = {'sc': 0, 'ccrimapp': 1, 'capp_1': 2, 'capp_2': 3, 'capp_3': 4,
                       'capp_4': 5, 'capp_5': 6, 'capp_6': 7, 'capp_7': 8, 'capp_8': 9,
                       'capp_9': 10, 'capp_10': 11, 'capp_11': 12, 'capp_12': 13,
                       'capp_13': 14, 'capp_14': 15}
        self.court_name = 'sc'
        self.url = "http://www.search.txcourts.gov/CaseSearch.aspx?coa=cossup&d=1"

    def _download(self, request_dict={}):
        driver = webdriver.PhantomJS(executable_path='C:\Users\Andrei\Desktop\phantomjs-197\phantomjs.exe')
        driver.get(self.url)
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
        # start_date.send_keys('7/3/2014')

        end_date = driver.find_element_by_id("ctl00_ContentPlaceHolder1_dtDocumentTo_dateInput")
        end_date.send_keys(self.case_date.strftime("%m/%d/%Y"))
        # end_date.send_keys('7/3/2014')

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
            html_tree = self._text_to_etree(driver)
            if nr_of_pages.text == '1':
                driver.close()
                return html_tree
            else:
                html_pages = [html_tree]
                for i in xrange(int(nr_of_pages.text) - 1):

                    next_page = driver.find_element_by_class_name('rgPageNext')
                    next_page.click()
                    driver.implicitly_wait(5)

                    html_tree = self._text_to_etree(driver)
                    html_pages.append(html_tree)
                driver.close()
                return html_pages
        else:
            driver.close()

    def _text_to_etree(self, driver):
        text = driver.page_source

        html_tree = html.fromstring(text)
        html_tree.make_links_absolute(self.url)

        remove_anchors = lambda url: url.split('#')[0]
        html_tree.rewrite_links(remove_anchors)
        return html_tree

    def _get_case_names(self):
        return [''] * self.records_nr

    def _get_case_dates(self):
        return [self.case_date] * self.records_nr

    def _get_precedential_statuses(self):
        return ['Published'] * self.records_nr

    def _get_download_urls(self):
        if isinstance(self.html, list):
            download_urls = []
            for html_tree in self.html:
                page_records_nr = int(html_tree.xpath("count(id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00')"
                                                      "//tr[contains(., 'Opinion') or contains(., 'Order')])"))
                for record in xrange(page_records_nr):
                    path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[4]//@href".format(n=record)
                    download_urls.append(html_tree.xpath(path)[0])
            return download_urls
        else:
            return map(self._return_download_url, range(self.records_nr))

    def _get_docket_numbers(self):
        if isinstance(self.html, list):
            docket_numbers = []
            for html_tree in self.html:
                page_records_nr = int(html_tree.xpath("count(id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00')"
                                                      "//tr[contains(., 'Opinion') or contains(., 'Order')])"))
                for record in xrange(page_records_nr):
                    path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')" \
                           "/td[5]//text()[contains(., '-')]".format(n=record)
                    docket_numbers.append(html_tree.xpath(path)[0])
            return docket_numbers
        else:
            return map(self._return_case_number, range(self.records_nr))

    def _return_case_number(self, record):
        path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[5]//text()[contains(., '-')]".format(
            n=record
        )
        return self.html.xpath(path)[0]

    def _return_download_url(self, record):
        path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[4]//@href".format(n=record)
        return self.html.xpath(path)[0]