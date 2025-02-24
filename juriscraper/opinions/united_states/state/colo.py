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
import re
from datetime import date, datetime, timedelta
from typing import Tuple
from urllib.parse import urlencode

import requests

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://research.coloradojudicial.gov/search.json"
    detail_url = "https://research.coloradojudicial.gov/vid/{}.json?include=abstract%2Cparent%2Cmeta%2Cformats%2Cchildren%2Cproperties_with_ids%2Clibrary%2Csource&fat=1&locale=en&hide_ct6=true&t={}"
    base_html_url = "https://research.coloradojudicial.gov/en/vid/"
    days_interval = 30
    first_opinion_date = datetime(2010, 1, 1)
    api_court_code = "14024_01"

    def _fetch_duplicate(self, data):
        # Create query for duplication
        query_for_duplication = {"pdf_url": data.get("pdf_url"), "docket": data.get("docket"), "title": data.get("title") , "citation": data.get("citation")}
        # Find the document
        duplicate = self.judgements_collection.find_one(query_for_duplication)
        object_id = None
        if duplicate is None:
            # Insert the new document
            self.judgements_collection.insert_one(data)

            # Retrieve the document just inserted
            updated_data = self.judgements_collection.find_one(query_for_duplication)
            object_id = updated_data.get("_id")  # Get the ObjectId from the document
            self.flag = True
        else:
            # Check if the document already exists and has been processed
            processed = duplicate.get("processed")
            if processed == 10:
                raise Exception("Judgment already Exists!")  # Replace with your custom DuplicateRecordException
            else:
                object_id = duplicate.get("_id")  # Get the ObjectId from the existing document
        return object_id

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
            "sort": "date",
            "include_local_excluive": "true",
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
        case_pattern = r'\b\d+[A-Z]+\d+\b'

        for result in search_json["results"]:
            #exract the id from the file
            case_id = result["id"]
            timestamp = str(datetime.now().timestamp())[:10]
            url = self.detail_url.format(result["id"], timestamp)

            html_url = f"{self.base_html_url}{case_id}"
            html_ur=f"{self.base_html_url}{case_id}/content"
            html_res = requests.get(html_ur,
                                         headers=self.request["headers"],
                                         proxies=self.proxies)

            if self.test_mode_enabled():
                detail_json = result["detail_json"]
            else:

                self._request_url_get(url)

                detail_json = self.request["response"].json()

            # pdf_url = f"https://research.coloradojudicial.gov/pdf/{case_id}"

            # Example of parallel citation:
            # https://research.coloradojudicial.gov/vid/907372624
            citation, parallel_citation = "", ""
            for p in detail_json["properties"]:
                label = p["property"]["label"]
                if label == "Docket Number":
                    print(p["values"][0])
                    docket_number = p["values"][0]
                if label == "Parties":
                    case_name_full = p["values"][0]
                if label == "Decision Date":
                    date_filed = p["values"][0]
                if label == "Citation":
                    citation = p["values"][0]
                    if len(p["values"]) > 1:
                        parallel_citation = p["values"][1]
            match = re.search(case_pattern, docket_number)

            case = {
                "date": date_filed,
                "docket": [match.group()],
                "name": case_name_full,
                "url" : f"https://research.coloradojudicial.gov/pdf/{case_id}",
                "status": "Published" if citation else "Unknown",
                "citation": [citation],
                "parallel_citation": [parallel_citation],
                "html_url": html_url,
                "response_html": html_res.text,
            }
            print(f'case docket is : {case["docket"]}')

            self.cases.append(case)

    def _download_backwards(self, dates: Tuple[date]) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        start = dates[0].strftime("%Y-%m-%d")
        end = dates[1].strftime("%Y-%m-%d")
        timestamp = str(datetime.now().timestamp())[:10]
        params = {**self.params}
        params.update(
            {
                "date": f"{start}..{end}",
                "locale": ["en", "en"],
                "hide_ct6": ["true", "true"],
                "t": [timestamp, timestamp],
            }
        )

        page=1
        while True:
            params["page"]=str(page)
            self.url=f"{self.base_url}?{urlencode(params)}"
            try:
                self.html = self._download()
                logger.info(f"Loading page {page}")

                search_json = self.html

                if not search_json.get("results"):
                    logger.info(f"No more data found on page {page}")
                    break

                self._process_html()
                page += 1

            except Exception as e:
                logger.error(f"Error loading page {page}: {e}")
                logger.info(f"Skipping page {page} due to error: {e}")
                page += 1
        logger.info("Finished backscraping for range %s to %s", start, end)



    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        # start_date = datetime(2024,10,31)
        # end_date=datetime(2024,11,30)
        logger.info("Crawling between the dates from %s to %s", start_date , end_date)
        # self.parse()
        self._download_backwards((start_date, end_date))
        self.parse()

        return len(self.cases)


    def get_class_name(self):
        return "colo"

    def get_court_name(self):
        return "Colorado Supreme Court"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Colorado"
