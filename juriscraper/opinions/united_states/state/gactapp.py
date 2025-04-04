# Scraper for Georgia Appeals Court
# CourtID: gactapp
# Court Short Name: gactapp
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from datetime import date, timedelta, datetime

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath("//tr")[::-1][:-1]:
            docket, name, date, disposition, _, url = row.xpath(".//td")
            self.cases.append({"docket": [docket.text_content()],
                               "name": titlecase(name.text_content()),
                               "date": date.text_content(),
                               "disposition": disposition.text_content().title(),
                               "url": url.xpath(".//a")[0].get("href"), })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start = start_date.date().strftime("%Y-%m-%d")
        end = end_date.date().strftime("%Y-%m-%d")
        self.url = f"https://www.gaappeals.us/wp-content/themes/benjamin/docket/docketdate/results_all.php?OPstartDate={start}&OPendDate={end}&submit=Start+Opinions+Search"
        self.parse()
        return 0

    def get_court_name(self):
        return "Georgia Court of Appeals"

    def get_class_name(self):
        return "gactapp"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Georgia"
