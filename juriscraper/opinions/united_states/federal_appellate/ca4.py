import json
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
        self.make_backscrape_iterable(kwargs)

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
            case_metadata = row.get("line2")
            if (
                "OPINION" not in case_metadata
                or "day, " not in case_metadata
                or "OPINION ATTACHMENTS" in case_metadata
            ):
                logger.debug("Skipping %s", case_metadata)
                continue

            is_published = " PUBLISHED" in case_metadata
            self.cases.append(
                {
                    "docket": row["line1"].split()[0],
                    "name": row.get("fieldMap").get("title"),
                    "url": row.get("fieldMap").get("url"),
                    "date": row["line2"].split("day, ")[1].strip("."),
                    "status": "Published" if is_published else "Unpublished",
                    "per_curiam": "PER CURIAM" in case_metadata,
                }
            )

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

    def _download(self, request_dict=None):
        """Download JSON object

        :param request_dict: None
        :return: the json if any
        """
        if self.test_mode_enabled():
            with open(self.url) as f:
                return json.load(f)
        self.update_parameters()
        json_param = self.request["parameters"]["json"]
        return self.request["session"].post(self.url, json=json_param).json()
