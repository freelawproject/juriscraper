from datetime import datetime
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.nebraska.gov/apps-courts-epub/public/supreme"
        )
        self.status='Published'

    def _process_html(self,*args, **kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        count = 0
        for row in self.html.xpath(".//table[@class='table table-striped table-bordered table-condensed citation-sortable docket-sortable']"):
            for case in row.xpath(".//tbody/tr"):
                date = case.xpath(".//td[1]/text()")[0].strip()
                case_date = datetime.strptime(date, "%m/%d/%Y").date()

                if start_date <= case_date <= end_date:
                    docket = case.xpath(".//td[2]/text()")
                    cleaned_text = " ".join(
                    text.strip() for text in docket if text.strip())
                    dockets = cleaned_text.strip().split(' ')
                    name = case.xpath(".//td[3]/text()")[0].strip()
                    citation=case.xpath(".//td[4]/text()")[0].strip()
                    url = case.xpath(".//td[5]/a/@href")[0].strip()
                    count += 1

                    self.cases.append(
                        {
                            "date": date,
                            "docket": dockets,
                            "name": name,
                            "citation": [citation.replace('   ',' ')],
                            "url": url,
                        }
                    )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            self.html = self._download()
            self._process_html(start_date=start_date.date(),end_date=end_date.date())

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

    def get_class_name(self):
        return "neb_sup_all_op"

    def get_state_name(self):
        return "Nebraska"

    def get_court_name(self):
        return "Supreme Court of Nebraska"
