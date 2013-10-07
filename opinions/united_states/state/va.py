from juriscraper.GenericSite import GenericSite
from datetime import datetime
import re

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.courts.state.va.us/wpcap.htm'
        self.parameters = {}
        self.method = 'GET'

    def _get_case_names(self):
        path = "//p/b/text()"
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = "//p/a/text()"
        return [doc for doc in self.html.xpath(path) if doc.isdigit()]

    def _get_case_dates(self):
        rv = []
        path = "//p/text()"
        pattern = r"\d{2}/\d{2}/\d{4}"
        for str in self.html.xpath(path):
            date = re.findall(pattern, str)
            if(len(date)):
                rv.append(datetime.strptime(date[0], '%m/%d/%Y').date())
        return rv[1:]

    def _get_download_urls(self):
        path = "//p/a/@href"
        return [url for url in self.html.xpath(path) if url.endswith('.pdf')]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
