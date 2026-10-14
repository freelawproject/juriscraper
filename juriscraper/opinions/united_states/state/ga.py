#  Scraper for Georgia Supreme Court
# CourtID: ga
# Court Short Name: ga

import re
from datetime import date

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import BackscrapeOptions, ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[int]):
    url_template = "https://www.gasupreme.us/opinions/{}-opinions/"
    first_opinion_year = 2017

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = self.url_template.format(date.today().year)
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        links: list[HtmlElement] = self.html.xpath(
            "//li/a[contains(@href, '.pdf')]"
        )
        for link in links:
            url = link.attrib["href"]
            # Expected title content:
            # - "S20A1505, S20A1506. PENDER v. THE STATE"
            # - "S21A0306. BELL v. RAFFENSPERGER"
            title = link.text_content()

            if not bool(title):
                logger.info("No link title for row %s", url)
                continue

            dockets = [
                match.group()
                for match in re.finditer(r"S?\d{2}\w\d{4}", title)
            ]
            if not bool(dockets):
                # Try this only when the <a> doesn't include the docket;
                # if done always, may pick up extra info like
                # "Reinstatement issued" or "Concurral issued"
                parent = link.getparent()
                title = parent.text_content() if parent is not None else ""
                dockets = [
                    match.group()
                    for match in re.finditer(r"S?\d{2}\w\d{4}", title)
                ]

            if not bool(dockets) or "SUMMARY" in title:
                # Skip links to weekly summaries or cases without a docket
                logger.info("Skip summary row %s", title)
                continue

            docket = ", ".join(dockets)
            name = title.split(dockets[-1])[-1].strip("., ")
            # Expected summary content:
            # - "October 19, 2021—SUMMARIES for NOTEWORTHY OPINIONS"
            # - "July 7, 2021"
            # - "February 15, 2021 – SUMMARIES for NOTEWORTHY OPINIONS"
            summary: str = link.xpath(
                ".//parent::li/parent::ul/preceding-sibling::h3[1]/following-sibling::p"
            )[0].text_content()
            # Character separator for dates from summary text could be:
            # - dash: "-"
            # - hyphen: "—"
            # - character U+2013: "–"
            date_str = (
                summary.split("–")[0].split("—")[0].split("-")[0].strip()
            )
            self.cases.append(
                {
                    "date": date_str,
                    "docket": docket,
                    "name": titlecase(name),
                    "url": url,
                }
            )

    @override
    async def _download_backwards(self, year: int) -> None:
        self.url = self.url_template.format(year)
        logger.info("Backscraping for year %s %s", year, self.url)
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        if bool(kwargs.get("backscrape_start")):
            start = int(kwargs["backscrape_start"])
        else:
            start = self.first_opinion_year

        if bool(kwargs.get("backscrape_end")):
            end = int(kwargs["backscrape_end"])
        else:
            end = date.today().year - 1

        if start == end:
            end = start + 1

        self.back_scrape_iterable = range(start, end)

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract the state citation from the document's text

        :param scraped_text: the extracted text
        :return: a dictionary, empty or with expected Citation key
        """
        if (match := re.search(r"\d+ Ga. \d+", scraped_text[:50])) is not None:
            return {"Citation": match.group(0)}
        else:
            return {}
