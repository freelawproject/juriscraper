# Scraper for US Coast Guard Court of Criminal Appeals

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite
from requests.utils import requote_uri


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
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
        names_xpath = "//tr//td[2]"
        return [name.text_content() for name in self.html.xpath(names_xpath)]

    def _get_precedential_statuses(self):
        rows_xpath = "//tr//td[1]"
        return ["Published"] * (len(self.html.xpath(rows_xpath)))

    def _get_download_urls(self):
        # All of the case urls contain spaces,
        # encoding them to be a good citizen.
        url_xpath = "//tr//td[1]/a/@href"

        return [requote_uri(url) for url in self.html.xpath(url_xpath)]
