"""
CourtID:	ca6
Court Contact:	WebSupport@ca6.uscourts.gov
"""
from datetime import datetime
from time import strftime

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.string_utils import clean_if_py3, convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.opn.ca6.uscourts.gov/opinions/opinions.php"

    def _get_case_names(self):
        return [
            string.split(" - ")[0]
            for string in self.get_nth_table_cell_data(4)
        ]

    def _get_download_urls(self):
        return self.get_nth_table_cell_data(1, href=True)

    def _get_case_dates(self):
        dates = []
        # return [
        #     convert_date_string(date)
        #     for date in self.get_nth_table_cell_data(3)
        # ]
        for date in self.get_nth_table_cell_data(3):
            dt = convert_date_string(date)
            dates.append(dt)
            comp_date = dt.strftime('%d/%m/%Y')
            res = CasemineUtil.compare_date(comp_date, self.crawled_till)
            if (res == 1):
                self.crawled_till = comp_date
        return dates

    def _get_docket_numbers(self):
        return self.get_nth_table_cell_data(2)

    def _get_precedential_statuses(self):
        statuses = []
        for file_name in self.get_nth_table_cell_data(1, link_text=True):
            if "n" in file_name.lower():
                statuses.append("Unpublished")
            elif "p" in file_name.lower():
                statuses.append("Published")
            else:
                statuses.append("Unknown")
        return statuses

    def get_nth_table_cell_data(self, n, href=False, link_text=False):
        path = "//table/tr/td[%d]" % n
        if href:
            path += "/a/@href"
        elif link_text:
            path += "/a/text()"
        else:
            path += "/text()"

        results = []
        for data in self.html.xpath(path):
            data = clean_if_py3(data).strip()
            if data:
                if(n==2):
                    docket=[]
                    docket.append(data)
                    results.append(docket)
                else:
                    results.append(data)
        return results

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.method = "POST"
        date_obj1 = start_date.strftime('%m/%d/%Y')
        date_obj2 = end_date.strftime('%m/%d/%Y')
        self.parameters = {"FROMDATE": date_obj1, "TODATE": date_obj2,"puid": "$puid"}
        self.parse()
        return 0

    def get_class_name(self):
        return "ca6"

    def get_court_name(self):
        return 'United States Court Of Appeals For The Sixth Circuit'

    def get_court_type(self):
        return 'Federal'
