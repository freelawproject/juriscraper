# History:
# - Long ago: Created by mlr
# - 2014-11-07: Updated by mlr to use new website.
# - 2025-08-26: Updated by lmanzur to use OpinionSiteLinear and extract lower court
# - 2026-08-05: Updated by grossir for the website redesign, see #2062

import re
from datetime import date, datetime
from urllib.parse import urlencode, urljoin

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # https://www.ca5.uscourts.gov/opinions?group=flat&pageSize=1000&quick=30
    base_url = "https://www.ca5.uscourts.gov/opinions/results"
    # Oldest opinion available on the court's search
    first_opinion_date = datetime(1992, 3, 19)
    days_interval = 90
    # Biggest page the endpoint will render. The court's busiest year had
    # ~3,200 opinions, so a `days_interval` sized range fits in a single
    # page; `_download_backwards` still follows the pager if it doesn't
    page_size = 1000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # `quick=30` selects the last 30 days of opinions and orders
        self.url = self.build_url({"quick": 30})
        self.should_have_results = True
        self.make_backscrape_iterable(kwargs)

    def build_url(self, params: dict) -> str:
        """Build a results URL, keeping the shared parameters in one place

        :param params: filters particular to this query, such as the `quick`
            shorthand or a `from` / `to` date range
        :return: the full URL
        """
        params = {"group": "flat", "pageSize": self.page_size, **params}
        return f"{self.base_url}?{urlencode(params)}"

    def _process_html(self) -> None:
        for row in self.html.xpath("//a[contains(@class, 'oprow')]"):
            docket = row.xpath("span[@class='oprow__docket']/text()")
            name = row.xpath("span[@class='oprow__caption']/text()")
            date_filed = row.xpath("span[@class='oprow__date']/text()")
            url = row.xpath("@href")

            if not (docket and name and date_filed and url):
                logger.error(
                    "ca5: incomplete opinion row '%s'",
                    " ".join(row.text_content().split()),
                )
                continue

            # Ex: "Published Opinion", "Unpublished Order"
            label = row.xpath(".//span[contains(@class, 'tag')]/text()")

            self.cases.append(
                {
                    "name": name[0].strip(),
                    "url": urljoin(self.base_url, url[0]),
                    "date": date_filed[0].strip(),
                    "docket": docket[0].strip(),
                    "status": self.get_status(
                        label[0].strip() if label else ""
                    ),
                }
            )

    def get_status(self, label: str) -> str:
        """Get the precedential status from the row's document type tag

        :param label: the document type. Ex: "Unpublished Opinion"
        :return: the precedential status
        """
        if label.startswith("Unpublished"):
            return "Unpublished"
        if label.startswith("Published"):
            return "Published"

        logger.error("ca5: unknown document type '%s'", label)
        return "Unknown"

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Scrape a date range, following the pager when the range is big

        :param dates: tuple with the date range to scrape
        :return: None
        """
        start, end = dates
        logger.info("Backscraping for range %s %s", *dates)
        params = {
            "from": start.strftime("%Y-%m-%d"),
            "to": end.strftime("%Y-%m-%d"),
        }

        page = 1
        while True:
            self.url = self.build_url({**params, "page": page})
            self.html = await self._download()
            self._process_html()

            if not self.html.xpath("//a[@rel='next']"):
                break
            page += 1

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """

        pattern = re.compile(
            r"""
            (?:
               Appeals?\s+from\s+the\s+
             | Petition\s+for\s+Review\s+from\s+an\s+Order\s+of\s+the\s+
             | Petition\s+for\s+Review\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USDC))
            """,
            re.X,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }
        return {}
