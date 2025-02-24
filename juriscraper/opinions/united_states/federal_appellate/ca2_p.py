"""Scraper for Second Circuit
CourtID: ca2
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov
"""

import time
from datetime import date, timedelta, datetime

from bs4 import BeautifulSoup
from dateutil.rrule import DAILY, rrule
from lxml.etree import tostring

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    dates = []
    names = []
    statuses = []
    urls = []
    dockets = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interval = 30
        self.court_id = self.__module__
        self.back_scrape_iterable = [i.date() for i in
            rrule(DAILY, interval=self.interval, dtstart=date(2007, 1, 1),
                until=date(2015, 1, 1), )]

    def _get_case_names(self):
        return self.names

    def _get_download_urls(self):
        return self.urls

    def _get_case_dates(self):
        return self.dates

    def _get_docket_numbers(self):
        return self.dockets

    def _get_precedential_statuses(self):
        return self.statuses

    def _download_backwards(self, d):
        self.url = "http://www.ca2.uscourts.gov/decisions?IW_DATABASE=OPN&IW_FIELD_TEXT=*&IW_SORT=-Date&IW_BATCHSIZE=100&IW_FILTER_DATE_BEFORE={before}&IW_FILTER_DATE_After={after}".format(
            before=(d + timedelta(self.interval)).strftime("%Y%m%d"),
            after=d.strftime("%Y%m%d"), )
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url="https://ww3.ca2.uscourts.gov/decisions"
        self.method='POST'
        # Parse the date string into a datetime object
        start_date1 = start_date.strftime('%Y/%m/%d')
        end_date1 = end_date.strftime('%Y/%m/%d')
        sdate = start_date1.split('/')
        edate = end_date1.split('/')
        self.parameters={"opinion":"30","sum_order":"0","IW_DATABASE":"OPN","IW_FIELD_TEXT":"*","IW_FILTER_DATE_AFTER":str(sdate[0])+str(sdate[1])+str(sdate[2]),"IW_FILTER_DATE_BEFORE":str(edate[0])+str(edate[1])+str(edate[2]),"IW_BATCHSIZE":"50","IW_SORT":"-DATE"}
        self.parse()
        return 0

    def pagination(self):
        data = tostring(self.html).decode('utf-8')
        soup = BeautifulSoup(data, 'html.parser')
        tables = soup.find_all('table')
        last_table = tables[-1]
        td_tags = last_table.find_next('tr').find_all_next('td')
        a_tag = td_tags[1].find_next('a')
        if a_tag.attrs.__contains__('disabled'):
            return None
        else:
            page_link = a_tag.attrs.get('href')
            if page_link.__contains__('https://ww3.ca2.uscourts.gov/'):
                return page_link
            else:
                page_link = "https://ww3.ca2.uscourts.gov/" + page_link
                return page_link

    def parse(self):
        if not self.downloader_executed:
            # Run the downloader if it hasn't been run already
            flag = True
            while flag:
                self.html = self._download()
                next_page_link = self.pagination()
                if next_page_link is None:
                    flag = False
                else:
                    self.method = 'GET'
                    self.url = next_page_link

                # names
                text_nodes = self.html.xpath("//table/td[2]/text()")
                for text in text_nodes:
                    self.names.append(titlecase(text))

                # dates
                date_nodes = self.html.xpath("//table/td[3]/text()")
                for dt in date_nodes:
                    date_filed = date.fromtimestamp(time.mktime(time.strptime(dt, "%m-%d-%Y")))
                    date_obj = date_filed.strftime('%d/%m/%Y')
                    self.dates.append(date_filed)
                    res = CasemineUtil.compare_date(date_obj, self.crawled_till)
                    if res == 1:
                        self.crawled_till = date_obj


                # docket_numbers
                docket_node = self.html.xpath("//table/td/b/a/nobr")
                for doc in docket_node:
                    cus_doc = []
                    cus_doc.append(doc.text_content())
                    self.dockets.append(cus_doc)

                url_node = self.html.xpath("//table/td/b/a/@href")
                for url in url_node:
                    self.urls.append(url)

                # status
                for s in self.html.xpath("//table/td[4]/text()"):
                    if "opn" in s.lower():
                        self.statuses.append("Published")
                    elif "sum" in s.lower():
                        self.statuses.append("Unpublished")
                    else:
                        self.statuses.append("Unknown")
                # Process the available html (optional)

        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self

    def _process_html(self):
        next_page_url = self.pagination()
        self.request["url"] = next_page_url
        self.request["response"] = self.request["session"].get(next_page_url,
            headers=self.request["headers"], verify=self.request["verify"],
            proxies=self.proxies, timeout=60, **self.request["parameters"])
        self._post_process_response()
        self.html = self._return_response_text_object()

    def get_class_name(self):
        return 'ca2_p'

    def get_court_name(self):
        return 'Court of Appeals for the Second Circuit'

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return "2d Circuit"
