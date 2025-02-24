import re
from datetime import date, datetime
from typing import Tuple
from urllib.parse import urlencode

from annotated_types.test_cases import cases
from exceptiongroup import catch
from lxml import html

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

            doc = row.xpath(
                './/*[contains(@class, "one-line-truncate me-1 mt-1")]/text()')[
                0
            ].strip()

            date = row.xpath(
                ".//div[@class='col-lg-12 small text-muted mt-2']/text()"
            )[0]

            dock = doc
            get_docks = dock.split('-')
            first = get_docks[0]
            second = get_docks[-1]
            get_docks = get_docks[1].split('/')

            docket = []
            for c in get_docks:
                docket.append(f"{first}-{c}-{second}")

            print(docket)
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

    # def _download_backwards(self, dates: Tuple[date]):
    #     params = {
    #             "start": dates[0].strftime("%Y-%m-%d"),
    #             "end": dates[1].strftime("%Y-%m-%d"),
    #             "page": 10
    #         }
    #
    #     self.url=f"{self.base_url}?{urlencode(params)}"
    #     self.html = self._download()
    #     print(html.tostring(self.html, pretty_print=True).decode('utf-8'))
    #     self._process_html()

    def _download_backwards(self, dates: Tuple[date]) -> None:

        logger.info("Setting the parameters for range %s %s", *dates)
        params = {
            "start": dates[0].strftime("%Y-%m-%d"),
            "end": dates[1].strftime("%Y-%m-%d"),
        }

        seen_dockets = set()  # To track unique docket numbers
        page = 0

        while True:
            params["page"] = page
            self.url = f"{self.base_url}?{urlencode(params)}"
            # logger.info(f"Fetching page {page} with URL: {self.url}")

            self.html = self._download()
            # print(html.tostring(self.html, pretty_print=True).decode('utf-8'))
            initial_case_count = len(self.cases)

            self._process_html()

            new_cases = []
            for case in self.cases[
                        initial_case_count:]:
                docket = tuple(case.get("docket"))
                if docket not in seen_dockets:
                    seen_dockets.add(docket)
                    new_cases.append(case)

            self.cases = self.cases[:initial_case_count] + new_cases

            logger.info(
                f"Unique cases added from page {page}: {len(new_cases)}")

            if not new_cases:
                logger.info(
                    f"No new unique cases on page {page}. Stopping pagination.")
                break

            page +=1

        logger.info(f"Total unique cases found: {len(self.cases)}")

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        logger.info(f"inside crawling_range function and crawling between the dates {start_date} and {end_date}")
        self._download_backwards((start_date , end_date))

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()

        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()

        logger.info(f"returning {len(self.cases)}")
        return len(self.cases)

    def get_court_name(self):
        return "Supreme Court of New Jersey"

    def get_state_name(self):
        return "New Jersey"

    def get_class_name(self):
        return "nj"

    def get_court_type(self):
        return "state"
