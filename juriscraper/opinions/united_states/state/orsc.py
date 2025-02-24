"""
History:
 - 2014-08-05: Adapted scraper to have year-based URLs.
 - 2023-11-18: Fixed and updated
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
import re
from datetime import datetime

from lxml import html

class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/sc/Pages/default.aspx"
        )
        self.court_code = "p17027coll3"

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
        url = f"https://cdm17027.contentdm.oclc.org/digital/api/collections/{self.court_code}/items/{id}/false"
        response_html = self.request["session"].get(url,headers=self.request["headers"]).json()
        return response_html['text']

    def _process_html(self, start_date: datetime, end_date: datetime):
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
                        url = anchors[0].xpath("./@href")[0]
                        docket = anchors[1].text_content().strip()
                        name = text.split(")", 1)[-1].strip()
                        citation = text.split("(", 1)[0].strip()
                        citation = re.sub(r'\s+', ' ', citation)
                        pdf_url_id = self.get_pdf_id(docket, name)

                        if (pdf_url_id is not None):
                            pdf_url = f"https://cdm17027.contentdm.oclc.org/digital/collection/{self.court_code}/id/{pdf_url_id}/rec"
                            response_html = self.get_html_responsd(pdf_url_id)
                        else:
                            pdf_url=""
                            response_html = ""


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



    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
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

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Oregon"

    def get_court_name(self):
        return "Supreme Court of Oregon"

    def get_class_name(self):
        return "orsc"


