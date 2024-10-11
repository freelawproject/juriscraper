import time
from datetime import date, datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.cadc.uscourts.gov/internet/opinions.nsf/uscadcopinions.xml"
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath("//item/description/text()")]

    def _get_download_urls(self):
        return [
            html.tostring(e, method="text").decode()
            for e in self.html.xpath("//item/link")
        ]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath("//item/pubdate/text()"):
            date_only = " ".join(date_string.split(" ")[1:4])
            dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_only, "%d %b %Y"))
                )
            )
        return dates

    def _get_docket_numbers(self):
        dockets=[]
        for e in self.html.xpath("//item/title/text()"):
            dock=[e.split("|")[0]]
            dockets.append(dock)
        return dockets

    def _get_precedential_statuses(self):
        return ["Published" for _ in range(0, len(self.case_names))]

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "cadc"

    def get_court_name(self):
        return 'United States Court Of Appeals For The District Of Columbia Circuit'

    def get_court_type(self):
        return 'Federal'

