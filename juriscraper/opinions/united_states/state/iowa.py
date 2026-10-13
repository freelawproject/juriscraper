# Scraper for Iowa Supreme Court
# CourtID: iowa
# Court Short Name: iowa
import re
from datetime import date

from lxml.html import HtmlElement
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSite import OpinionSite


class _Case(TypedDict):
    name: str
    docket: str
    date: str
    url: str


class Site(OpinionSite[str]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[str]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.cases: list[_Case] = []
        self.archive = False
        self.back_scrape_iterable = [
            "placeholder"
        ]  # this array can't be empty
        self.url = "https://www.iowacourts.gov/iowa-courts/supreme-court/supreme-court-opinions/"
        self.should_have_results = True

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> HtmlElement:
        if request_dict is None:
            request_dict = {}
        html = await super()._download(request_dict)
        if not isinstance(html, HtmlElement):
            raise TypeError("Expected a downloaded HTML document")
        self.extract_cases(html)
        if self.test_mode_enabled() or self.archive:
            return html

        # Walk over pagination "Next" page(s), if present
        proceed = True
        while proceed:
            next_page_url = self.extract_next_page_url(html)
            if bool(next_page_url):
                logger.info(f"Scraping next page: {next_page_url}")
                html = await self._get_html_tree_by_url(next_page_url)
                self.extract_cases(html)
            else:
                proceed = False
        return html

    @override
    def _get_case_names(self) -> list[str]:
        return [case["name"] for case in self.cases]

    @override
    def _get_download_urls(self) -> list[str]:
        return [case["url"] for case in self.cases]

    @override
    def _get_case_dates(self) -> list[date | None]:
        return [convert_date_string(case["date"]) for case in self.cases]

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)

    @override
    def _get_docket_numbers(self) -> list[str]:
        return [case["docket"] for case in self.cases]

    @override
    async def _download_backwards(self, _: str) -> None:
        """Walk over all "Archive" links on Archive page,
        extract cases dictionaries, and add to self.cases
        """
        self.archive = True
        self.url = f"{self.url}opinions-archive/"
        landing_page_html = await self._download()
        path = '//div[@class="main-content-wrapper"]//a[contains(./text(), "Opinions Archive")]/@href'
        archive_page_urls: list[str] = landing_page_html.xpath(path)
        for archive_page_url in archive_page_urls:
            logger.info(f"Back scraping archive page: {archive_page_url}")
            archive_page_html = await self._get_html_tree_by_url(
                archive_page_url
            )
            self.extract_archive_cases(archive_page_html)

    def extract_cases(self, html: HtmlElement) -> None:
        """Extract case dictionaries from "Recent" html page
        and add them to self.cases
        """
        case_substring = "Case No."
        case_elements: list[HtmlElement] = html.xpath(
            f'//h3[contains(., "{case_substring}")]'
        )
        for case_element in case_elements:
            text = case_element.text_content()
            parts = text.split(":")
            docket = parts[0].replace(case_substring, "").strip()
            name = parts[1].strip()
            date_text: str = case_element.xpath("./following::p[1]")[
                0
            ].text_content()
            date_string = date_text.replace("Filed", "")
            url: str = case_element.xpath("./following::p[2]//a/@href")[0]
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date_string,
                    "url": url,
                }
            )

    def extract_archive_cases(self, html: HtmlElement) -> None:
        """Extract case dictionaries from "Archive" html page
        and add them to self.cases
        """
        path_date = '//div[@class="cms_category_icon_title_row"]'
        date_headers: list[HtmlElement] = html.xpath(path_date)
        for date_header in date_headers:
            text = date_header.text_content()
            date_string = text.replace("- DELETE", "")
            path_cases = './following::div[@class="cms_items"][1]/div[@class="cms_item"]'
            case_containers: list[HtmlElement] = date_header.xpath(path_cases)
            for case_container in case_containers:
                docket_element = case_container.findall(
                    './div[@class="cms_item_icon_title_row"]'
                )[0]
                self.cases.append(
                    {
                        "date": date_string,
                        "url": docket_element.xpath(".//a/@href")[0],
                        "docket": docket_element.text_content().strip(),
                        "name": case_container.findall(
                            './div[@class="cms_item_description"]'
                        )[0]
                        .text_content()
                        .strip(),
                    }
                )

    def extract_next_page_url(self, html: HtmlElement) -> str | None:
        """Return the href url from "Next" pagination element
        if it exists, otherwise return None.
        """
        path = '//div[contains(./@class, "pagination-next-page")]//a/@href'
        elements: list[str] = html.xpath(path)
        return elements[0] if bool(elements) else None

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (?:
               Appeals?\s+from\s+the\s+(?:report\s+of\s+the\s+)?
              | On\s+review\s+of\s+the\s+report\s+of\s+the\s+
              | On\s+application\s+of\s+the\s+
              | On\s+review\s+from\s+the\s+
            )
            (?P<lower_court>[^,.]+?)
            (?:,\s*
                (?P<lower_court_judge>[^,]+?)
                ,\s*judge
            )?
            \.
            """,
            re.X | re.IGNORECASE,
        )

        result: ExtractedMetadata = {}
        if (match := pattern.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

            result["Docket"] = {
                "appeal_from_str": lower_court,
            }

            if bool(match.group("lower_court_judge")):
                lower_court_judge = re.sub(
                    r"\s+", " ", match.group("lower_court_judge")
                ).strip()

                result["OriginatingCourtInformation"] = {
                    "assigned_to_str": lower_court_judge
                }

        return result
