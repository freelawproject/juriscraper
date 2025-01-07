import re

import requests
from lxml import html
from datetime import datetime
from casemine.proxy_manager import ProxyManager
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from sample_caller import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # self.url = "https://www.oscn.net/decisions/ok/90"
        self.year = datetime.today().year
        self.url = f"https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSSC&year={self.year}&level=1"
        self.status = "Published"
        self.expected_content_types = ["text/html"]
        self._opt_attrs = self._opt_attrs + ["cite_info_html"]
        self.proxy_usage_count = 0


        self.valid_keys.update({
            "cite_info_html"
        })
        self._all_attrs = self._req_attrs + self._opt_attrs

        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_cite_info_html(self):
        return self._get_optional_field_by_id("cite_info_html")

    def fetch_oscn_page_with_proxy(self,url, proxy_host, proxy_port):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(
            f"--proxy-server={proxy_host}:{proxy_port}")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            print(
                f"Opening the page with proxy {proxy_host}:{proxy_port}: {url}")
            driver.get(url)

            time.sleep(30)
            if "OSCN Turnstile" in driver.title:
                print("CAPTCHA not solved. Retry after solving the CAPTCHA.")
                return None
            page_content = driver.page_source
            return page_content

        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        finally:
            driver.quit()

    def _process_html(self):
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

            if len(parts)==2:
                docket , name = parts
                date = ""
            elif len(parts)==4:
                docket, citation, date, name = parts
                citation = citation.replace("\xa0"," ")

            elif len(parts)==3:
                docket, date, name = parts

            docket=docket.replace("\xa0"," ")
            print(f"date of the case is {date}")

            try:
                print(f"getting result of docket {docket}")
                print(f"hitting url {url} for html and cite html")
                time.sleep(4)
                response_html = requests.get(url,
                                             headers=self.request["headers"],
                                             proxies=self.proxies)

                html_content = response_html.text

                tree = html.fromstring(html_content)
                # print(html_content)
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
                                # print(content)
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
                                        if td[0] == 'OPIN':
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

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath("//*[@id='oscn-content']")[0]
        return html.tostring(
            core_element, pretty_print=True, encoding="unicode"
        ).encode("utf-8")

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            self.html = self._download()
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

    def get_court_name(self):
        return "Supreme Court of Oklahoma"

    def get_state_name(self):
        return "Oklahoma"

    def get_class_name(self):
        return "okla"

    def get_court_type(self):
        return "state"
