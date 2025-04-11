# Scraper for Oklahoma Attorney General Opinions
# CourtID: oklaag
# Court Short Name: OK
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

from datetime import datetime

import requests
from lxml import html

from casemine.proxy_manager import ProxyManager
from juriscraper.opinions.united_states.state import okla
from sample_caller import logger


class Site(okla.Site):
    # Inherit cleanup_content from Okla
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = datetime.today().year
        self.url = f"https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKAG&year={year}&level=1"
        self.status = "Published"
        self.expected_content_types = ["text/html"]

    def _process_html(self , start_date : datetime , end_date : datetime):
        proxy_manager = ProxyManager()
        proxy = proxy_manager.get_random_proxy()
        cite_html=""
        div=""

        if self.proxy_usage_count >= 4:
            self.proxies = {
                "http": f"http://{proxy[0]}:{proxy[1]}",
                "https": f"http://{proxy[0]}:{proxy[1]}",
            }
            logger.info(f"updated proxy is {self.proxies}")
            self.proxy_usage_count = 0
        for row in self.html.xpath("//div/p['@class=document']")[::-1]:
            if "OK" not in row.text_content() or "EMAIL" in row.text_content():
                continue
            docket, date, name = row.text_content().split(",", 2)
            docket = docket.replace("\xa0"," ")
            url = row.xpath(".//a/@href")[0]

            if datetime.strptime(date.strip(),
                                 "%m/%d/%Y") >= start_date and datetime.strptime(
                date.strip(), "%m/%d/%Y") <= end_date:
                try:
                    print(f"hitting url : {url}")
                    response_html = requests.get(url,
                                                 headers=self.request["headers"],
                                                 proxies=self.proxies)

                    html_content = response_html.text

                    tree = html.fromstring(html_content)
                    cite_text = tree.xpath("//div[@class='tmp-citationizer']")
                    cite_html = html.tostring(cite_text[0], pretty_print=True).decode(
                        "utf-8")
                    div_content = tree.xpath(
                        "//div[@class='container-fluid sized']")
                    if div_content:
                            tmp = div_content[0].xpath(
                                ".//div[@id='opinons-navigation']")
                            if tmp:
                                tmp[0].getparent().remove(
                                    tmp[0])
                            tmp_citationizer = div_content[0].xpath(
                                ".//div[@class='tmp-citationizer']")
                            if tmp_citationizer:
                                tmp_citationizer[0].getparent().remove(
                                    tmp_citationizer[0])

                            div = html.tostring(div_content[0],
                                                pretty_print=True).decode("utf-8")

                except Exception as e:
                    logger.info(f"inside the exception block .......{e}")

                self.cases.append(
                    {
                        "date": date,
                        "name": name,
                        "docket": [docket],
                        "url": "",
                        "citation": "",
                        "html_url": url,
                        "response_html": div,
                        "cite_info_html": cite_html,
                    }
                )
                self.proxy_usage_count +=1
                print("------------------------------------------------------------------------")

    def get_court_name(self):
        return "Opinions of Atty. Gen."

    def get_class_name(self):
        return "oklaag"
