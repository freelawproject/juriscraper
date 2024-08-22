"""
Scraper for New Hampshire Supreme Court
CourtID: nh
Court Short Name: NH
Court Contact: webmaster@courts.state.nh.us
Author: Andrei Chelaru
Reviewer: mlr
History:
    - 2014-06-27: Created
    - 2014-10-17: Updated by mlr to fix regex error.
    - 2015-06-04: Updated by bwc so regex catches comma, period, or
    whitespaces as separator. Simplified by mlr to make regexes more semantic.
    - 2016-02-20: Updated by arderyp to handle strange format where multiple
    case names and docket numbers appear in anchor text for a single case pdf
    link. Multiple case names are concatenated, and docket numbers are
    concatenated with ',' delimiter
    - 2021-12-29: Updated for new web site, by flooie and satsuki-chan
    - 2024-08-21: Implement backscraper and update headers, by grossir
"""

import re
from datetime import datetime
from typing import Dict, List
from urllib.parse import urlencode, urljoin

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # document_purpose = 1331 -> Supreme Court Opinion
    base_filter = "{}@field_document_purpose|=|1331"
    year_to_filter = {
        2024: "@field_document_subcategory|=|2316",
        2023: "@field_document_subcategory|=|2256",
        2022: "@field_document_subcategory|=|2091",
        2021: "@field_tags|CONTAINS|1206~field_entity_tags|CONTAINS|1206",
        2020: "@field_tags|CONTAINS|1366~field_entity_tags|CONTAINS|1366",
        2019: "@field_tags|CONTAINS|1416~field_entity_tags|CONTAINS|1416",
        2018: "@field_document_subcategory|=|1601",
        2017: "@field_document_subcategory|=|1596",
        2016: "@field_document_subcategory|=|1591",
        2015: "@field_document_subcategory|=|1586",
    }
    # there is data since 2002, but we would need to
    # collect all subcategory or tag values
    start_year = 2015
    end_year = datetime.today().year - 1

    params = {
        "iterate_nodes": "true",
        "q": "",
        "sort": "field_date_posted|desc|ALLOW_NULLS",
        "filter_mode": "exclusive",
        "type": "document",
        "page": "1",
        "size": "25",
    }
    docket_regex = re.compile(r"\d{4}-\d{4}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.base_url = "https://www.courts.nh.gov/content/api/documents"
        self.set_request_parameters()
        self.needs_special_headers = True
        self.make_backscrape_iterable(kwargs)
        self.paginate = False

    def _process_html(self) -> None:
        json_response = self.html

        for case in json_response["data"]:
            url = case["fields"]["field_document_file"]["0"]["fields"]["uri"][
                0
            ].split("//")[1]

            if "," not in case["title"]:
                logger.info("Skipping case with title %s", case["title"])
                continue

            # "title" format changes since 2024, where a citation string
            # replaces the docket number, and the docket is in another row
            docket_or_cite, name = case["title"].split(",", 1)
            if self.docket_regex.search(docket_or_cite):
                docket = docket_or_cite
                neutral_citation = ""
            else:
                neutral_citation = docket_or_cite
                docket_str = case["fields"]["field_description"][0]["#text"]
                docket = self.docket_regex.search(docket_str).group(0)

            self.cases.append(
                {
                    "name": name.strip(),
                    "docket": docket.strip(),
                    "date": case["fields"]["field_date_posted"][0],
                    "url": urljoin(
                        "https://www.courts.nh.gov/sites/g/files/ehbemt471/files/",
                        url,
                    ),
                    "citation": neutral_citation,
                }
            )

        # This flag will be set to True by the _download_backwards method
        if not self.paginate:
            return
        self.paginate = False  # prevent recursion

        logger.info(
            "Found %s results, will paginate through", json_response["total"]
        )
        for page in range(2, json_response["last_page"] + 1):
            logger.info("Paginating to page %s", page)
            self.url = self.url.replace(f"page={page-1}", f"page={page}")
            self.html = self._download()
            self._process_html()

    def set_request_parameters(
        self, year: int = datetime.today().year
    ) -> None:
        """Each year has a unique `field_document_subcategory` key, so we must
        set it accordingly

        :param year: full year integer
        """
        params = {**self.params}
        # Will raise a KeyError if there is no proper year key, we will
        # need to manually correct this next year
        params["q"] = self.base_filter.format(self.year_to_filter[year])

        self.url = f"{self.base_url}?{urlencode(params)}"
        self.request["headers"] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "Referer": f"https://www.courts.nh.gov/our-courts/supreme-court/orders-and-opinions/opinions/{year}",
            "X-Requested-With": "XMLHttpRequest",
        }

    def _download_backwards(self, year: int) -> None:
        self.paginate = True
        self.set_request_parameters(year)
        logger.info("Backscraping year %s", year)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: Dict) -> List[int]:
        """The API exposes no date filter, so we must query a year 
        and then paginate the results.
        """
        start = int(kwargs.get("backscrape_start") or self.start_year)
        end = int(kwargs.get("backscrape_end") or self.end_year)

        if start == end:
            self.back_scrape_iterable = [start]
        else:
            self.back_scrape_iterable = range(start, end + 1)
