# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.
from cgitb import html
from datetime import datetime
from xml.etree.ElementTree import tostring

import pytz
from lxml import html
import feedparser
from bs4 import BeautifulSoup

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def _process_html(self):
        html_string = html.tostring(self.html, pretty_print=True).decode(
            'utf-8')
        soup = BeautifulSoup(html_string, 'html.parser')
        table = soup.find('table', id="results")
        tbody = table.find_next('tbody')
        trs = tbody.find_all_next('tr')
        # if self.test_mode_enabled():
        #     self.year = 2022
        # feed = feedparser.parse(self.request["response"].content)
        for tr in trs:
            td = tr.find_all_next('td')
            case_docket = td[0].text
            docket= [case_docket]
            title = td[1].text
            case_type = td[2].text
            case_date = td[3].text
            date_object = datetime.strptime(case_date, '%m/%d/%Y')
            date_object = date_object.replace(hour=0, minute=0, second=0)
            new_date_format = '%d/%m/%Y'
            new_date_string = date_object.strftime(new_date_format)
            res = CasemineUtil.compare_date(new_date_string, self.crawled_till)
            if res == 1:
                self.crawled_till = new_date_string
            timezone = pytz.timezone('America/Chicago')  # CDT is the same as 'America/Chicago'
            date_object = timezone.localize(date_object)

            # Step 3: Format the datetime object to the desired string format
            formatted_date = date_object.strftime('%a, %d %b %Y %H:%M:%S %Z')

            status = td[4].text
            url = td[4].find_next('a').attrs['href']
            author = td[5].text
            # parts = item["summary"].split()
            # docket = parts[parts.index("case#") + 1]
            # name = item["summary"].split(docket)[1].split("(")[0]
            # author = item["summary"].split("{")[1].split("}")[0]
            self.cases.append({
                "url": url,
                "docket": docket,
                "date": formatted_date,
                "name": title,
                "status": status,
                "judge": [author],
                "author": author,
                "type": case_type
                }
            )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        sdate = start_date.strftime('%Y-%m-%d')
        edate = end_date.strftime('%Y-%m-%d')
        self.url='https://media.ca7.uscourts.gov/cgi-bin/OpinionsWeb/processWebInputExternal.pl?Time=any&startDate='+sdate+'&endDate='+edate+'&Author=any&AuthorName=&Case=any&CaseYear=&CaseNum=&OpsOnly=yesRubmit=RssRecent&RssJudgeName=Sykes&'
        self.parse()
        return 0


    def get_class_name(self):
        return "ca7"

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return "7th Circuit"

    def get_court_name(self):
        return 'Court of Appeals for the Seventh Circuit'


