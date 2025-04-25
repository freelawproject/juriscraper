from datetime import datetime
import html

from lxml import html

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
        divs = self.html.xpath("//div[@id='TNWBContent_TabContainer1_body']/div")
        i=0
        for div in divs:
            # print(html.tostring(div,pretty_print=True).decode("utf-8"))
            if i==0:
                i += 1
                continue
            judge = div.xpath('./div[@class="primaryTab"]/h5/text()')
            if i==1:
                table_id=f"TNWBContent_TabContainer1_TabPanel1_gvData"
            else:
                table_id = f"TNWBContent_TabContainer1_TabPanel{i}_gvData{i}"
            trs = div.xpath('./div/table[@id="'+table_id+'"]/tr')
            i += 1
            for tr in trs:
                date =  self.check_len(tr.xpath("./td[1]/text()"))
                if not date.__eq__(""):
                    curr_date = datetime.strptime(date,"%m/%d/%Y").strftime("%d/%m/%Y")
                    res = CasemineUtil.compare_date(self.crawled_till,curr_date)
                    if res==1:
                        break
                docket = self.check_len(tr.xpath("./td[2]/a/text()")).split("&")
                pdf_url = self.check_len(tr.xpath("./td[2]/a/@href"))
                adv_no = self.check_len(tr.xpath("./td[3]/text()"))
                title = self.check_len(tr.xpath("./td[4]/text()"))
                summary = self.check_len(tr.xpath("./td[5]/text()"))
                if date.__eq__("") and pdf_url.__eq__(""):
                    continue
                self.cases.append({
                    "name":title,
                    "url":pdf_url,
                    "docket":docket,
                    "date":date,
                    "summary":summary,
                    "adversary_number":adv_no
                })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url="https://www.tnwb.uscourts.gov/TNW/Opinions.aspx"
        self.parse()
        return 0

    def get_class_name(self):
        return "bank_wd_tenn"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "6th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Western District of Tennessee"