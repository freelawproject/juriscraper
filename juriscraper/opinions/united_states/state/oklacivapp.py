# Scraper for Oklahoma Court of Civil Appeals
# CourtID: oklacivapp
# Court Short Name: OK
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05
from datetime import datetime

from juriscraper.opinions.united_states.state import okla
import re

import requests
from lxml import html
from casemine.proxy_manager import ProxyManager
from sample_caller import logger

import time

class Site(okla.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSCV&year={self.year}&level=1"

    def _process_html(self, start_date : datetime , end_date : datetime):
        base_url = "https://www.oscn.net/dockets/"
        cite_html=""
        div=""

        for row in self.html.xpath(".//p[@id='document']"):
            pdf_url = "null"
            proxy_manager = ProxyManager()
            proxy = proxy_manager.get_random_proxy()

            if self.proxy_usage_count >= 4:
                self.proxies = {
                    "http": f"http://{proxy[0]}:{proxy[1]}",
                    "https": f"http://{proxy[0]}:{proxy[1]}",
                }
                logger.info(f"updated proxy is {self.proxies}")
                self.proxy_usage_count = 0

            text = row.xpath(".//a/text()")
            url = row.xpath(".//a/@href")[0]
            case = text[0]
            parts = case.split(", ")


            docket, citation, date, name = None, None, None, None

            if len(parts)==4:
                docket, citation, date, name = parts
                citation = citation.replace("\xa0"," ")

            elif len(parts)==3:
                docket, date, name = parts

            docket=docket.replace("\xa0"," ")

            if datetime.strptime(date.strip(),
                                 "%m/%d/%Y") >= start_date and datetime.strptime(
                date.strip(), "%m/%d/%Y") <= end_date:
                try:
                    print(f"getting result of docket {docket}")
                    print(f"hitting url {url} for html and cite html")
                    time.sleep(4)
                    response_html = requests.get(url,
                                                 headers=self.request["headers"],
                                                 proxies=self.proxies)

                    html_content = response_html.text

                    tree = html.fromstring(html_content)

                    cite_text = tree.xpath("//div[@class='tmp-citationizer']")
                    cite_html = html.tostring(cite_text[0], pretty_print=True).decode("utf-8")
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

                            div = html.tostring(div_content[0],pretty_print=True).decode("utf-8")

                            anchor_text = tree.xpath("//div[@id='tmp-style']//a/text()")
                            if anchor_text:
                                case_number = anchor_text[0]
                                if case_number:
                                    print(f"got the case number {case_number}")
                                    full_url = base_url + "GetCaseInformation.aspx?db=Appellate&number=" + case_number
                                    if "; " in case_number:
                                        match = re.search(r'^(\d+);', case_number)
                                        if match:
                                            number = match.group(1)
                                            full_url = base_url + "GetCaseInformation.aspx?db=Appellate&number=" + number


                                    if "SCBD" in case_number:
                                        number_match = re.search(r"SCBD-(\d+)",
                                                                 case_number)
                                        if number_match:
                                            extracted_number = number_match.group(1)
                                            print(f"Extracted number: {extracted_number}")
                                            full_url = base_url + "GetCaseInformation.aspx?db=Appellate&number=" + extracted_number
                                    print(f"getting the content for pdf from the url {full_url}")
                                    get_pdf_html = requests.get(full_url, headers=
                                    self.request["headers"], proxies=self.proxies)
                                    content = get_pdf_html.text
                                    if "OSCN Turnstile" in content or "cf-turnstile" in content:
                                        print("captcha")
                                        content=self.fetch_oscn_page_with_proxy(full_url, proxy[0], proxy[1])


                                    content1 = html.fromstring(content)
                                    table = content1.xpath(
                                        "//table[@class='docketlist ocis']")
                                    if table:
                                        trow = table[0].xpath(".//tbody//tr")
                                        for tr in trow:
                                            td = tr.xpath(".//td[2]//nobr/text()")
                                            dt = tr.xpath(".//td[1]//nobr/text()")
                                            dt_str = str(dt[0]).strip()
                                            if td[0] == 'COPN':
                                                url1 = tr.xpath(
                                                    ".//td[3]//div[@class='description-wrapper']//a[@class='doc-pdf']/@href")[
                                                    0]
                                                pdf_url = base_url + url1
                                            elif td[0] == 'ORDR':
                                                dt_str = dt_str.replace("-", "/")
                                                url1 = tr.xpath(".//td[3]//div[@class='description-wrapper']//a[@class='doc-pdf']/@href")[0]
                                                if dt_str == date:
                                                    print(
                                                        f"Date matches for ORDR row. PDF URL: {url1}")
                                                    pdf_url = base_url + url1

                                    else:
                                        pdf_url = "null"
                                    print(f"got the pdf url {pdf_url}")

                    else:
                        logger.info("no div with calssname container-fluid sized present")
                except Exception as e:
                    logger.info(f"inside the exception block in okla class ..... {e}")

                print("-------------------------------------------------------------------------------------------------------------------")



            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "docket": [docket],
                    "citation": [citation],
                    "url": pdf_url,
                    "cite_info_html":cite_html,
                    "html_url":url,
                    "response_html":div,
                }
            )
            self.proxy_usage_count +=1
    def get_court_name(self):
        return "Okla. Civ. App."

    def get_class_name(self):
        return "oklacivapp"
