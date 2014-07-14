# coding=utf-8
"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Reviewer: mlr
Date created: 2014-07-11
"""

from OpinionSite import OpinionSite
from lib.string_utils import clean_string
import re
from datetime import date
from lxml import html
import time

class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.crawl_date = date.today()
        self.url = 'http://www.jud.ct.gov/external/supapp/archiveAROsup{year}.htm'.format(year=self.crawl_date.strftime("%y"))
        self.court_id = self.__module__

    def _get_case_names(self):
        names=[]
        casenames=self.html.xpath('//*[@id="AutoNumber1"]/tr[2]/td/table/tr/td/ul/li//text()')
        for x in range(0,len(casenames)):
            if "-" in casenames[x]:
                names.append(clean_string(casenames[x]))
        return names

    def _get_download_urls(self):
        return self._get_data_by_grouping_name('href')

    def _get_case_dates(self):
        dates=[]
        for title in self.html.xpath('//table[@id="AutoNumber1"]/tr[2]/td/table/tr/td/p/b'):
            
            for x in range(0,len(title.getparent().xpath('following-sibling::ul[1]/li'))):
                dates.append( date.fromtimestamp(
                      time.mktime(time.strptime(self._get_last_entry(clean_string(title.text)),'%m/%d/%y'))))
                
        return dates
                

    def _get_docket_numbers(self):
        return self._get_data_by_grouping_name('docket_numbers')

    def _get_precedential_statuses(self):
        publish=[]
        for x in range(0,len(self.case_dates)):
            if self.crawl_date < self.case_dates[x]:
                publish.append('Not Published')
            else:
                publish.append('Published')
                
        return publish

    def _get_last_entry(self,text):
        t1=text.split()
        return t1[len(t1)-1][:-1]
       
    def _get_data_by_grouping_name(self, group_name):
        path = '//table[@id="AutoNumber1"]/tr[2]/td/table/tr/td/p/b'
        meta_data = []
        for title in self.html.xpath(path):
            if group_name is 'href':
                links= title.getparent().xpath('//@href')
                for i in range(0,len(links)):
                    if( '.pdf' in links[i]):
                       meta_data.append(links[i])
                return meta_data
            if group_name is 'docket_numbers':
                docket_numbers=title.getparent().xpath('following-sibling::ul/li//a/text()')
                for d in docket_numbers:
                    meta_data.append(clean_string(d))
                return meta_data
        return meta_data
    
