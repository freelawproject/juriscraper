"""
Scraper for South Carolina Attorney General
CourtID: scag
Court Short Name: SC AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.scag.gov/opinions/opinions-archive/"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//div[@class='opinion-link']"):
            date = row.xpath(".//p")[0].text_content().strip()
            url = row.xpath(".//a/@href")
            name = row.xpath(".//a/h2/text()")[0]
            self.cases.append(
                {"url": url[0], "docket": "", "name": name, "date": date}
            )

    def _get_download_urls(self) -> DeferringList:
        """Get urls using a deferring list."""

        def get_download_url(link: str) -> str:
            """Abstract out the download link"""
            if self.test_mode_enabled():
                return link
            html = self._get_html_tree_by_url(link)
            return html.xpath(".//a[contains(@href, '.pdf')]/@href")[2]

        links = [case["url"] for case in self.cases]
        return DeferringList(seed=links, fetcher=get_download_url)
