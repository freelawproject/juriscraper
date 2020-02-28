from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from datetime import timedelta
from juriscraper.lib.string_utils import clean_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        begin_date = date.strftime(date.today() - timedelta(15), "%m/%d/%Y")
        end_date = date.strftime(date.today(), "%m/%d/%Y")
        self.url = (
            "http://wicourts.gov/supreme/scopin.jsp?"
            "begin_date=%s&end_date=%s&SortBy=date"
        ) % (begin_date, end_date)
        self.court_id = self.__module__

    def _get_case_names(self):
        return [t for t in self.html.xpath("//form/table[1]//tr/td[3]/text()")]

    def _get_download_urls(self):
        return [
            href
            for href in self.html.xpath(
                '//form/table[1]/tr//td[4]/a[contains(.//text(), "PDF")]/@href'
            )
        ]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath("//form/table[1]/tr//td[1]/text()"):
            dates.append(
                date.fromtimestamp(
                    time.mktime(
                        time.strptime(clean_string(date_string), "%b %d, %Y")
                    )
                )
            )
        return dates

    def _get_docket_numbers(self):
        return [e for e in self.html.xpath("//form/table[1]/tr//td[2]/text()")]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
