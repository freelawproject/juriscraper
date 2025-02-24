import re
from datetime import datetime
from typing import Dict, Any

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.govinfo.gov/wssearch/search"
        self.court_id = self.__module__
        self.court_name = None
        self.json = {}

    def _download(self, request_dict={}):
        """Download the latest version of Site"""
        self._request_url_post(self.url)
        self._post_process_response()
        return self._return_response_text_object()

    def _process_html(self) -> None:
        self.json = self.html
        if list(self.json["resultSet"]).__len__() == 0:
            return
        for row in self.json["resultSet"]:
            package_id = row["fieldMap"]["packageid"]
            docket = row["line1"].split()[0]
            date_arr = str(row['line2']).split(".")
            # print(row['line2'])
            # print(row['line1'])
            date_finder = date_arr[-1]
            if date_finder.__eq__(""):
                date_finder = date_arr[-2]

            date_str = date_finder.split("day, ")[1].strip(".")
            teaser = ''
            if dict(row["fieldMap"]).keys().__contains__("teaser"):
                teaser = row["fieldMap"]["teaser"]
            # print(teaser)
            # url = f"https://www.govinfo.gov/content/pkg/{package_id}/pdf/{package_id}-0.pdf"
            title = ''
            if dict(row["fieldMap"]).keys().__contains__("title"):
                title = row["fieldMap"]["title"]

            if title.__eq__(''):
                title=str(row["line2"]).split(".")[2]
            # print(title)
            self.cases.append({
                "docket": [docket],
                "name": title,
                "url": row["fieldMap"]["url"],
                "date": date_str,
                "summary": row["line2"],
                "status": "Unknown",
                "teaser": teaser
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return precedential status

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        if re.findall(r"\bPUBLISHED\b", scraped_text):
            status = "Published"
        elif re.findall(r"\bUNPUBLISHED\b", scraped_text):
            status = "Unpublished"
        else:
            status = "Unknown"
        metadata = {"OpinionCluster": {"precedential_status": status, }, }
        return metadata

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.method = "POST"
        self.request["headers"] = {'Host': 'www.govinfo.gov',
                                   'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
                                   'Accept': 'application/json, text/plain, */*',
                                   'Accept-Language': 'en-US,en;q=0.5',
                                   'Accept-Encoding': 'gzip, deflate, br, zstd',
                                   'Connection': 'keep-alive',
                                   'Content-Type': 'application/json', }
        flag = True
        page = 0
        while flag:
            self.parameters = '{"historical":false,"offset":' + str(page) + ',"query":"publishdate:range(' + start_date.strftime("%Y-%m-%d") + ',' + end_date.strftime("%Y-%m-%d") + ') ","facetToExpand":"governmentauthornav","facets":{"accodenav":["USCOURTS"],"governmentauthornav":["' + self.court_name + '"]},"filterOrder":["accodenav","governmentauthornav"],"sortBy":"2","pageSize":100}'
            self.parse()
            if list(self.json["resultSet"]).__len__() == 0:
                flag = False
            page += 1
        return 0
