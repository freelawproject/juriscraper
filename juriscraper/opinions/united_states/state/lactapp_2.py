from datetime import datetime, date
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.html_utils import get_row_column_text, get_row_column_links

class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.la2nd.org/opinions/"
        self.year = datetime.now().year
        self.url = f"{self.base_url}?opinion_year={self.year}"
        self.cases = []
        self.status = "Published"

        
        # Add these for backwards scraping
        self.target_date = datetime.today()
        self.first_opinion_date = datetime(2019, 7, 17)  # Your start date
        self.days_interval = 28  # Monthly interval
        self.make_backscrape_iterable(kwargs)

    def _download(self):
        """Download the page content"""
        html = super()._download()
        
        if html is not None:
            tables = html.cssselect('table#datatable')
            if not tables or not tables[0].cssselect('tbody tr'):
                print(f"No data found for {self.year}, trying {self.year-1}")
                self.year -= 1
                self.url = f"{self.base_url}?opinion_year={self.year}"
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
                case = {
                    "date": get_row_column_text(row, 1),
                    "docket": get_row_column_text(row, 2),
                    "name": get_row_column_text(row, 3),
                    "author": get_row_column_text(row, 4),
                    "disposition": get_row_column_text(row, 5),
                    "lower_court": get_row_column_text(row, 6),
                    "summary": get_row_column_text(row, 7),
                    "url": get_row_column_links(row, 8),
                }
                
                # Filter by date if in backwards scraping mode
                case_date = datetime.strptime(case['date'], '%m/%d/%Y')
                if case_date >= self.first_opinion_date:
                    self.cases.append(case)

    def _download_backwards(self, target_date: date) -> None:
        """Handle backwards scraping"""
        self.target_date = target_date
        self.year = target_date.year
        self.url = f"{self.base_url}?opinion_year={self.year}"
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs):
        """Set up the backscraping iteration"""
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(self.back_scrape_iterable)