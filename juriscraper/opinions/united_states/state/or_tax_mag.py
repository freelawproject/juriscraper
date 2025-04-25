import re
from datetime import datetime

from lxml import html

from juriscraper.DeferringList import DeferringList
from juriscraper.opinions.united_states.state import orsc


class Site(orsc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/tax/Pages/tax-magistrate.aspx"
        )
        self.status = "Unublished"
        self.court_code = "p17027coll6"

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
    def fetch_url_json(self, identifier):
        """"""
        url = f"https://ojd.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/{self.court_code}/identi^{identifier}^all^and/title!subjec!descri!dmrecord/title/1024/1/0/0/0/0/json"
        json = self.request["session"].get(url).json()
        print(json)
        if len(json['records'])>0:
            code=json['records'][0]['pointer']
        else:
            code = ""
        return f"https://ojd.contentdm.oclc.org/digital/api/collection/{self.court_code}/id/{code}/download"

    def _process_html(self, start_date: datetime, end_date: datetime):
        start = start_date.year
        end = end_date.year
        for header in self.html.xpath("//div[@id='ctl00_ctl00_MainContentPlaceHolder_PageContentPlaceHolder_PageContentPlaceHolder_RichHtmlField1__ControlWrapper_OregonRichHtmlField']/ul"):
            for row in header.xpath(".//li"):
                date = row.xpath("./b/text()")[0].strip()
                month , day , year = date.split('/')
                dt = f"{day}/{month}/{year}"
                if int(year) >end or int(year)<start: break
                docket=row.xpath("./a[2]/text()")[0].strip()
                docket = docket.replace("\t" , " ")
                pdf = row.xpath("./a[1]/@href")[0]
                name = row.xpath("./text()")[-1]
                name = name.replace(") ","")

                pdf_url_id = self.get_pdf_id(docket, name)
                html_url = f"https://cdm17027.contentdm.oclc.org/digital/collection/p17027coll6/id/{pdf_url_id}/rec"
                response_html = self.get_html_responsd(pdf_url_id)

                self.cases.append(
                    {
                        "date": date,
                        "name": name,
                        "docket": [docket],
                        "url": pdf,
                        "html_url": html_url,
                        "response_html": response_html,
                        "status": "Unpublished"
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


    def get_state_name(self):
        return "Oregon"

    def get_court_name(self):
        return "Oregon Tax Court"

    def get_class_name(self):
        return "or_tax_mag"

    def get_court_type(self):
        return "state"
