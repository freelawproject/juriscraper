# Scraper for US Coast Guard Court of Criminal Appeals

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite
from re import search
from requests.utils import requote_uri


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.mj_cite_regex = "\\d+ *M\\.*J\\.* *\\d+"
        self.wl_cite_regex = "\\d+ *W\\.*L\\.* *\\d+"
        self.current_page = 1
        self.base_url = (
            "https://www.uscg.mil/Resources/Legal/"
            "Court-of-Criminal-Appeals/"
            "CGCCA-Opinions/smdpage15701/{}"
        )
        self._format_url()

    def _format_url(self):
        self.url = self.base_url.format(self.current_page)

    def _process_html(self):
        table_xpath = "//table[@class='Dashboard']//tbody[1]"
        self.html = self.html.xpath(table_xpath)[0]

    def _get_case_dates(self):
        dates_xpath = "//tr//td[3]"
        return [
            convert_date_string(date.text_content())
            for date in self.html.xpath(dates_xpath)
        ]

    def _get_case_names(self):
        names_xpath = "//tr//td[1]"
        names_regex = "^([a-zA-Z ]+ [Vv]\\.? [ ]*[a-zA-Z]+)"
        names = []
        for name in self.html.xpath(names_xpath):
            text = name.text_content()
            m = search(names_regex, text)
            names.append(m.group(0) if m else text)

        return names

    def _get_precedential_statuses(self):
        publish_regex = "((- [a-zA-Z]+)|(\\([a-zA-Z ]+\\)))$"
        statuses = []
        for name in self._get_case_names():
            m = search(publish_regex, name)
            statuses.append(m.group(0).strip("()- ") if m else "PUBLISHED")

        # Parse out any notes on publishing. If nothing assume published.
        return statuses

    def _get_download_urls(self):
        # All of the case urls contain spaces,
        # encoding them to be a good citizen.
        url_xpath = "//tr//td[1]/a/@href"
        return [requote_uri(url) for url in self.html.xpath(url_xpath)]

    def _get_west_citations(self):
        return self._parse_citations(self.wl_cite_regex)

    def _get_neutral_citations(self):
        return self._parse_citations(self.mj_cite_regex)

    def _parse_citations(self, regex):
        cite_list = []
        for name in self._get_case_names():
            m = search(regex, name)
            cite_list.append(m.group(0) if m else None)

        return cite_list
