from datetime import datetime

from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = 'https://www.dir.ca.gov/wcab/wcab-Decisions.htm'
        # self.status = 'Unpublished'

    def _process_html(self, start :int , end :int) -> None:
        for table in self.html.xpath(".//cagov-accordion//div[@class='accordion-body']//table"):
            for rec in table.xpath(".//tr"):
                date = rec.xpath("./td[1]/text()")
                title = rec.xpath("./td[2]")
                if len(date)==0 or len(title)==0 : continue
                if len(date)==0: continue
                date=date[0]
                title=title[0]
                year = int(date[-4:])

                if year < start or year>end: break

                if title.xpath("./p/a/@href"):
                    url = title.xpath("./p/a/@href")[0]
                    text = title.xpath("string(.)").strip()
                else:
                    url = title.xpath("./a/@href")[0]
                    text = title.xpath("string(.)").strip()

                self.cases.append(
                    {
                        "date": date,
                        "docket": [],
                        "name": text,
                        "url": url,
                        "status": "",
                    }
                )



    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start = start_date.year
        end = end_date.year
        self.html  = self._download()
        self._process_html(start,end)

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

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "California Workers Compensation Decisions"

    def get_state_name(self):
        return "California"

    def get_class_name(self):
        return "cal_work_panel"
