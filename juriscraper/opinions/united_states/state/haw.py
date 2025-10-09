# Author: Michael Lissner
# Date created: 2013-05-23

import re
from datetime import date, datetime

from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

logger = make_default_logger()


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2010, 1, 1)
    days_interval = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://www.courts.state.hi.us/opinions_and_orders/opinions"
        )
        self.court_id = self.__module__
        self.court_code = "S.Ct"
        self.status = "Published"
        self.should_have_results = True
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        for row in self.html.xpath("//tr[@class='row-']"):
            date, court, docket, name, lower_court, citation = row.xpath(
                ".//td"
            )
            court = court.text_content()
            if court != self.court_code:
                continue

            if not docket.xpath(".//a"):
                continue

            name_text = name.text_content().strip()
            last_period_regex = (
                r", Dated|(?<!v)(?<!Jr)(?<!U\.S)(?<! [A-Z])\.(?! Inc\.)"
            )

            if "(" in name_text:
                name = name_text.split("(", 1)[0].strip()
            else:
                v_match = re.search(r" v\. ", name_text)
                if v_match:
                    post_v = name_text[v_match.end() :]
                    name = (
                        name_text[: v_match.end()]
                        + re.split(last_period_regex, post_v, maxsplit=1)[
                            0
                        ].strip()
                    )
                else:
                    name = re.split(last_period_regex, name_text, maxsplit=1)[
                        0
                    ].strip()

            self.cases.append(
                {
                    "date": date.text_content(),
                    "name": name,
                    "docket": docket.text_content()
                    .strip()
                    .split("\t")[0]
                    .split()[0],
                    "url": docket.xpath(".//a")[0].get("href"),
                    "lower_court": lower_court.text_content(),
                    "citation": citation.text_content(),
                }
            )

    def _download_backwards(self, search_date: date) -> None:
        """Download and process HTML for a given target date.

        :param search_date (date): The date for which to download and process opinions.
        :return None; sets the target date, downloads the corresponding HTML
        and processes the HTML to extract case details.
        """

        self.request["parameters"]["params"] = {
            "yr": search_date.year,
            "mo": f"{search_date.month:02d}",
        }
        logger.info(
            "Now downloading case page at: %s (params: %s)"
            % (self.url, self.request["parameters"]["params"])
        )
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
