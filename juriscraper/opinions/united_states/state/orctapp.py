"""
Scraper for Oregon Court of Appeals
CourtID: orctapp
Court Short Name: OR Ct App
Author: William Palin
History:
    - 2023-11-18: Created
"""
import re
from datetime import datetime

import requests
from lxml import html

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/coa/Pages/default.aspx"
        )
        # https://cdm17027.contentdm.oclc.org/digital/search/advanced
        self.cases = []
        self.court_code = "p17027coll5"

    def fetch_url_json(self, identifier):
        """"""
        url = f"https://ojd.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/{self.court_code}/identi^{identifier}^all^and/title!subjec!descri!dmrecord/title/1024/1/0/0/0/0/json"
        json = self.request["session"].get(url).json()
        return f"https://ojd.contentdm.oclc.org/digital/api/collection/{self.court_code}/id/{json['records'][0]['pointer']}/download"

    def get_pdf_id(self,docket : str, name : str):
        u = f"https://cdm17027.contentdm.oclc.org/digital/api/search/collection/p17027coll3!p17027coll5!p17027coll6/searchterm/{docket}/field/all/mode/all/conn/all/order/date/ad/desc/maxRecords/50"
        url_json = self.request["session"].get(u,headers=self.request["headers"]).json()

        if url_json["totalResults"]==0:
            return
        if url_json["totalResults"]==1:
            rec= url_json["items"]
            return rec[0]['itemId']
        for case in url_json["items"]:
            metadata = case["metadataFields"]
            tit = metadata[1]["value"]
            modi_tit = tit.replace('\n',"")

            if(modi_tit == name):
                return case['itemId']


    def get_html_responsd(self,id : str):
        url = f"https://cdm17027.contentdm.oclc.org/digital/api/collections/p17027coll5/items/{id}/false"
        response_html = self.request["session"].get(url,headers=self.request["headers"]).json()
        return response_html['text']

    def _process_html(self, start_date: datetime, end_date: datetime):
        # print(f"inside process html {start_date} , {end_date}")
        for header in self.html.xpath("//h4//a/parent::h4"):
            date_string = header.text_content().strip()
            pdf_url = ""
            if not date_string:
                continue
            if datetime.strptime(date_string.strip(),
                                 "%m/%d/%Y") >= start_date and datetime.strptime(
                date_string.strip(), "%m/%d/%Y") <= end_date:

                ul_elements = header.xpath("./following-sibling::ul[1]")
                for ul in ul_elements:
                    for item in ul.xpath(".//li"):
                        anchors = item.xpath(".//a")
                        if not (len(anchors) > 1):
                            continue
                        text = item.text_content().strip()
                        text=text.replace("\t"," ")
                        url = anchors[0].xpath("./@href")[0]
                        docket = anchors[1].text_content().strip()
                        name = text.split(")", 1)[-1].strip()
                        citation = text.split("(", 1)[0].strip()
                        citation = re.sub(r'\s+', ' ', citation)
                        pdf_url_id = self.get_pdf_id(docket, name)
                        pdf_url = f"https://cdm17027.contentdm.oclc.org/digital/collection/{self.court_code}/id/{pdf_url_id}/rec"
                        response_html = self.get_html_responsd(pdf_url_id)

                        self.cases.append(
                            {
                                "date": date_string,
                                "name": name,
                                "docket": [docket],
                                "url": url,
                                "citation":[citation],
                                "html_url":pdf_url,
                                "response_html":response_html,
                                "status":"Published"
                            }
                        )
                ul_elements = header.xpath("./following-sibling::ul[2]")
                for ul in ul_elements:
                    for item in ul.xpath(".//li"):
                        anchors = item.xpath(".//a")
                        if not (len(anchors) > 1):
                            continue
                        text = item.text_content().strip()
                        text=text.replace("\t"," ")
                        url = anchors[0].xpath("./@href")[0]
                        docket = anchors[1].text_content().strip()
                        name = text.split(")", 1)[-1].strip()
                        citation = text.split("(", 1)[0].strip()
                        citation = re.sub(r'\s+', ' ', citation)
                        pdf_url_id = self.get_pdf_id(docket, name)
                        pdf_url = f"https://cdm17027.contentdm.oclc.org/digital/collection/p17027coll5/id/{pdf_url_id}/rec"
                        response_html = self.get_html_responsd(pdf_url_id)

                        self.cases.append(
                            {
                                "date": date_string,
                                "name": name,
                                "docket": [docket],
                                "url": url,
                                "citation": [citation],
                                "html_url": pdf_url,
                                "response_html": response_html,
                                "status": "Unpublished"
                            }
                        )

                ul_elements = header.xpath("./following-sibling::ul[3]")
                for ul in ul_elements:
                    for item in ul.xpath(".//li"):
                        anchors = item.xpath(".//a")
                        if (len(anchors) > 1):
                            continue
                        case = item.text_content().strip()
                        normalize_string = case.replace("\t", " ")
                        splits = normalize_string.split(" ", 1)
                        docket = splits[0]
                        name = splits[1]

                        self.cases.append(
                            {
                                "date": date_string,
                                "name": name,
                                "docket": [docket],
                                "url": "null",
                                "citation": "",
                                "html_url": "",
                                "response_html": "",
                                "status": "Unpublished"
                            }
                        )



    def _get_download_urls(self):
        """Get download urls

        :return: List URLs
        """

        def fetcher(case):
            if self.test_mode_enabled():
                return case["url"]

            if case["url"] == "null":
                return "null"

            return self.fetch_url_json(case["url"].split("=")[-1][:-4])

        return DeferringList(seed=self.cases, fetcher=fetcher)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        # start_date=datetime(2024,10,1)
        # end_date=datetime(2024,10,9)
        if not self.downloader_executed:
            self.html = self._download()
            # print(html.tostring(self.html,pretty_print=True).decode('UTF-8'))
            self._process_html(start_date,end_date)

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
        return "Oregon Court of Appeals"

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "orctapp"

    def get_state_name(self):
        return "Oregon"
