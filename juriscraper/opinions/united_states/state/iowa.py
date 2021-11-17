# Scraper for Iowa Supreme Court
# CourtID: iowa
# Court Short Name: iowa

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.cases = []
        self.archive = False
        self.back_scrape_iterable = [
            "placeholder"
        ]  # this array can't be empty
        self.url = "https://www.iowacourts.gov/iowa-courts/supreme-court/supreme-court-opinions/"

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        self.extract_cases(html)
        if self.test_mode_enabled() or self.archive:
            return html

        # Walk over pagination "Next" page(s), if present
        proceed = True
        while proceed:
            next_page_url = self.extract_next_page_url(html)
            if next_page_url:
                logger.info(f"Scraping next page: {next_page_url}")
                html = self._get_html_tree_by_url(next_page_url)
                self.extract_cases(html)
            else:
                proceed = False

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_dates(self):
        return [convert_date_string(case["date"]) for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _download_backwards(self, _):
        """Walk over all "Archive" links on Archive page,
        extract cases dictionaries, and add to self.cases
        """
        self.archive = True
        self.url = f"{self.url}opinions-archive/"
        landing_page_html = self._download()
        path = '//div[@class="main-content-wrapper"]//a[contains(./text(), "Opinions Archive")]/@href'
        for archive_page_url in landing_page_html.xpath(path):
            logger.info(f"Back scraping archive page: {archive_page_url}")
            archive_page_html = self._get_html_tree_by_url(archive_page_url)
            self.extract_archive_cases(archive_page_html)

    def extract_cases(self, html):
        """Extract case dictionaries from "Recent" html page
        and add them to self.cases
        """
        case_substring = "Case No."
        case_elements = html.xpath(f'//h3[contains(., "{case_substring}")]')
        for case_element in case_elements:
            text = case_element.text_content()
            parts = text.split(":")
            docket = parts[0].replace(case_substring, "").strip()
            name = parts[1].strip()
            date_text = case_element.xpath("./following::p[1]")[
                0
            ].text_content()
            date_string = date_text.replace("Filed", "")
            url = case_element.xpath("./following::p[2]//a/@href")[0]
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date_string,
                    "url": url,
                }
            )

    def extract_archive_cases(self, html):
        """Extract case dictionaries from "Archive" html page
        and add them to self.cases
        """
        path_date = '//div[@class="cms_category_icon_title_row"]'
        for date_header in html.xpath(path_date):
            text = date_header.text_content()
            date_string = text.replace("- DELETE", "")
            path_cases = './following::div[@class="cms_items"][1]/div[@class="cms_item"]'
            for case_container in date_header.xpath(path_cases):
                docket_element = case_container.xpath(
                    './div[@class="cms_item_icon_title_row"]'
                )[0]
                self.cases.append(
                    {
                        "date": date_string,
                        "url": docket_element.xpath(".//a/@href")[0],
                        "docket": docket_element.text_content().strip(),
                        "name": case_container.xpath(
                            './div[@class="cms_item_description"]'
                        )[0]
                        .text_content()
                        .strip(),
                    }
                )

    def extract_next_page_url(self, html):
        """Return the href url from "Next" pagination element
        if it exists, otherwise return False.
        """
        path = '//div[contains(./@class, "pagination-next-page")]//a/@href'
        elements = html.xpath(path)
        return elements[0] if elements else False
