"""Scraper for Supreme Court of U.S.
CourtID: scotus
Court Short Name: scotus
History:
 - 2014-07-20 - Created by Andrei Chelaru, reviewed by MLR
 - 2017-10-09 - Updated by MLR.
"""

from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(2010, 2015))
        self.dockets=[]
        self.dates=[]
        self.urls=[]
        self.names=[]
        self.types=[]

    def _get_download_urls(self):
        return self.urls
        # path = "id('list')//tr//a/text()"
        # return list(map(self._return_download_url, self.html.xpath(path)))

    @staticmethod
    def _return_download_url(d):
        file_type = "mp3"  # or 'wma' is also available for any case.
        download_url = "http://www.supremecourt.gov/media/audio/{type}files/{docket_number}.{type}".format(type=file_type, docket_number=d)
        return download_url

    def _get_case_names(self):
        return self.names
        # path = "id('list')//tr/td/span/text()"
        # return [s.lstrip(". ") for s in self.html.xpath(path)]

    def _get_case_dates(self):
        return self.dates
        # path = "id('list')//tr/td[2]//text()"
        # return [
        #     datetime.strptime(s, "%m/%d/%y").date()
        #     for s in self.html.xpath(path)
        #     if not "Date" in s
        # ]

    def _get_docket_numbers(self):
        return self.dockets
        # path = "id('list')//tr//a/text()"
        # return list(self.html.xpath(path))

    def _download_backwards(self, year):
        self.url = (
            f"http://www.supremecourt.gov/oral_arguments/argument_audio/{year}"
        )
        self.html = self._download()

    def _get_opinion_types(self):
        return self.types

    def _process_html(self):
        for row in self.html.xpath("//div[@id='list']//table//tr[td]"):
            cells = row.xpath("td")
            if len(cells) >= 2:
                case_link = cells[0].xpath(".//a")[0]  # Get the <a> element
                case_number = case_link.text  # Get case number
                case_href = case_link.get("href")  # Get href value
                case_name = cells[0].xpath(".//span/text()")[0]  # Get case name
                date_argued = datetime.strptime(cells[1].text.strip(),'%m/%d/%y')  # Get date argued
                res=CasemineUtil.compare_date(self.crawled_till,date_argued.strftime('%d/%m/%Y'))
                if res==1:
                    break
                type='Oral Argument'
                self.dockets.append([case_number])
                self.names.append(case_name)
                self.urls.append(case_href)
                self.dates.append(date_argued)
                self.types.append(type)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year-1,end_date.year):
            self.url = f"https://www.supremecourt.gov/oral_arguments/argument_transcript/{year}"
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "scotus"

    def get_court_name(self):
        return 'U.S. Supreme Court'

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return ''
