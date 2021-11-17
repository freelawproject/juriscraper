import re
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.state.va.us/scndex.htm"

    def _get_case_names(self):
        path = "//p[./a[contains(./@href, '.pdf')]]/b/text()"
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = "//p[./a[contains(./@href, '.pdf')]]/a/text()"
        return [
            doc.strip()
            for doc in self.html.xpath(path)
            if doc.strip().isdigit()
        ]

    def _get_case_dates(self):
        dates = []
        path = "//p[./a[contains(./@href, '.pdf')]]/text()"
        pattern = r"^\s*\d{2}/\d{2}/\d{4}"
        for s in self.html.xpath(path):
            date_str = re.findall(pattern, s)
            if len(date_str):
                dates.append(
                    datetime.strptime(date_str[0].strip(), "%m/%d/%Y").date()
                )
        return dates

    def _get_download_urls(self):
        path = "//p[./a[contains(./@href, '.pdf')]]/a[2]/@href"
        urls = [url for url in self.html.xpath(path) if url.endswith(".pdf")]
        return urls

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
