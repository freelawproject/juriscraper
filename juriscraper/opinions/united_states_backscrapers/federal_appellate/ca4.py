from datetime import date, datetime, timedelta

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://pacer.ca4.uscourts.gov/cgi-bin/opinions.pl"
        self.court_id = self.__module__
        td = date.today()
        self.parameters = {
            "CASENUM": "",
            "FROMDATE": (td - timedelta(days=20)).strftime("%m-%d-%Y"),
            "TITLE": "",
            "TODATE": td.strftime("%m-%d-%Y"),
        }
        self.method = "POST"

    def _get_case_names(self):
        if self.only_get_unpublished:
            # No precedential cases (or else dups)
            path = "//tr/td[4][../td[1]/a/text()[contains(., 'U')]]/text()"
        else:
            path = "//tr/td[4]/text()"
        names = []
        for s in self.html.xpath(path):
            if s.strip():
                names.append(s)
        return names

    def _get_download_urls(self):
        if self.only_get_unpublished:
            path = "//tr/td[1][../td[1]/a/text()[contains(., 'U')]]/a/@href"
        else:
            path = "//tr/td[1]/a/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        if self.only_get_unpublished:
            path = "//tr/td[3][../td[1]/a/text()[contains(., 'U')]]/text()"
        else:
            path = "//tr/td[3]/text()"
        return [
            datetime.strptime(date_string.strip(), "%Y/%m/%d").date()
            for date_string in self.html.xpath(path)
        ]

    def _get_docket_numbers(self):
        if self.only_get_unpublished:
            path = "//tr/td[2][../td[1]/a/text()[contains(., 'U')]]//text()"
        else:
            path = "//tr/td[2]//text()"
        docket_numbers = []
        for s in self.html.xpath(path):
            if s.strip():
                docket_numbers.append(s)
        return docket_numbers

    def _get_precedential_statuses(self):
        statuses = []
        # using download link, we can get the statuses
        for download_url in self.download_urls:
            file_name = download_url.split("/")[-1]
            if "u" in file_name.lower():
                statuses.append("Unpublished")
            else:
                statuses.append("Published")
        return statuses

    def _download_backwards(self, dt):
        self.end_date = dt + timedelta(days=6)
        self.resource_org_end_date = date(2007, 7, 31)
        # We only get unpublished docs when we're in a period of time during which we have resource.org docs.
        self.only_get_unpublished = self.end_date < self.resource_org_end_date
        self.parameters["FROMDATE"] = dt.strftime("%m-%d-%Y")
        self.parameters["TODATE"] = self.end_date.strftime("%m-%d-%Y")
        self.html = self._download()
