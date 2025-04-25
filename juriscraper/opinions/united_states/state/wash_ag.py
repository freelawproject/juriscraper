from datetime import datetime

from lxml import html
import requests

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//div[@class="view-content"]/div[@class="views-row"]')
        for row in rows:
            docket = row.xpath('.//div[@class="views-field views-field-field-opinion-date"]/div[@class="field-content"]/text()[1]')[0].strip().split('>')[0].strip()
            date = row.xpath('.//div[@class="views-field views-field-field-opinion-date"]//time/text()')[0]
            title = row.xpath('.//div[@class="views-field views-field-title"]//a/text()')[0].strip()
            relative_url = row.xpath('.//div[@class="views-field views-field-title"]//a/@href')[0]
            i = 0
            response = None
            while True:
                try:
                    us_proxy = CasemineUtil.get_us_proxy()
                    prox=f"{us_proxy.ip}:{us_proxy.port}"
                    response = requests.get(url=relative_url,proxies={"http":prox,"https":prox})
                    # print(response.status_code)
                    break
                except Exception as ex:
                    if str(ex).__contains__("Unable to connect to proxy") or str(ex).__contains__("Forbidden for url") or str(ex).__contains__("Read timed out"):
                        print("hitting again")
                        i += 1
                        if i == 100:
                            break
                        else:
                            continue
                    else:
                        raise ex

            response_html = ''
            if response is not None:
                response_html = response.text
                html_tree = self._make_html_tree(response_html)
                response_html = html_tree.xpath("//section[@id='block-atg-content']")[0]
                content = html.tostring(response_html,pretty_print=True).decode("utf-8")
            self.cases.append({
                "date":date,
                "docket":[docket],
                "name":title,
                "url":'',
                "html_url":relative_url,
                "response_html":content
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year, end_date.year + 1):
            self.url = f"https://www.atg.wa.gov/ago-opinions/year/{year}"
            self.parse()
            self.downloader_executed = False
        return 0

    def get_class_name(self):
        return "wash_ag"

    def get_court_type(self):
        return 'state'

    def get_state_name(self):
        return "Washington"

    def get_court_name(self):
        return "Opinions of the Washington Attorney General"