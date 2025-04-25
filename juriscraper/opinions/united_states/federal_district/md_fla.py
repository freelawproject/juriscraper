from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        table_tag = self.html.xpath("//table")[1]
        rows = table_tag.xpath("./tr")

        # print(html.tostring(rows,pretty_print=True).decode("utf-8"))
        # with open("/home/gaugedata/Documents/output.html", "w") as file:
        #     file.write(html.tostring(rows,pretty_print=True).decode("utf-8"))
        # print("file is written")
        i=0
        for row in rows:  # Skips the header row
            if i==0:
                i+=1
                continue
            date = row.xpath('./td[1]/text()')[0].strip()
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            # Full docket line: title + docket number
            docket_full = row.xpath('./td[2]//text()')
            title = docket_full[0].strip()
            docket = docket_full[1].strip() if len(docket_full) > 1 else ""

            # Description (text inside <a><b>)
            description = row.xpath('./td[3]/a/b/text()')
            description = description[0].strip() if description else ""

            # PDF URL
            pdf_url = row.xpath('./td[3]/a/@href')
            pdf_url = pdf_url[0] if pdf_url else ""

            # Judge
            judge = row.xpath('./td[4]/text()')
            judge = judge[0].strip() if judge else ""
            self.cases.append({
                "name": title,
                "url": pdf_url,
                "docket": [docket],
                "date": date,
                "judge": [judge],
                "summary":description
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url='https://ecf.flmd.uscourts.gov/cgi-bin/Opinions.pl'
        self.parse()
        return 0

    def get_class_name(self):
        return "md_fla"

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return "11th Circuit"

    def get_court_name(self):
        return "Middle District of Florida"