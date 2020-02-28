from juriscraper.opinions.united_states.state import va


class Site(va.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.courts.state.va.us/wpcap.htm"
        self.court_id = self.__module__

    def _get_download_urls(self):
        path = "//p[./a[contains(./@href, '.pdf')]]/a[1]/@href"
        urls = [url for url in self.html.xpath(path) if url.endswith(".pdf")]
        return urls
