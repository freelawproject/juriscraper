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

from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://research.coloradojudicial.gov/search.json"
    detail_url = "https://research.coloradojudicial.gov/vid/{}.json?include=abstract%2Cparent%2Cmeta%2Cformats%2Cchildren%2Cproperties_with_ids%2Clibrary%2Csource&fat=1&locale=en&hide_ct6=true&t={}"
    days_interval = 30
    first_opinion_date = datetime(2010, 1, 1)
    api_court_code = "14024_01"
    label_to_key = {
        "Docket Number": "docket",
        "Parties": "name",
        "Decision Date": "date",
        "Citation": "citation",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.params = {
            "product_id": "COLORADO",
            "jurisdiction": "US",
            "content_type": "2",
            "court": self.api_court_code,
            "bypass_rabl": "true",
            "include": "parent,abstract,snippet,properties_with_ids",
            "per_page": "50",  # Server breaks down when per_page=500, returns 503
            "page": "1",
            "sort": "date",
            "type": "document",
            "include_local_exclusive": "true",
            "cbm": "6.0|361.0|5.0|9.0|4.0|2.0=0.01|400.0|1.0|0.001|1.5|0.2",
            "locale": "en",
            "hide_ct6": "true",
        }
        self.update_url()
        self.request["headers"]["User-Agent"] = "Courtlistener"

        # https://www.coloradojudicial.gov/system/files/opinions-2024-11/24SC459.pdf
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

    def update_case(self, case: dict, detail_json: dict) -> dict:
        """Update case dictionary with nested properties

        :param case: the case data
        :param detail_json: The json response
        :return: The updated case data
        """
        for p in detail_json["properties"]:
            label = p["property"]["label"]
            values = p["values"]
            if label in self.label_to_key:
                key = self.label_to_key[label]
                if label == "Citation":
                    case[key] = values[0]
                    if len(values) > 1:
                        case["parallel_citation"] = values[1]
                else:
                    case[key] = values[0]
        case["status"] = "Published" if case["citation"] else "Unpublished"
        return case

    def _process_html(self) -> None:
        search_json = self.html
        logger.info(
            "Number of results %s; %s in page",
            search_json["count"],
            len(search_json["results"]),
        )

        for result in search_json["results"]:
            case = {"citation": "", "parallel_citation": ""}
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

            if (
                self.court_id
                == "juriscraper.opinions.united_states.state.colo"
            ):
                case["url"] = f"{detail_json['public_url']}/content"
            else:
                case["url"] = (
                    f"https://colorado.vlex.io/pdf_viewer/{result.get('id')}"
                )

            case = self.update_case(case, detail_json)
            self.cases.append(case)

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.update_url(dates)
        self.html = self._download()
        self._process_html()

    def update_url(self, dates: Optional[Tuple[date]] = None) -> None:
        """
        Set URL with date filters and current timestamp.
        Request with no date filter was returning very old documents
        instead of the most recent ones

        :param dates: start and end date tuple. If not present,
            scrape last week
        """
        if not dates:
            today = datetime.now()
            dates = (today - timedelta(7), today + timedelta(1))

        start = dates[0].strftime("%Y-%m-%d")
        end = dates[1].strftime("%Y-%m-%d")
        timestamp = str(datetime.now().timestamp())[:10]
        params = {**self.params}
        params.update(
            {
                "date": f"{start}..{end}",
                "t": timestamp,
            }
        )
        self.url = f"{self.base_url}?{urlencode(params)}"
