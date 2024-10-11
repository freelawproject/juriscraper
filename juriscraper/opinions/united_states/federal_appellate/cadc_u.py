import re

from lxml import html

from juriscraper.opinions.united_states.federal_appellate import cadc


class Site(cadc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.cadc.uscourts.gov/internet/judgments.nsf/uscadcjudgments.xml"
        self.court_id = self.__module__

    def _get_case_names(self):
        names = []
        for e in self.html.xpath("//item/title/text()"):
            name=str(e.split("|")[1]).strip()
            names.append(name)
        return names

    def _get_download_urls(self):
        urls = []
        for url in self.html.xpath("//item/link"):
            url = html.tostring(url, method="text").decode().replace("\n","")
            urls.append(url)
        return urls

    def _get_docket_numbers(self):
        docs = []
        for e in self.html.xpath("//item/title/text()"):
            doc = str(e.split("|")[0]).strip()
            docs.append([doc])
        return docs

    def _get_precedential_statuses(self):
        return ["Unpublished" for _ in range(0, len(self.case_names))]

    def get_class_name(self):
        return "cadc_u"
