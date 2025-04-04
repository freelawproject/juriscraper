"""Scraper for United States Court of Appeals for the Federal Circuit
CourtID: cafc
Court Short Name: U.S. Court of Appeals for the Federal Circuit
Author: Dave Voutila
Reviewer:
Type:
History:
    2016-05-10: Created by Dave Voutila, @voutilad
    2021-01-24: Item's title split fixed to extract opinions name, @satsuki-chan
"""
import json
from datetime import datetime

import feedparser
from lxml.html import fromstring

from lxml import html
from bs4 import BeautifulSoup
from socks import method

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    flag = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def _process_html(self):
        html_string = html.tostring(self.html, pretty_print=True).decode(
            'utf-8')
        soup = BeautifulSoup(html_string, 'html.parser')
        content = soup.find('p').text
        json_content = json.loads(content)
        data = json_content['data']
        if (len(data) == 0):
            self.flag = False
            return
        for i in range(len(data)):
            item = data[i]
            date = item[0]
            docket = item[1]
            origin = item[2]
            type = item[3]
            name = item[4].replace("</a>", "")
            status = item[5]
            slug = item[6]
            self.cases.append({"date": date, "docket": [docket],
                               "url": f"https://cafc.uscourts.gov/{slug}",
                               "name": name,
                               "status": self._get_status(status.lower())})

    def _process_html_old(self) -> None:
        """Process the RSS feed.

        Iterate over each item in the RSS feed to extract out
        the date, case name, docket number, and status and pdf URL.
        Return: None
        """
        feed = feedparser.parse(self.request["response"].content)
        for item in feed["entries"]:
            value = item["content"][0]["value"]
            docket, title = item["title"].split(" [")[0].split(": ", 1)
            slug = fromstring(value).xpath(".//a/@href")[0]
            self.cases.append({"date": item["published"], "docket": docket,
                               "url": f"https://cafc.uscourts.gov/{slug}",
                               "name": titlecase(title),
                               "status": self._get_status(
                                   item["title"].lower()), })

    def _get_status(self, title: str) -> str:
        """Get precedential status from title string.

        return: The precedential status of the case.
        """
        if "nonprecedential" in title:
            status = "Unpublished"
        elif "precedential" in title:
            status = "Published"
        else:
            status = "Unknown"
        return status

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url = 'https://cafc.uscourts.gov/wp-admin/admin-ajax.php?action=get_wdtable&table_id=1'
        self.method = 'POST'
        sdate = start_date.strftime("%d/%m/%Y").split("/")
        edate = end_date.strftime("%d/%m/%Y").split("/")
        start = 0
        length = 100
        draw = 2
        self.flag = True
        while (self.flag):
            # self.parameters = {'draw': str(draw), 'columns[0][data]': '0', 'columns[0][name]': 'Release_Date', 'columns[0][searchable]': 'true', 'columns[0][orderable]': 'true', 'columns[0][search][value]': str(sdate[1])+'/'+str(sdate[0])+'/'+str(sdate[2])+'|'+str(edate[1])+'/'+str(edate[0])+'/'+str(edate[2]), 'columns[0][search][regex]': 'false', 'columns[1][data]': '1', 'columns[1][name]': 'Appeal_Number', 'columns[1][searchable]': 'true', 'columns[1][orderable]': 'true', 'columns[1][search][value]': '', 'columns[1][search][regex]': 'false', 'columns[2][data]': '2', 'columns[2][name]': 'Origin', 'columns[2][searchable]': 'true', 'columns[2][orderable]': 'true', 'columns[2][search][value]': '', 'columns[2][search][regex]': 'false', 'columns[3][data]': '3', 'columns[3][name]': 'Document_Type', 'columns[3][searchable]': 'true', 'columns[3][orderable]': 'true', 'columns[3][search][value]': '', 'columns[3][search][regex]': 'false', 'columns[4][data]': '4', 'columns[4][name]': 'Case_Name', 'columns[4][searchable]': 'true', 'columns[4][orderable]': 'true', 'columns[4][search][value]': '', 'columns[4][search][regex]': 'false', 'columns[5][data]': '5', 'columns[5][name]': 'Status', 'columns[5][searchable]': 'true', 'columns[5][orderable]': 'true', 'columns[5][search][value]': '', 'columns[5][search][regex]': 'false', 'columns[6][data]': '6', 'columns[6][name]': 'File_Path', 'columns[6][searchable]': 'false', 'columns[6][orderable]': 'false', 'columns[6][search][value]': '', 'columns[6][search][regex]': 'false', 'order[0][column]': '0', 'order[0][dir]': 'desc', 'start': str(start), 'length': '500', 'search[value]': '', 'search[regex]': 'false', 'wdtNonce': 'ed364e2dd7', 'sRangeSeparator': '|'}
            self.parameters = {'draw': '2', 'columns[0][data]': '0',
                               'columns[0][name]': 'Release_Date',
                               'columns[0][searchable]': 'true',
                               'columns[0][orderable]': 'true',
                               'columns[0][search][value]': str(
                                   sdate[1]) + '/' + str(sdate[0]) + '/' + str(
                                   sdate[2]) + '|' + str(edate[1]) + '/' + str(
                                   edate[0]) + '/' + str(edate[2]),
                               'columns[0][search][regex]': 'false',
                               'columns[1][data]': '1',
                               'columns[1][name]': 'Appeal_Number',
                               'columns[1][searchable]': 'true',
                               'columns[1][orderable]': 'true',
                               'columns[1][search][value]': '',
                               'columns[1][search][regex]': 'false',
                               'columns[2][data]': '2',
                               'columns[2][name]': 'Origin',
                               'columns[2][searchable]': 'true',
                               'columns[2][orderable]': 'true',
                               'columns[2][search][value]': '',
                               'columns[2][search][regex]': 'false',
                               'columns[3][data]': '3',
                               'columns[3][name]': 'Document_Type',
                               'columns[3][searchable]': 'true',
                               'columns[3][orderable]': 'true',
                               'columns[3][search][value]': '',
                               'columns[3][search][regex]': 'false',
                               'columns[4][data]': '4',
                               'columns[4][name]': 'Case_Name',
                               'columns[4][searchable]': 'true',
                               'columns[4][orderable]': 'true',
                               'columns[4][search][value]': '',
                               'columns[4][search][regex]': 'false',
                               'columns[5][data]': '5',
                               'columns[5][name]': 'Status',
                               'columns[5][searchable]': 'true',
                               'columns[5][orderable]': 'true',
                               'columns[5][search][value]': '',
                               'columns[5][search][regex]': 'false',
                               'columns[6][data]': '6',
                               'columns[6][name]': 'File_Path',
                               'columns[6][searchable]': 'false',
                               'columns[6][orderable]': 'false',
                               'columns[6][search][value]': '',
                               'columns[6][search][regex]': 'false',
                               'order[0][column]': '0',
                               'order[0][dir]': 'desc', 'start': f'{start}',
                               'length': f'{length}', 'search[value]': '',
                               'search[regex]': 'false',
                               'wdtNonce': '3a29821d98',
                               'sRangeSeparator': '|'}
            self.parse()
            start = start + length
            draw = draw + 1
            self.downloader_executed = False
        return 0

    def get_class_name(self):
        return "cafc"

    def get_court_type(self):
        return "Federal"

    def get_court_name(self):
        return "United States Court of Appeals for the Federal Circuit"

    def get_state_name(self):
        return "Fed. Cir."
