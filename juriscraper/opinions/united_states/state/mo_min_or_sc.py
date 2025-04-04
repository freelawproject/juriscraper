"""Scraper for Missouri
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
"""

from datetime import date, datetime

import requests
from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Supreme"
        # self.url = self.build_url()
        self.status = "Published"
        self.url = "https://www.courts.mo.gov/SUP/index.nsf/TheMinutes"
        self.base_url = "https://www.courts.mo.gov"

    def process_html(self,case_html,date):

        for row in case_html.xpath("//form/table"):
            docket=row.xpath(".//tr[2]/td[1]/font/text()")
            anchor = row.xpath(".//tr[2]/td[2]/a")
            if anchor:
                name=row.xpath(".//tr[2]/td[2]/a/font/text()")
                url=row.xpath(".//tr[2]/td[2]/a/@href")
            else:
                name = row.xpath(".//tr[2]/td[2]/font/text()")
                url = "null"
            content = ""
            for text in row.xpath(".//tr[4]/td[2]/font/text()"):
                content += text.strip()
            date=date

            # print(html.tostring(docket[0],pretty_print=True).decode('UTF-8'))
            print(docket)
            print(name)
            print(url)
            print(date)
            print(content)
            print("-------------------------")

    def getdates(self,start_date , end_date):
        print(f"finding the minute orders between {start_date} and {end_date}")
        table = self.html.xpath("//table[@cellpadding='2']")

        for row in table[0].xpath(".//tr[@valign='top']/td"):
            dt = row.xpath(".//a/text()")
            date_string = dt[0].replace("Minutes of ","")
            case_date = datetime.strptime(date_string, "%B %d, %Y")
            if case_date.date()>= start_date and case_date.date()<=end_date:
                date_url = row.xpath(".//a/@href")[0]

                case_html_text = requests.get(date_url,headers=self.request["headers"],proxies=self.proxies)
                case_html=html.fromstring(case_html_text.text)
                self.process_html(case_html,case_date.date())


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start_date=datetime(2024,1,1)
        if not self.downloader_executed:
            self.html = self._download()

            # print(html.tostring(self.html,pretty_print=True).decode('UTF-8'))
            self.getdates(start_date.date(),end_date.date())

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "mo"

    def get_state_name(self):
        return "Missouri"

    def get_court_name(self):
        return "Supreme Court of Missouri"
