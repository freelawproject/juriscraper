import os
from datetime import datetime

import requests

from casemine.casemine_util import CasemineUtil
from casemine.constants import MAIN_PDF_PATH
from juriscraper.OpinionSite import OpinionSite

class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_type = 'opinions'
        self.names = []
        self.urls = []
        self.dates = []
        self.dockets = []
        self.statuses = []
        self.opn_type = []

    def _get_case_names(self):
        # return [e for e in self.html.xpath("//item/description/text()")]
        return self.names

    def _get_download_urls(self):
        # return [html.tostring(e, method="text").decode()for e in self.html.xpath("//item/link")]
        return self.urls

    def _get_case_dates(self):
        # dates = []
        # for date_string in self.html.xpath("//item/pubdate/text()"):
        #     date_only = " ".join(date_string.split(" ")[1:4])
        #     dates.append(
        #         date.fromtimestamp(
        #             time.mktime(time.strptime(date_only, "%d %b %Y"))
        #         )
        #     )
        # return dates
        return self.dates

    def _get_docket_numbers(self):
        # dockets=[]
        # for e in self.html.xpath("//item/title/text()"):
        #     dock=[e.split("|")[0]]
        #     dockets.append(dock)
        # return dockets
        return self.dockets

    def _get_precedential_statuses(self):
        # return ["Published" for _ in range(0, len(self.case_names))]
        return self.statuses

    def _get_opinion_types(self):
        return self.opn_type

    def _process_html(self):
        rows = self.html.xpath("//div[@class='mt-0 pt-0 pb-3 row']")
        for row in rows:
            # print(html.tostring(row,pretty_print=True).decode())
            href = row.xpath('.//a/@href')[0]
            docket = row.xpath('string(.//a)')
            title = row.xpath(
                'string(.//div[@class="col-sm-9 ml-3 ml-sm-0"]/div[@class="row"][1])')
            date = row.xpath(
                'string(.//div[@class="col-sm-9 ml-3 ml-sm-0"]/div[@class="row"][4])')
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            self.names.append(title)
            self.dates.append(datetime.strptime(date,'%m/%d/%Y'))
            self.dockets.append([docket])
            self.urls.append(href)
            self.statuses.append('Published')
            self.opn_type.append(
                self.court_type)  # print(f'{date} {docket} {title} {href}')

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year, end_date.year + 1):
            for month in range(1, 13):
                self.url = f"https://media.cadc.uscourts.gov/{self.court_type}/bydate/{year}/{month}"
                self.parse()
                result = self.html.xpath(
                    "//div[@class='overview']//p[text()='No items found.']/text()")
                if list(result).__len__() != 0 and (year >= end_date.year and month >= end_date.month):
                    print(result[0])
                    break
                self.downloader_executed = False
        return 0

    def get_class_name(self):
        return "cadc"

    def get_court_name(self):
        return 'United States Court of Appeals, District of Columbia Circuit'

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return 'United States District of Columbia Circuit'

    def download_pdf(self, data, objectId):
        pdf_url = data.__getitem__('pdf_url')
        year = int(data.__getitem__('year'))
        court_name = data.get('court_name')
        court_type = data.get('court_type')
        state_name = data.get('circuit')
        opinion_type = data.get('opinion_type')

        path = MAIN_PDF_PATH + court_type + "/" + state_name + "/" + court_name + "/" + str(
            year)
        obj_id = str(objectId)
        download_pdf_path = os.path.join(path, f"{obj_id}.pdf")
        os.makedirs(path, exist_ok=True)
        try:
            response = requests.get(url=pdf_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"},
                                    proxies={"http": "p.webshare.io:9999",
                                             "https": "p.webshare.io:9999"},
                                    timeout=120)
            response.raise_for_status()
            with open(download_pdf_path, 'wb') as file:
                file.write(response.content)
            self.judgements_collection.update_one({"_id": objectId},
                                                  {"$set": {"processed": 0}})
        except requests.RequestException as e:
            print(f"Error while downloading the PDF: {e}")
            self.judgements_collection.update_many({"_id": objectId},
                                                   {"$set": {"processed": 2}})
        return download_pdf_path
