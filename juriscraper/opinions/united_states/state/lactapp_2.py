"""
Scraper for the Louisiana Second Circuit Court of Appeal
CourtID: lactapp_2
Court Short Name: La. Ct. App. 2d Cir
Author: Gianfranco Huaman
History:
 - 2025-01-11, giancohs: created
"""



from datetime import datetime, date
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import get_row_column_text, get_row_column_links
from urllib.parse import urljoin, urlencode
import re

class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.la2nd.org/opinions/"
        self.year = datetime.now().year
        params = {"opinion_year": self.year}
        self.url = urljoin(self.base_url, f"?{urlencode(params)}")
        self.cases = []
        self.status = "Published"
        self.first_opinion_date = datetime(2019, 7, 17).date()
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)

    def _download(self):
        """Download the page content"""
        html = super()._download()
        
        if html is not None:
            tables = html.cssselect('table#datatable')
            if not tables or not tables[0].cssselect('tbody tr'):
                print(f"No data found for {self.year}, trying {self.year-1}")
                self.year -= 1
                params = {"opinion_year": self.year}
                self.url = urljoin(self.base_url, f"?{urlencode(params)}")
                return self._download()
        return html

    def _process_html(self):
        """Process the HTML and extract case information"""
        self.cases = []
        
        if self.html is None:
            return
        
        tables = self.html.cssselect('table#datatable')
        if tables and tables[0].cssselect('tbody tr'):
            rows = tables[0].cssselect('tbody tr')
            print(f"Found {len(rows)} cases for year {self.year}")
            
            for row in rows:
                status_str = get_row_column_text(row, 7)
                status = "Published" if "Published" in status_str else "Unpublished"
                case_date = datetime.strptime(get_row_column_text(row, 1), '%m/%d/%Y').date()
                
                # Skip if not in date range
                if self.is_backscrape and not self.date_is_in_backscrape_range(case_date):
                    continue
                if not self.is_backscrape and case_date < self.first_opinion_date:
                    continue
                
                self.cases.append({
                    "date": get_row_column_text(row, 1),
                    "docket": get_row_column_text(row, 2),
                    "name": get_row_column_text(row, 3),
                    "author": get_row_column_text(row, 4),
                    "disposition": get_row_column_text(row, 5),
                    "url": get_row_column_links(row, 8),
                    "status": status,
                })

    def make_backscrape_iterable(self, kwargs):
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        Louisiana's opinions page returns all opinions for a year, so we must
        filter out opinions not in the date range we are looking for

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.now().date()

        self.back_scrape_iterable = [(start, end)]

    def _download_backwards(self, dates):
        """Called when backscraping

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.start_date, self.end_date = dates
        self.is_backscrape = True
        logger.info(
            "Backscraping for range %s %s", self.start_date, self.end_date
        )
        
        self.year = self.start_date.year
        params = {"opinion_year": self.year}
        self.url = urljoin(self.base_url, f"?{urlencode(params)}")
        self.html = self._download()
        self._process_html()

    def date_is_in_backscrape_range(self, case_date):
        """When backscraping, check if the case date is in
        the backscraping range

        :param date_str: string date from the HTML source
        :return: True if date is in backscrape range
        """
        return self.start_date <= case_date <= self.end_date