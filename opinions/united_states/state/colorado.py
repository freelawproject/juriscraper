"""
Auth: Asadullah Baig<asadullahbeg@outlook.com>
History:
Notes: There are some Docket numbers which dont obey the general format for them additional code is there
"""

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from lxml import html
import requests


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.cobar.org/opinions/index.cfm?courtid=1'
        self.court_id = self.__module__

    def _get_case_names(self):
        g1=[]
        print 'IN  GET CASE NAMES'
        page=requests.get(self.url)
        tree=html.fromstring(page.text)
        for h2 in tree.xpath('//*[@id="bodyBox"]/table[2]/tr[1]/td[1]/ul[1]/li/strong/a/@href'):
            str1='http://www.cobar.org/opinions/'+h2
            page1=requests.get(str1)
            tree1=html.fromstring(page1.text)
            text=tree1.xpath('//*[@id="opinion"]/p/a/b//text()')
            g2=''
            for t in text:
                str=t.split('.')
                a=0
                for g in str:
                    if a>=3:
                        g2=g2+g
                    a=a+1
                print g2
                g1.append(g2)
                g2=''
        return [g for g in g1]

    def _get_download_urls(self):
        back=[]
        print 'IN GET DOWNLOAD URLS'
        page=requests.get(self.url)
        tree=html.fromstring(page.text)

        for h2 in tree.xpath('//*[@id="bodyBox"]/table[2]/tr[1]/td[1]/ul[1]/li/strong/a/@href'):
            str1='http://www.cobar.org/opinions/'+h2
            page1=requests.get(str1)
            tree1=html.fromstring(page1.text)
            opinions=tree1.xpath('//*[@id="opinion"]/p/a/@href')
            d=0
            a=0
            for opinion in opinions:
                d=d+1
            for opinion in opinions:
                if(a<=d-3):
                    opinion= 'http://www.cobar.org/opinions/'+opinion

                    back.append(opinion)
                a=a+1

        return [url for url in back]

    def _get_case_dates(self):
        g1=[]
        print 'IN GET CASE DATES'
        page=requests.get(self.url)
        tree=html.fromstring(page.text)

        for h2 in tree.xpath('//*[@id="bodyBox"]/table[2]/tr[1]/td[1]/ul[1]/li/strong/a/@href'):
            str1='http://www.cobar.org/opinions/'+h2
            page1=requests.get(str1)
            tree1=html.fromstring(page1.text)
            date1=tree1.xpath('//*[@id="opinion"]/p[1]/font/b/font//text()')
            text=tree1.xpath('//*[@id="opinion"]/p/a/b//text()')
            g2=''
            try:
                date_obj = date.fromtimestamp(
                      time.mktime(time.strptime(date1[0], "%B %d, %Y")))
            except ValueError:
                date_obj = date.fromtimestamp(
                      time.mktime(time.strptime(date1[0], "%B %Y")))
            for t in text:

                g1.append(date_obj)
                print date_obj
        return [g for g in g1]

    def _get_docket_numbers(self):
        g1=[]
        print 'IN GET DOCKET NUMBERS'
        page=requests.get(self.url)
        tree=html.fromstring(page.text)

        for h2 in tree.xpath('//*[@id="bodyBox"]/table[2]/tr[1]/td[1]/ul[1]/li/strong/a/@href'):
            str1='http://www.cobar.org/opinions/'+h2
            page1=requests.get(str1)
            tree1=html.fromstring(page1.text)
            text=tree1.xpath('//*[@id="opinion"]/p/a/b//text()')
            g2=''
            for t in text:
                str=t.split('.')
                a=0
                for g in str:

                    if a>=1 and a<=2:
                        g2=g2+g
                    if 'No' not in str[1]:
                        g2=''
                        g2='No '+str[1]
                    a=a+1
                print g2
                g1.append(g2)
                g2=''
        return [g for g in g1]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
