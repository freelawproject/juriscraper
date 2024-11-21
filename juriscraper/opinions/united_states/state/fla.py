# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from bs4 import BeautifulSoup
from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # make a backscrape request every `days_interval` range, to avoid pagination
    days_interval = 20
    first_opinion_date = datetime(1999, 9, 23)
    flag = True
    # even though you can put whatevere number you want as limit, 50 seems to be max
    # base_url = "https://www.floridasupremecourt.org/search/?searchtype=opinions&limit=50&startdate={}&enddate={}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        # self.set_url()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parses HTML into case dictionaries

        :return: None
        """
        path = '//div[@class="search-results"]//tbody/tr'
        if path is None:
            self.flag=False
        for row in self.html.xpath(path):
            cells = row.xpath("td")
            url = cells[5].xpath("a/@href")
            name = cells[3].text_content().strip()

            if not url or not name:
                # Skip rows without PDFs or without case names
                continue

            dockets = str(cells[2].text_content().strip())
            dockets = dockets.replace("&",",")
            doc_arr=[]
            if dockets.__contains__(","):
                doc_arr=dockets.split(',')
            else:
                doc_arr.append(dockets)

            new_doc = []
            for i in doc_arr:
                new_doc.append(i.strip())

            self.cases.append(
                {
                    "url": url[0],
                    "docket": new_doc,
                    "name": name,
                    "date": cells[0].text_content().strip(),
                    "status": self.status,
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL using date arguments

        If not dates are passed, get 50 most recent opinions

        :param start: start date
        :param end: end date
        :return: none
        """
        if not start:
            end = datetime.today()
            start = end - timedelta(days=365)

        fmt = "%m/%d/%Y"
        # self.url = self.base_url.format(start.strftime(fmt), end.strftime(fmt))

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Overrides scraper URL using date inputs

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(*dates)
        logger.info("Backscraping for range %s %s", *dates)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        offset=0
        sdate=f'{start_date.month}%2F{start_date.day}%2F{start_date.year}'
        edate=f'{end_date.month}%2F{end_date.day}%2F{end_date.year}'
        flag=True
        while flag:
            self.url=f'https://supremecourt.flcourts.gov/search/opinions/?query=&offset={offset}&view=embed_custom&startDate={sdate}&endDate={edate}&searchType=opinions&scopes%5B0%5D=supreme_court&date%5Bday%5D=&date%5Bmonth%5D=&date%5Byear%5D=&limit=50&sort=opinion%2Fdisposition_date%20desc%2C%20opinion%2Fcase_number%20asc&recentOnly=0&types%5B0%5D=Written&types%5B1%5D=PCA&types%5B2%5D=Citation&activeOnly=0&active_only=0&nonActiveOnly=0&nonactive_only=0&show_scopes=1&hide_search=0&hide_filters=0&siteaccess=supreme&type%5B0%5D=Written&type%5B1%5D=PCA&type%5B2%5D=Citation'
            self.parse()
            self.downloader_executed=False
            offset = offset+50
            last_li = self.html.xpath('//ul[@class="pagination"]/li[last()]')
            # Print the last <li> element
            if list(last_li).__len__() == 0:
                flag = False
            else:
                disabled_li = html.tostring(last_li[0], pretty_print=True).decode()
                if disabled_li.__contains__('disabled'):
                    flag = False
        return 0

    def get_state_name(self):
        return "Florida"

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Supreme Court of Florida"

    def get_class_name(self):
        return "fla"
