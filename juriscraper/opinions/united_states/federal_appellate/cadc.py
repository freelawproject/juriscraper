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
            date_obj = datetime.strptime(date_only, "%d %b %Y")

            # Format the datetime object into the desired format
            formatted_date = date_obj.strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(formatted_date, self.crawled_till)
            if (res == 1):
                self.crawled_till = formatted_date
            dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_only, "%d %b %Y"))
                )
            )
        return dates

    def _get_docket_numbers(self):
        return [
            e.split("|")[0] for e in self.html.xpath("//item/title/text()")
        ]

    def _get_precedential_statuses(self):
        return ["Published" for _ in range(0, len(self.case_names))]

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0
