from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//div[contains(@class, "views-row")]')
        for case in rows:
            title_text = case.xpath('.//div[contains(@class,"views-field-body")]//p[1]//text()')
            title = title_text[0].strip() if title_text else ""
            # Extract docket number from title (assuming format "Docket Title")
            docket = title.split(' ', 1)[0] if title else ""
            summary = " ".join(case.xpath('.//div[contains(@class,"views-field-body")]//p[position()>1]//text()')).strip()
            pdf_url = case.xpath('.//div[contains(@class,"views-field-field-opinion-file")]//a/@href')
            pdf_url = pdf_url[0] if pdf_url else ""
            judge = case.xpath('.//div[contains(@class,"views-field-field-opinion-judge")]//a/text()')
            judge = judge[0].strip() if judge else ""
            date = case.xpath('.//span[contains(@class, "date-display-single")]/text()')
            date = date[0].strip() if date else ""
            curr_date = datetime.strptime(date, "%A, %B %d, %Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            # print(f"{date} || {title.replace(docket,'').strip()} || {docket} || {judge} || {pdf_url} || {summary}")
            self.cases.append({
                "name": title.replace(docket,'').strip(),
                "docket": [docket],
                "summary": summary,
                "url": pdf_url,
                "judge": [judge],
                "date": date
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year,end_date.year+1):
            page = 0
            flag=True
            while flag:
                self.url=f'https://www.wied.uscourts.gov/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={year}&field_opinion_judge_tid=All&page={page}'
                self.parse()
                last_page_div = self.html.xpath("//ul[@class='pager']/li[contains(@class, 'pager__item--next')]")
                if list(last_page_div).__len__()==0:
                    flag=False
                self.downloader_executed=False
                page+=1
        return 0

    def get_class_name(self):
        return "ed_wis"

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return "7th Circuit"

    def get_court_name(self):
        return "Eastern District of Wisconsin"