"""
Author: Michael Lissner
Date created: 2013-04-05
Revised by Taliah Mirmalek on 2014-02-07
Scraper for the Supreme Court of Arizona
CourtID: ariz
Court Short Name: Ariz.
"""

from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://superiorcourt.maricopa.gov/departments/superior-court/tax/tax-decisions/"
        self.status = 'Unpublished'
    def _process_html(self, start :int , end :int) -> None:
        for divs in self.html.xpath(".//section[@class='container common-accordion xs-custom-container overlap-padding-s section-inner-space']/div[@class='accordion']"):
            for year_divs in divs.xpath(".//div[@class='accordion-item ']"):
                curr_year = int(year_divs.xpath(".//h3/button/text()")[0].strip())
                if end >= curr_year >= start:
                    for records in year_divs.xpath(".//div[@class='accordion-body']/p"):
                        strng=records.xpath("./text()")[0].strip()
                        dat=strng[:strng.find(" ")]
                        name=strng[strng.find(" ")+1 :]
                        dt = datetime.strptime(dat, "%m/%d/%Y")
                        formatted_date = dt.strftime("%d/%m/%Y")
                        res = CasemineUtil.compare_date(self.crawled_till, formatted_date)
                        if res == 1:
                            return
                        dock=records.xpath("./a/text()")
                        url=records.xpath("./a/@href")[0]

                        self.cases.append(
                            {
                                "date": formatted_date,
                                "docket": dock,
                                "name": name,
                                "url": url
                            }
                        )
                else: continue


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start = start_date.year
        end = end_date.year
        if not self.downloader_executed:
            self.html = self._download()
            self._process_html(start , end)

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return 0

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Arizona Tax Court"

    def get_state_name(self):
        return "Arizona"

    def get_class_name(self):
        return "ariz_tax"
