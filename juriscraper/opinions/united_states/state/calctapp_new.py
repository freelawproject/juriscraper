import \
    re
from datetime import date, datetime, timedelta

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skipped_word=['Supreme Court','Appellate Division']
        self.set_status="Published"
        self.set_url_keyword='publishedcitable-opinions'
        self.pattern=r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        self.opn_type="Opinion"

    def _process_html(self):
        list = self.html.xpath("//ul[@class='stack']/li")
        i = 1
        for li in list:
            court = str(li.xpath("string(.//div[@class='result-excerpt__brow-notation'])")).strip()
            if court.__contains__(self.skipped_word[0]) or court.__contains__(self.skipped_word[1]):
                continue
            if court.__contains__('1st District Court of Appeal'):
                court='1st App. Dist.'
            elif court.__contains__('2nd District Court of Appeal'):
                court = '2nd App. Dist.'
            elif court.__contains__('3rd District Court of Appeal'):
                court = '3rd App. Dist.'
            elif court.__contains__('4th District Court of Appeal, Division One'):
                court = '4th App. Dist. Div. 1'
            elif court.__contains__('4th District Court of Appeal, Division Two'):
                court = '4th App. Dist. Div. 2'
            elif court.__contains__('4th District Court of Appeal, Division Three'):
                court = '4th App. Dist. Div. 3'
            elif court.__contains__('5th District Court of Appeal'):
                court = '5th App. Dist.'
            elif court.__contains__('6th District Court of Appeal'):
                court = '6th App. Dist.'

            docket = li.xpath("string(.//span[@class='result-excerpt__brow-primary'])").strip()
            date = li.xpath("string(.//span[@class='result-excerpt__brow-secondary'])").strip()
            curr_date = datetime.strptime(date, "%B %d, %Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            title = li.xpath("string(.//div[@class='result-excerpt__title'])").strip()
            name = re.split(self.pattern, title)[0].strip()
            pdf_url = li.xpath("string(.//a[text()='PDF']/@href)").strip()
            self.cases.append({
                "date": date,
                "docket": [docket],
                "url": pdf_url,
                "name": name,
                "status": self.set_status,
                "division":court,
                "opinion_type":self.opn_type,
            })
            i += 1

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        flag = True
        page = 0
        while flag:
            self.url = f"https://courts.ca.gov/opinions/{self.set_url_keyword}?field_opinion_source_target_id=All&field_case_number_plain_value=&title=&items_per_page=200&page={page}"
            self.parse()
            page += 1
            self.downloader_executed = False
            if str(self.html.xpath("string(//div[@class='stack content'])")).__contains__("No results found. Please try another search."):
                flag = False
        return 0

    def get_class_name(self):
        return "calctapp_new"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "California"

    def get_court_name(self):
        return "California Court of Appeals"
