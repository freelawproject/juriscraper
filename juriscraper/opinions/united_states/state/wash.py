from datetime import date, timedelta

from dateutil.rrule import MONTHLY, rrule

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.start = date.today() - timedelta(days=60)
        self.end = date.today()
        self.url = "http://www.courts.wa.gov/opinions/index.cfm?fa=opinions.processSearch"
        self.method = "POST"

        self.courtLevel = "S"
        self.pubStatus = "All"
        self._set_parameters()
        self.base = "//tr[../tr/td/strong[contains(., 'File Date')]]"
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=date(2014, 2, 1),
                until=date.today(),
            )
        ]

    def _set_parameters(self):
        self.parameters = {
            "courtLevel": self.courtLevel,
            "pubStatus": self.pubStatus,
            "beginDate": self.start.strftime("%m/%d/%Y"),
            "endDate": self.end.strftime("%m/%d/%Y"),
            "SType": "Phrase",
            "SValue": "",
        }

    def _get_case_names(self):
        path = f"{self.base}/td[3]/text()"
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = f"{self.base}/td[2]/a/text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = f"{self.base}/td[1]/text()"
        return [
            convert_date_string(date.strip())
            for date in self.html.xpath(path)
            if date.strip()
        ]

    def _get_download_urls(self):
        path = f"{self.base}/td[2]/a[2]/@href"
        return list(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _download_backwards(self, d):
        self.start = d
        self.end = d + timedelta(days=32)
        self._set_parameters()
        self.html = self._download()
