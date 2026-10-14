from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[str]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[str]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.fisc.uscourts.gov/public-filings"
        self.status = "Published"
        self.back_scrape_iterable = ["placeholder"]
        self.do_backscrape = False
        self.should_have_results = True

    @override
    async def _process_html(self) -> None:
        """Parse HTML into case objects

        :return None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr[td/a]")
        for row in rows:
            filing_name, *_, filename = row.xpath("td/a/text()")
            if "opinion" not in filing_name.lower():
                continue

            docket = row.find("td[4]")
            docket = (
                docket.text_content().strip() if docket is not None else ""
            )
            date_filed: str = row.xpath("td[1]/span/text()")[0]

            if self.skip_record(docket, filename):
                continue

            url: str = row.xpath(".//a/@href")[-1]
            self.cases.append(
                {
                    "date": date_filed.split(",")[-1],
                    "docket": docket,
                    "name": filing_name,
                    "url": url,
                }
            )

            if not isinstance(self.html, HtmlElement):
                raise ValueError(
                    "An HTML document must be downloaded before parsing."
                )
            next_page: list[str] = self.html.xpath(
                "//a[@title='Go to next page']/@href"
            )
            if self.do_backscrape and bool(next_page):
                # Perform download since we are not yielding a site for each
                # element in the backscrape iterable
                self.url = urljoin(
                    (self.url if self.url is not None else ""), next_page[0]
                )
                self.html = await self._download()
                await self._process_html()

    def skip_record(self, docket: str, filename: str) -> bool:
        """Check if a record belongs to 'FISCR'

        :param docket: docket number
        :param filename: opinion title

        :return: True if record should skipped
        """
        return "FISCR" in docket or "FISCR" in filename

    @override
    async def _download_backwards(self, _: str) -> None:
        """Start from second page up to last page

        :return None
        """
        self.do_backscrape = True
        self.url = "https://www.fisc.uscourts.gov/public-filings?page=1"
