from datetime import datetime

from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"(Just|Village|Town) Ct|Just(ice)? Cour+t"

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for i in range(start_date.month, end_date.month+1):
            if i==end_date.month:
                self.url=self.build_url()
            else:
                self.url=self.build_url(datetime(year=start_date.year,month=i,day=start_date.day))
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "nyjustct"

    def get_court_name(self):
        return "New York Justice Court"
