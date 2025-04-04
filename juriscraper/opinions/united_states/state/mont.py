# Author: Michael Lissner
# Date created: 2013-06-03
# Date updated: 2020-02-25
from datetime import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://juddocumentservice.mt.gov/getDailyOrders"
        self.download_base = (
            "https://juddocumentservice.mt.gov/getDocByCTrackId?DocId="
        )
        self.expected_content_types = None


    def _process_html(self):
        for row in self.html:
            name = row['title']
            docket = row['caseNumber']
            date = row['fileDate']
            url = f"{self.download_base}{row['cTrackId']}"
            summary = row['documentDescription']

            if docket.startswith("DA"):
                nature = "Direct Appeal"
            elif docket.startswith("OP"):
                nature = "Original Proceeding"
            elif docket.startswith("PR"):
                nature = "Professional Regulation"
            elif docket.startswith("AF"):
                nature = "Administrative File"
            else:
                nature = "Unknown"
            self.cases.append({
                "date": date,
                "docket": [docket],
                "name": name,
                "url": url,
                "summary":summary,
                "nature_of_suit":nature,
                "status": "Published",
            })

    def filter_records_by_date_range(self,data, start_date: datetime, end_date: datetime):
        print(f"{start_date} , {end_date}")
        filtered_records = [
            record for record in data
            if start_date <= datetime.strptime(record["fileDate"],
                                               "%Y-%m-%d %H:%M:%S.%f") <= end_date
        ]
        return filtered_records

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            response = self._download()
            self.html=self.filter_records_by_date_range(response,start_date, end_date)
            print(self.html)
            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "mont"

    def get_state_name(self):
        return "Montana"

    def get_court_name(self):
        return "Supreme Court of Montana"
