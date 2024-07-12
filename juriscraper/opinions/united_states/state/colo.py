"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by WEP
    - 2023-11-19: Drop Selenium by WEP
    - 2023-12-20: Updated with citations, judges and summaries, Palin
    - 2024-07-04: Update to new site, grossir
"""

from datetime import date, datetime
from typing import Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://research.coloradojudicial.gov/search.json"
    detail_url = "https://research.coloradojudicial.gov/vid/{}.json?include=abstract%2Cparent%2Cmeta%2Cformats%2Cchildren%2Cproperties_with_ids%2Clibrary%2Csource&fat=1&locale=en&hide_ct6=true&t={}"
    days_interval = 30
    first_opinion_date = datetime(2010, 1, 1)
    api_court_code = "14024_01"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.params = {
            "product_id": "WW",
            "jurisdiction": "US",
            "content_type": "2",
            "court": self.api_court_code,
            "bypass_rabl": "true",
            "include": "parent,abstract,snippet,properties_with_ids",
            "per_page": "30",  # Server breaks down when per_page=500, returns 503
            "page": "1",
            "sort": "date",
            "include_local_exclusive": "true",
            "cbm": "6.0|361.0|5.0|9.0|4.0|2.0=0.01|400.0|1.0|0.001|1.5|0.2",
            "locale": "en",
            "hide_ct6": "true",
            "t": str(datetime.now().timestamp())[:10],
            "type": "document",
        }
        self.url = f"{self.base_url}?{urlencode(self.params)}"

        # Request won't work without some of these X- headers
        self.request["headers"].update(
            {
                "X-Requested-With": "XMLHttpRequest",
                "X-Root-Account-Email": "colorado@vlex.com",
                "X-User-Email": "colorado@vlex.com",
                "X-Webapp-Seed": "9887408",
            }
        )
        self.expected_content_types = ["text/html"]
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        search_json = self.html
        logger.info(
            "Number of results %s; %s in page",
            search_json["count"],
            len(search_json["results"]),
        )

        for result in search_json["results"]:
            timestamp = str(datetime.now().timestamp())[:10]
            url = self.detail_url.format(result["id"], timestamp)

            if self.test_mode_enabled():
                # we have manually nested detail JSONs to
                # to be able to have a test file
                detail_json = result["detail_json"]
            else:
                # Full case name and docket number are only available
                # on the detail page
                self._request_url_get(url)
                detail_json = self.request["response"].json()

            # Example of parallel citation:
            # https://research.coloradojudicial.gov/vid/907372624
            citation, parallel_citation = "", ""
            for p in detail_json["properties"]:
                label = p["property"]["label"]
                if label == "Docket Number":
                    docket_number = p["values"][0]
                if label == "Parties":
                    case_name_full = p["values"][0]
                if label == "Decision Date":
                    # Note that json['published_at'] is not the date_filed
                    date_filed = p["values"][0]
                if label == "Citation":
                    citation = p["values"][0]
                    if len(p["values"]) > 1:
                        parallel_citation = p["values"][1]

            case = {
                "date": date_filed,
                "docket": docket_number,
                "name": case_name_full,
                "url": f"{detail_json['public_url']}/content",
                "status": "Published" if citation else "Unknown",
                "citation": citation,
                "parallel_citation": parallel_citation,
            }

            self.cases.append(case)

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        start = dates[0].strftime("%Y-%m-%d")
        end = dates[1].strftime("%Y-%m-%d")
        timestamp = str(datetime.now().timestamp())[:10]
        params = {**self.params}
        params.update(
            {
                "date": f"{start}..{end}",
                # These are duplicated by the frontend too
                "locale": ["en", "en"],
                "hide_ct6": ["true", "true"],
                "t": [timestamp, timestamp],
            }
        )
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, self.days_interval
        )
