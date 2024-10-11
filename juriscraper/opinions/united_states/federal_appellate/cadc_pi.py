"""Scraper for Public Interest Cases for the CADC
CourtID: cadc
Court Short Name: Court of Appeals of the District of Columbia
Author: flooie
History:
  2021-12-18: Created by flooie
  2023-01-12: Fixed requests.exceptions.InvalidURL error by grossir
"""
from datetime import datetime
from time import strftime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from lxml import etree

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://media.cadc.uscourts.gov/orders/bydate/recent"
        self.base = "https://www.cadc.uscourts.gov"
        self.court_id = self.__module__

    def _process_html(self) -> None:
        """Iterate over the public interest cases.

        :return: None
        """
        soup = BeautifulSoup(self.html, 'html.parser')
        table = soup.find('table', class_='mt-0 pt-0 pb-3 row')
        tbody=table.find('tbody')
        trs=tbody.find('tr')
        for tr in trs:
            tr.find("td")

        # for row in self.html.xpath(".//div[@class='row']"):
        #     url = row.xpath(".//a/@href")[0]
        #     docket = [row.xpath(".//a/span/text()")[0]]
        #     name = row.xpath(".//div[@class='column-two']/div[1]/text()")[
        #         0
        #     ].strip()
        #     date = row.xpath(".//date/text()")[0]
        #     self.cases.append(
        #         {
        #             "date": date,
        #             "url": urljoin("https:", url),
        #             "docket": docket,
        #             "name": name,
        #             "status": "Published",
        #         }
        #     )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for month in range(start_date.month, end_date.month+1):
            self.url='https://media.cadc.uscourts.gov/orders/bydate/'+str(end_date.year)+'/'+str(month)
            if not self.downloader_executed:
                # Run the downloader if it hasn't been run already
                self.html = self._download()

                # Process the available html (optional)
                html_string = etree.tostring(self.html, pretty_print=True,encoding='unicode')
                soup = BeautifulSoup(html_string, 'html.parser')
                results = [div for div in soup.find_all('div') if div.get('class') == ['mt-0', 'pt-0', 'pb-3', 'row']]
                if(results.__len__()!=0):
                    for i in range(len(results)):
                        inner_div = [div for div in soup.find_all('div') if
                                   div.get('class') == ['col', 'col-md-12']]
                        for j in range(len(inner_div)):
                            if(inner_div[j].text.__len__()!=0):
                                title = inner_div[j].text
                                url = inner_div[j].find_next("a").attrs.get('href')
                                docket = [inner_div[j].find_next("a").text]
                self.downloader_executed = False

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
        return 0

    def get_class_name(self):
        return "cadc_pi"
