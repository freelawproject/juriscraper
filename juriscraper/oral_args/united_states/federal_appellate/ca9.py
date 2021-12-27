"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OralArgumentSiteLinearWebDriven import (
    OralArgumentSiteLinearWebDriven,
)


class Site(OralArgumentSiteLinearWebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/media/"
        self.uses_selenium = True

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            return super()._download(request_dict)
        else:
            self.initiate_webdriven_session()
            return super()._download(request_dict)

    def _process_html(self):
        path = "//table[@id='search-results-table']//tr"
        rows = self.html.xpath(path)

        for row in rows:
            # In the last row there is not valid data, but a one celled table footer
            cells = row.xpath(".//td")
            if len(cells) != 7:
                continue
            # Skip cases where the URL includes spaces
            url = get_row_column_links(row, 6)
            if " " in url:
                logger.warning(f"URL includes spaces: {url}")
                continue

            self.cases.append(
                {
                    "date": get_row_column_text(row, 5),
                    "docket": get_row_column_text(row, 2),
                    "judge": get_row_column_text(row, 3),
                    "name": get_row_column_text(row, 1),
                    "url": url,
                }
            )

    def _get_download_urls(self):
        """Links from the root page go to a second page where the real links
        are posted.
        """

        def fetcher(case_url):
            if self.test_mode_enabled():
                return "No links fetched during tests."
            else:
                # Creates session to load page, grabs the link and returns it.
                self.webdriver.get(case_url)
                path_to_audio_file = (
                    "//*[@class='av-content']//span[@id='download']/a"
                )
                try:
                    self.wait_for_id("download")
                    audio_file = self.find_element_by_xpath(path_to_audio_file)
                    url = audio_file.get_property("href")
                except IndexError:
                    # The URL wasn't found, so something is wrong and we'll have to
                    # fix it in the _post_parse() method.
                    url = ""
                    logger.warning(
                        f"Audio file link not found at page: {case_url}"
                    )
                return url

        return [fetcher(case["url"]) for case in self.cases]
