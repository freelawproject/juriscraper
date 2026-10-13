# Scraper for Iowa Appeals Court
# CourtID: iowactapp
# Court Short Name: iowactapp

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker

from . import iowa


class Site(iowa.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[str]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.iowacourts.gov/iowa-courts/court-of-appeals/court-of-appeals-court-opinions/"

    @override
    async def _download_backwards(self, _: str) -> None:
        """Overriding this method from parent iowa class because the
        site link/page structure for archived Court of Appeals opinions
        is different than that of Archived Supreme Court opinions
        """
        self.archive = True
        landing_page_html = await self._download()
        path_filter_class = 'contains(./@class, "nav-link")'
        path_filter_text = (
            'contains(./text(), "Archived Court of Appeals Opinions")'
        )
        path = f"//a[{path_filter_class}][{path_filter_text}]/@href"
        archive_page_urls: list[str] = landing_page_html.xpath(path)
        for archive_page_url in archive_page_urls:
            logger.info(f"Back scraping archive page: {archive_page_url}")
            archive_page_html = await self._get_html_tree_by_url(
                archive_page_url
            )
            self.extract_archive_cases(archive_page_html)

    @override
    def extract_archive_cases(self, html: HtmlElement) -> None:
        """Overriding this method from parent iowa class because the
        html structure for archived Court of Appeals opinion pages is
        different than that of Archived Supreme Court opinion pages
        """
        path_date = '//h2[contains(., "Summaries")]'
        date_headers: list[HtmlElement] = html.xpath(path_date)
        for date_header in date_headers:
            text = date_header.text_content()
            date_string = text.replace("Summaries", "").replace("Opinion", "")
            path_case_rows = "./following::table[1]//tr[.//a]"
            case_rows: list[HtmlElement] = date_header.xpath(path_case_rows)
            for case_row in case_rows:
                self.cases.append(
                    {
                        "date": date_string,
                        "url": case_row.xpath("./td[1]//a/@href")[0],
                        "name": case_row.findall("./td[2]")[0]
                        .text_content()
                        .strip(),
                        "docket": case_row.findall("./td[1]")[0]
                        .text_content()
                        .strip(),
                    }
                )
