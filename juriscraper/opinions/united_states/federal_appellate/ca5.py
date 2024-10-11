# History:
# - Long ago: Created by mlr
# - 2014-11-07: Updated by mlr to use new website.

from datetime import datetime

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.ca5.uscourts.gov/rss.aspx?Feed=Opinions&Which=All&Style=Detail"
        self.court_id = self.__module__

    def _get_case_names(self):
        path = "//item/description/text()[2]"
        return [s for s in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "//item/link"
        return [e.tail for e in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "//item/description/text()[5]"
        dates=[]
        for date_string in self.html.xpath(path):
            date_obj = datetime.strptime(date_string, "%m/%d/%Y").date()
            formatted_date = date_obj.strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(formatted_date, self.crawled_till)
            if (res == 1):
                self.crawled_till = formatted_date
            dates.append(date_obj)
        return dates

    def _get_docket_numbers(self):
        path = "//item/description/text()[1]"
        dockets=[]
        for s in self.html.xpath(path):
            docket=[]
            docket.append(s)
            dockets.append(docket)
        return dockets

    def _get_precedential_statuses(self):
        path = "//item/description/text()[3]"
        statuses = []
        for status in self.html.xpath(path):
            if status == "pub":
                statuses.append("Published")
            elif status == "unpub":
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")
        return statuses

    def _get_nature_of_suit(self):
        path = "//item/description/text()[4]"
        return [s for s in self.html.xpath(path)]

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "ca5"

    def get_court_name(self):
        return 'United States Court Of Appeals For The Fifth Circuit'

    def get_court_type(self):
        return 'Federal'

