from juriscraper.opinions.united_states.state import va


class Site(va.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.courts.state.va.us/wpcau.htm"
        self.court_id = self.__module__

    def _get_download_urls(self):
        path = "//p[./a[contains(./@href, '.pdf')]]/a[1]/@href"
        urls = [url for url in self.html.xpath(path) if url.endswith(".pdf")]
        return urls

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)
