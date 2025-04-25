from datetime import datetime
import html

from lxml import html
import requests

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"
        self.current_year = None

    def _process_html(self):
        html = self.html
        print(html)
        pass

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year, end_date.year+1):
            self.url=f'https://www.mass.gov/lists/{year}-dia-reviewing-board-decisions'
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "mass_dia"

    def get_court_type(self):
        return 'state'

    def get_state_name(self):
        return "Massachusetts"

    def get_court_name(self):
        return "Massachusetts Department of Industrial Accidents"