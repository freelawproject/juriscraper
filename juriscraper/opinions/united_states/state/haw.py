# Author: Michael Lissner
# Date created: 2013-05-23

from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        year = date.today().year
        self.url = (
            "http://www.courts.state.hi.us/opinions_and_orders/opinions?yr=%s"
            % year
        )
        self.back_scrape_iterable = range(2010, year + 1)
        self.court_id = self.__module__
        self.target_id = "S.Ct"
        self.cases = []

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self.extract_cases_from_table(html)
        return html

    def extract_cases_from_table(self, html):
        path_rows = '//div[@id="table-content"]/table/tbody/tr'
        path_target = "./td[2]/div/span/text()"
        for row in html.xpath(path_rows):
            court = row.xpath(path_target)
            if court and court[0].strip() == self.target_id:
                case_text = row.xpath(
                    "./td[4]/p/text() | ./td[4]/p/span/text()"
                )[0]
                court_text = row.xpath("./td[5]/text()")
                self.cases.append(
                    {
                        "url": row.xpath("./td[3]/a/@href")[0],
                        "date": row.xpath("./td[1]/text()")[0],
                        "name": case_text.split(" (")[0],
                        "docket": row.xpath("./td[3]/a/text()")[0],
                        "court": court_text[0] if court_text else False,
                    }
                )

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_case_dates(self):
        return [convert_date_string(case["date"]) for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_lower_courts(self):
        return [case["court"] for case in self.cases]

    def _download_backwards(self, year):
        if int(year) < 2010:
            raise Exception("the haw portal does not include pre-2010 cases")

        self.url = (
            "http://www.courts.state.hi.us/opinions_and_orders/opinions?yr=%s"
            % year
        )
        self.html = self._download()

        # Loop over all pages
        pages = self.html.xpath('//a[@class="page-numbers"]/text()')
        if pages:
            last_page = int(pages[-1])
            for page in range(2, last_page + 1):
                self.url = (
                    "http://www.courts.state.hi.us/opinions_and_orders/opinions/page/%d?yr=%s"
                    % (page, year)
                )
                self.html = self._download()
