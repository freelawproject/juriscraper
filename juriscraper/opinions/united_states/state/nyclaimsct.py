from datetime import datetime
from typing import List

from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"^Ct Cl|C(our)?t( [Oo]f)? Cl(aims)?$"

    def _get_child_courts(self) -> List[str]:
        """Return an empty string as child_court, since the
        New York Court of Claims in this source has no children

        :return: list of empty strings
        """
        return ["" for _ in self.cases]

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
        return "nyclaimsct"

    def get_court_name(self):
        return "New York Court of Claims"
