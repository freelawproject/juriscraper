import re
from datetime import datetime
from typing import Dict, Any

from typing_extensions import override

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.html_utils import set_response_encoding


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.govinfo.gov/wssearch/search"
        self.court_id = self.__module__
        self.court_name = None
        self.json = {}

    def _download(self, request_dict={}):
        """Download the latest version of Site"""
        i = 0
        while True:
            try:
                # Getting new us proxy
                us_proxy = CasemineUtil.get_us_proxy()
                # Setting in proxies header
                self.proxies = {
                    "http": f"{us_proxy.ip}:{us_proxy.port}", "https": f"{us_proxy.ip}:{us_proxy.port}",
                }
                self._request_url_post(self.url)
                self._post_process_response()
                break
            except Exception as ex:
                if str(ex).__contains__("Unable to connect to proxy") or str(ex).__contains__("Forbidden for url"):
                    # print(f"{i} {ex} - hitting with new proxy after 2 minutes")
                    # sleep(30)
                    if i == 100:
                        break
                    else:
                        continue
                else:
                    raise ex
        return self._return_response_text_object()

    @override
    def _request_url_post(self, url):
        """Execute POST request and assign appropriate request dictionary values"""
        self.request["url"] = url
        self.request["response"] = self.request["session"].post(
            url,
            headers=self.request["headers"],
            verify=self.request["verify"],
            data=self.parameters,
            proxies=self.proxies,
            timeout=60,
            **self.request["parameters"],
        )

    @override
    def _post_process_response(self):
        """Cleanup to response object"""
        self.tweak_response_object()
        self.request["response"].raise_for_status()
        set_response_encoding(self.request["response"])

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
            curr_date = datetime.strptime(date_str, "%B %d, %Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
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
            self.parameters = '{"historical":false,"offset":' + str(page) + ',"query":"publishdate:range(' + start_date.strftime("%Y-%m-%d") + ',' + end_date.strftime("%Y-%m-%d") + ')","facetToExpand":"governmentauthornav","facets":{"accodenav":["USCOURTS"],"governmentauthornav":["' + self.court_name + '"]},"filterOrder":["accodenav","governmentauthornav"],"sortBy":"2","pageSize":100}'
            self.parse()
            if list(self.json["resultSet"]).__len__() == 0:
                flag = False
            page += 1
        return 0
