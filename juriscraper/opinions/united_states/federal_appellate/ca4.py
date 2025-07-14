import re
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    oldest_opinion = "2002-03-20"
    court_name = "United States Court of Appeals for the Fourth Circuit"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.govinfo.gov/wssearch/search"
        self.court_id = self.__module__
        self.method = "POST"
        self.expected_content_types = ["application/pdf"]

        self.start = (date.today() - relativedelta(months=1)).strftime(
            "%Y-%m-%d"
        )
        self.end = date.today().strftime("%Y-%m-%d")
        self.date_range = f"{self.start},{self.end}"
        self.parameters = {}
        self.update_parameters()
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    def make_backscrape_iterable(self, kwargs: dict[str, str]) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        start_str = kwargs.get("backscrape_start", self.oldest_opinion)
        end_str = kwargs.get("backscrape_end", self.end)

        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

        date_ranges: list[str] = []
        current = start_date

        while current <= end_date:
            week_end = min(current + relativedelta(days=7), end_date)
            date_ranges.append(f"{current:%Y-%m-%d},{week_end:%Y-%m-%d}")
            current = week_end + relativedelta(days=1)

        self.back_scrape_iterable = date_ranges

    def _process_html(self) -> None:
        """Process CA4 Opinions

        :return: None
        """
        for row in self.html["resultSet"]:
            line2 = row.get("line2")
            if (
                "OPINION" not in line2
                or "day, " not in line2
                or "OPINION ATTACHMENT" in line2
            ):
                logger.debug("Skipping %s", line2)
                continue

            teaser = row.get("fieldMap").get("teaser")
            metadata = self.extract_metadata(teaser)
            is_published = " PUBLISHED" in line2
            case = {
                "docket": row["line1"].split()[0],
                "name": row.get("fieldMap").get("title"),
                "url": row.get("fieldMap").get("url"),
                "date": row["line2"].split("day, ")[1].strip("."),
                "status": "Published" if is_published else "Unpublished",
                "per_curiam": "PER CURIAM" in line2,
            }
            case.update(metadata)
            self.cases.append(case)

    def extract_metadata(self, teaser: str) -> dict[str, str]:
        """Extract out various metadata fields

        Method leaves in a few regex patterns that we do not currently support
        but could be added to our ingestion pipeline.

        :param teaser: The teaser line provided in some opinions
        :return: Extracted data
        """
        if not teaser:
            return {"lower_court": "", "lower_court_number": ""}
        patterns = {
            "lower_court": re.compile(
                r"""
                (?:
                   Appeal(?:s)?\s+from\s+the\s+
                 | On\s+Petition\s+for\s+Review\s+of\s+an\s+Order\s+of\s+the\s+
                )
                (?P<lower_court>[^.,]+?)
                (?=[\.,])
                """,
                re.X,
            ),
            "lower_court_number": re.compile(
                r"""
                \(\s*
                (?P<lower_court_number>\d+:\d{2}-[a-z]{2}-\d+(?:-[\w-]+)*)
                \s*\)
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            # "date_argued": re.compile(
            #     r"Argued:\s*(?P<date_argued>[A-Z][a-z]+ \d{1,2}, \d{4})"),
            # "date_decided": re.compile(
            #     r"Decided:\s*(?P<date_decided>[A-Z][a-z]+ \d{1,2}, \d{4})"),
            # "amended_date": re.compile(
            #     r"Amended:\s*(?P<amended_date>[A-Z][a-z]+ \d{1,2}, \d{4})"),
            # "panel_str": re.compile(r"Before\s+(?P<panel_str>[^.]+)"),
        }
        metadata: dict[str, str] = {}
        for name, pat in patterns.items():
            m = pat.search(teaser)
            match = m.group(name) if m else ""
            if (
                match.strip()
                == "United States District Court for the Southern District of West"
            ):
                match = "United States District Court for the Southern District of West Virginia"
            metadata[name] = match
        return metadata

    def update_parameters(self):
        """Update the date range parameter"""

        self.request["parameters"]["json"] = {
            "historical": True,
            "offset": 0,
            "query": f"collection:(USCOURTS) AND publishdate:range({self.date_range})  AND  courtname:(United States Court of Appeals for the Fourth Circuit)",
            "pageSize": 100,
            "sortBy": "2",  # 2 -> newest to oldest
        }

    def _download_backwards(self, date_range) -> None:
        """Download backward

        :param date_range: the date range as a string
        :return: None
        """
        self.date_range = date_range
        self.update_parameters()
        self.html = self._download()
        self._process_html()
