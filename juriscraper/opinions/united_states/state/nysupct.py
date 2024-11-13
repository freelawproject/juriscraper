from datetime import datetime

from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"Sup[rt]?\.? ?[Cc]o?u?r?t?|[sS]ur?pu?rem?e? C(our)?t|Sur?pe?r?me?|Suoreme|Sup County|Integrated Domestic Violence|Soho Fashions LTD"

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
        return "nysupct"

    def get_court_name(self):
        return "New York Supreme Court"
