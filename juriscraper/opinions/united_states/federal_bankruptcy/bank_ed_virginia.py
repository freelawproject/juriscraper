from datetime import datetime

from PIL.ImageChops import offset
import certifi
from lxml import html
import requests
from typing_extensions import override

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def check_len(self, field):
        if list(field).__len__()==0:
            return ""
        else:
            return field[0].strip()


    def _process_html(self):
        print(self.html)
            # print(f"{date} || {docket} || {title} || {advisory} || {judge} || {pdfurl}")
            # self.cases.append({
            #     "name":title,
            #     "type": type,
            #     "docket": [docket],
            #     "adversary_number": advisory,
            #     "url":pdfurl, "judge": [judge],
            #     "date":date
            # })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url="https://www-a.vaeb.uscourts.gov/opinions/?v-r=uidl&v-uiId=1"
        self.method="POST"
        self.parameters={
            "csrfToken":"77e4d210-08c9-483a-8a80-1da6635aa724",
            "rpc":[
                {
                    "type":"mSync",
                    "node":'15',
                    "feature":'1',
                    "property":"selected",
                    "value":'1'
                },{
                    "type":"event",
                    "node":'15',
                    "event":"selected-changed",
                    "data":{}
                }
            ],
            "syncId":'9',
            "clientId":'9'
        }
        self.parse()
        return 0

    @override
    def _request_url_post(self, url):
        us_proxy=CasemineUtil.get_us_proxy()
        prox={
            "http":f"{us_proxy.ip}:{us_proxy.port}",
            "https": f"{us_proxy.ip}:{us_proxy.port}",
        }
        resp = requests.get(url='https://www-a.vaeb.uscourts.gov/opinions/',verify=False)
        cookie = resp.headers.get("set-cookie").replace("Path=/opinions; ","").replace("HttpOnly, ","").replace("; Path=/opinions","")

        headers={
            'Host':'www-a.vaeb.uscourts.gov',
            'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0',
            'Accept':'*/*',
            'Accept-Language':'en-US,en;q=0.5',
            'Accept-Encoding':'gzip, deflate, br, zstd',
            'DNT':'1',
            'Sec-GPC':'1',
            'Connection':'keep-alive',
            'Referer':'https://www-a.vaeb.uscourts.gov/opinions/',
            'Cookie':cookie,
            'Sec-Fetch-Dest':'empty',
            'Sec-Fetch-Mode':'cors',
            'Sec-Fetch-Site':'same-origin',
            'Pragma':'no-cache',
            'Cache-Control':'no-cache'
        }
        print(cookie.split(" ")[1].replace("csrfToken=",""))
        data={"csrfToken":{cookie.split(" ")[1].replace("csrfToken=","")},"rpc":[{"type":"publishedEventHandler","node":'33',"templateEventMethodName":"updateSelectedTab","templateEventMethodArgs":[True],"promise":'0'},{"type":"publishedEventHandler","node":'15',"templateEventMethodName":"updateSelectedTab","templateEventMethodArgs":[True],"promise":'0'},{"type":"publishedEventHandler","node":'7',"templateEventMethodName":"setRequestedRange","templateEventMethodArgs":['0','23'],"promise":'0'}],"syncId":'2',"clientId":'2'}
        # data={
        #     "csrfToken":,
        #     "rpc":[{"type":"publishedEventHandler",
        #             "node":'33',
        #             "templateEventMethodName":"updateSelectedTab",
        #             "templateEventMethodArgs":[True],
        #             "promise":0
        #            },{
        #         "type":"publishedEventHandler",
        #         "node":15,
        #         "templateEventMethodName":"updateSelectedTab",
        #         "templateEventMethodArgs":[True],
        #         "promise":0
        #     },
        #            {"type":"publishedEventHandler",
        #             "node":7,
        #             "templateEventMethodName":"setRequestedRange",
        #             "templateEventMethodArgs":[0,23],
        #             "promise":0
        #            }]
        #     ,"syncId":2,"clientId":2}
        # Cookie
        print(cookie)
        self.request["response"] = requests.post(url=url, verify=False,headers=headers,data=data)

    @override
    def _return_response_text_object(self):
        return self.request["response"].text

    def get_class_name(self):
        return "bank_ed_virginia"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "4th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Eastern District of Virginia"