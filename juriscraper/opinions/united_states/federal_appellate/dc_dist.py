import os
import re
from datetime import datetime

import requests
from lxml import html

from casemine.constants import MAIN_PDF_PATH
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def _process_html(self):
        rows = self.html.xpath("//table[@id='ts']/tbody/tr")
        for row in rows:
            # print(html.tostring(row,pretty_print=True).decode())
            date = row.xpath("string(./td[1])")
            docket_title = html.tostring(row.xpath("./td[2]")[0],
                                         pretty_print=True).decode().replace(
                "<td>", "").replace("</td>", "").split("<br>")
            docket = docket_title[0].replace("Civil Action No.", "").replace(
                "Criminal No.", "").replace("Misc. No.", "").strip()
            title = docket_title[1].strip().replace("\n", "")

            type_judge = str(row.xpath("string(./td[3])")).split("by")
            judge = type_judge[1].strip()
            doc_type = type_judge[0].strip()

            regex_for_type = r"\((.*?)\)"
            match = re.search(pattern=regex_for_type, string=doc_type)
            opn_type = ''
            if match:
                opn_type = match.group(1)

            link = row.xpath("string(.//a/@href)")
            self.cases.append(
                {"date": date, "docket": [docket], "judge": [judge],
                    "url": link, "name": title, "status": "published",
                    "opinion_type": opn_type})  # print(f'{date} {docket} {title} {type_judge}')

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year, end_date.year + 1):
            self.url = f'https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?{year}'
            print(self.url)
            self.parse()
            self.downloader_executed = False
        return 0

    def get_class_name(self):
        return "dc_dist"

    def get_court_name(self):
        return 'District Court'

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return 'United States District of Columbia Circuit'

    def download_pdf(self, data, objectId):
        pdf_url = data.__getitem__('pdf_url')
        year = int(data.__getitem__('year'))
        court_name = data.get('court_name')
        court_type = data.get('court_type')
        state_name = data.get('state')
        opinion_type = data.get('opinion_type')

        path = MAIN_PDF_PATH + court_type + "/" + state_name + "/" + court_name + "/" + str(year)
        obj_id = str(objectId)
        download_pdf_path = os.path.join(path, f"{obj_id}.pdf")
        os.makedirs(path, exist_ok=True)
        try:
            response = requests.get(url=pdf_url,
                                    headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"},
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
            self.judgements_collection.update_many({"_id": objectId}, {
                "$set": {"processed": 2}})
        return download_pdf_path
