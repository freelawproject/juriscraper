from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base="https://ecf.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM={}&theYY={}&A1=Get+Opinions"

    def make_url(self, month: int , year : int) -> str:
        return self.base.format(month, year)

    def _process_html(self) -> None:
        pre = self.html.xpath("//pre")[0]
        current_date = None
        for elem in pre.iterchildren():
            if elem.tag == 'b':
                date_text = elem.text_content().strip("[] ")
                current_date = date_text
            elif elem.tag == 'a':
                doc=elem.text_content()

                if "New Search" in doc: continue
                url = elem.get('href')
                case_text = elem.tail.strip() if elem.tail else ""
                if "P" in doc :
                    doc=doc.replace("P.pdf", "")
                    status = "Published"
                else :
                    doc=doc.replace("U.pdf", "")
                    status = "Unpublished"

                name = case_text.split('\n')[0]
                dt = name.split('  ')[0]
                title = name.replace(dt,"").strip()

                self.cases.append({
                    "name": title,
                    "url": url,
                    "docket": [f"{doc[:2]}-{doc[2:]}"],
                    "date": current_date,
                    "status":status,
                    "summary":case_text
                   })



    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start = str(start_date.date())
        end = str(end_date.date())

        start_month =int(start.split('-')[1])
        end_month =int(end.split('-')[1])

        start_year = int(start.split('-')[0])
        end_year= int(end.split('-')[0])
        month = 0o1

        if start_year < end_year:
            while start_month<13:
                self.url = self.make_url(start_month,start_year)
                self.html = self._download()
                if "NO OPINIONS FOUND..." in self.html:
                    print("no records found")
                    continue
                self._process_html()
                start_month += 1
            while month < end_month+1:
                self.url = self.make_url(month, end_year)
                self.html = self._download()
                if "NO OPINIONS FOUND..." in self.html:
                    print("no records found")
                    continue
                self._process_html()
                month += 1

        else:
            while start_month < end_month+1:
                self.url = self.make_url(start_month,start_year)
                self.html = self._download()
                if "NO OPINIONS FOUND..." in self.html:
                    print("no records found")
                    continue
                self._process_html()
                start_month += 1



        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()

        return 0

    def get_class_name(self):
        return "b_ca8"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "8th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court of Appeal for the Eighth Circuit"
