import re
from datetime import date, datetime
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2013, 1, 14)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = self.url = (
            "https://www.njcourts.gov/attorneys/opinions/supreme"
        )
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath("//div[@class='card-body']"):
            container = row.xpath(".//a[@class='text-underline-hover']")
            if not container:
                logger.warning(
                    "Skipping row with no URL: %s",
                    re.sub(r"\s+", " ", row.text_content()),
                )
                continue

            url = container[0].xpath("@href")[0]
            # name is sometimes inside a span, not inside the a tag
            name_content = container[0].xpath("string(.)")
            name_str, _, _ = name_content.partition("(")

            docket = row.xpath('.//*[contains(@class, "mt-1")]/text()')[
                0
            ].strip()
            date = row.xpath(
                ".//div[@class='col-lg-12 small text-muted mt-2']/text()"
            )[0]

            case = {
                "date": date,
                "docket": docket,
                "name": titlecase(name_str.strip()),
                "url": url,
            }

            if self.status == "Published":
                summary = row.xpath(".//div[@class='modal-body']/p/text()")
                case["summary"] = "\n".join(summary)

            self.cases.append(case)

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (?:
                On\s+certification\s+to\s+the\s+
                |On\s+appeal\s+from\s+the\s+
                |On\s+petitions\s+for\s+review\s+of\s+a\s+decision\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*[.,])
            """,
            re.X,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            if lower_court.lower().strip() == "superior court":
                lower_court = "New Jersey Superior Court"

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": titlecase(lower_court),
                }
            }

        return {}

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        params = {
            "start": dates[0].strftime("%Y-%m-%d"),
            "end": dates[1].strftime("%Y-%m-%d"),
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()
