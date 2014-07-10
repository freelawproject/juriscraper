'''
History:
 - Left message for Diana Norman (512) 463-1551, at the Appeals Court, requesting a call back.

http://www.search.txcourts.gov/RetrieveDocument.aspx?DocId=886&Index=***coa01%5cOpinion
http://www.search.txcourts.gov/SearchMedia.aspx?MediaVersionID=906eee9d-85e3-48a8-9349-7387948b6673&coa=coa01&DT=Opinion&MediaID=cf67a534-225a-4a5e-966f-41f68c35e6c4
'''

# Author: Michael Lissner
# Date created: 2013-06-05


import requests
from datetime import date
from datetime import datetime
from lxml import etree
from selenium import webdriver

from juriscraper.OpinionSite import OpinionSite
from juriscraper.DeferringList import DeferringList
from juriscraper.lib.string_utils import titlecase


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
		# Not Working
        self.parameters = {
            # 'ctl00_RadScriptManager1_TSM': ';;System.Web.Extensions, Version=3.5.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en-US:eb198dbd-2212-44f6-bb15-882bde414f00:ea597d4b:b25378d2;Telerik.Web.UI, Version=2012.1.411.35, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:4cad056e-160b-4b85-8751-cc8693e9bcd0:16e4e7cd:f7645509:7c926187:8674cba1:b7778d6c:c08e9f8a:a51ee93e:59462f1:ed16cbdc:58366029:24ee1bba:f46195d3:874f8ea2:19620875:39040b5c',
            # '__EVENTTARGET' : 'ctl00$ContentPlaceHolder1$grdDocuments$ctl00$ctl03$ctl01$ctl05',
            # '__EVENTARGUMENT':'',
            # '__LASTFOCUS':'',
            'ctl00$ContentPlaceHolder1$Fuzziness': '0',
            'ctl00$ContentPlaceHolder1$SearchType': 'rbSearchByDocument',
            'ctl00$ContentPlaceHolder1$Stemming': 'on',
            'ctl00$ContentPlaceHolder1$btnSearchText': 'Search Text',
            'ctl00$ContentPlaceHolder1$chkListCourts$0': 'on',
            'ctl00$ContentPlaceHolder1$chkListDocTypes$0': 'on',
            'ctl00$ContentPlaceHolder1$chkListDocTypes$1': 'on',
            'ctl00$ContentPlaceHolder1$dtDocumentFrom': '2014-07-03',
            'ctl00$ContentPlaceHolder1$dtDocumentFrom$dateInput': '2014-07-03-00-00-00',
            'ctl00$ContentPlaceHolder1$dtDocumentTo': '2014-07-03',
            'ctl00$ContentPlaceHolder1$dtDocumentTo$dateInput': '2014-07-03-00-00-00',
            'ctl00$ContentPlaceHolder1$txtSearchText': '',
            'ctl00_ContentPlaceHolder1_dtDocumentFrom_ClientState': '',
            'ctl00_ContentPlaceHolder1_dtDocumentFrom_calendar_AD': '[[1980,1,1],[2099,12,30],[2014,7,9]]',
            'ctl00_ContentPlaceHolder1_dtDocumentFrom_calendar_SD': '[[2014,7,3]]',
            'ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput_ClientState': '{"enabled":true,"emptyMessage":"","minDateStr":"1/1/1980 0:0:0","maxDateStr":"12/31/2099 0:0:0","enteredText":"7/3/2014"}',
            'ctl00_ContentPlaceHolder1_dtDocumentTo_ClientState': '',
            'ctl00_ContentPlaceHolder1_dtDocumentTo_calendar_AD': '[[1980,1,1],[2099,12,30],[2014,7,9]]',
            'ctl00_ContentPlaceHolder1_dtDocumentTo_calendar_SD': '[[2014,7,3]]',
            'ctl00_ContentPlaceHolder1_dtDocumentTo_dateInput_ClientState': '{"enabled":true,"emptyMessage":"","minDateStr":"1/1/1980 0:0:0","maxDateStr":"12/31/2099 0:0:0","enteredText":"7/3/2014"}}'
        }
        self.method = 'POST'

    # def _download(self, request_dict={}):
    #     driver = webdriver.Firefox()
    #     driver.get(self.url)
    #     driver.implicitly_wait(10)
    #     search_court_type = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListCourts_{court_nr}".format(
    #         court_nr=self.courts[self.court_name])
    #     )
    #     search_court_type.click()
    #
    #     search_opinions = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListDocTypes_0")
    #     search_opinions.click()
    #
    #     search_orders = driver.find_element_by_id("ctl00_ContentPlaceHolder1_chkListDocTypes_1")
    #     search_orders.click()
    #
    #     start_date = driver.find_element_by_id("ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput")
    #     # start_date.send_keys(self.case_date.strftime("%m/%d/%Y"))
    #     start_date.send_keys('7/3/2014')
    #
    #     end_date = driver.find_element_by_id("ctl00_ContentPlaceHolder1_dtDocumentTo_dateInput")
    #     # end_date.send_keys(self.case_date.strftime("%m/%d/%Y"))
    #     end_date.send_keys('7/3/2014')
    #
    #     submit = driver.find_element_by_id("ctl00_ContentPlaceHolder1_btnSearchText")
    #     submit.click()
    #     driver.implicitly_wait(20)
    #     text = driver.page_source
    #     driver.close()
    #
    #     html_tree = html.fromstring(text)
    #     html_tree.make_links_absolute(self.url)
    #
    #     remove_anchors = lambda url: url.split('#')[0]
    #     html_tree.rewrite_links(remove_anchors)
    #     return html_tree

    def _get_download_urls(self):
        return map(self._return_download_url, range(self.records_nr))

    def _get_case_names(self):
        return [''] * self.records_nr

    def _get_case_dates(self):
        print(etree.tostring(self.html))
        self.records_nr = int(self.html.xpath("count(id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00')"
                                              "//tr[contains(., 'Opinion') or contains(., 'Order')])"))
        return [self.case_date] * self.records_nr

    def _get_precedential_statuses(self):
        return ['Published'] * self.records_nr

    def _get_docket_numbers(self):
        return map(self._return_case_number, range(self.records_nr))

    def _return_case_number(self, record):
        path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[5]//text()[contains(., '-')]".format(
            n=record
        )
        return self.html.xpath(path)

    def _return_download_url(self, record):
        path = "id('ctl00_ContentPlaceHolder1_grdDocuments_ctl00__{n}')/td[4]//@href".format(n=record)
        return self.html.xpath(path)