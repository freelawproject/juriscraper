"""
Scraper for New Hampshire Supreme Court
CourtID: nh_p
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
    """
    Regular site:
    https://www.courts.nh.gov/our-courts/supreme-court/orders-and-opinions/opinions
    """

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
        2014: "@field_document_subcategory|=|1581",
    }
    filter_mode = "exclusive"
    document_type = "opinions"
    # there is data since 2002, but we would need to
    # collect all subcategory or tag values
    start_year = 2015
    end_year = datetime.today().year - 1
    cite_regex = re.compile(r"\d{4}\sN\.H\.\s\d+")
    docket_regex = re.compile(r"(?P<docket>\d{4}-\d{1,4})[\s,]*")

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
            fields = case["fields"]

            if fields["field_document_file"]:
                url_object = fields["field_document_file"]
            elif fields["field_document"]:
                # seen on withdrawn opinions. Ex: 2020-0268
                # Hampstead School Board & a. v. School Administrative Unit No. 5
                url_object = fields["field_document"][0]["fields"][
                    "field_document_file"
                ]
            else:
                logger.warning(
                    "Skipping row '%s', can't find document link",
                    case["title"],
                )
                continue
            url = url_object["0"]["fields"]["uri"][0].split("//")[1]

            if fields["field_date_filed"]:
                case_date = fields["field_date_filed"][0]
            elif fields["field_date_posted"]:
                # usually this is the only populated field
                case_date = fields["field_date_posted"][0]
            else:
                logger.warning(
                    "Skipping row '%s'. No date found", case["title"]
                )
                continue

            # "title" format changes since 2024, where a citation string
            # replaces the docket number, and the docket is in another row
            name = case["title"]

            citation = ""
            cite_match = self.cite_regex.search(case["title"])
            if cite_match:
                citation = cite_match.group(0)
                name = re.sub(self.cite_regex, " ", name)

            docket = ", ".join(
                [
                    match.group("docket")
                    for match in self.docket_regex.finditer(case["title"])
                ]
            )
            if not docket and fields.get("field_description"):
                docket_str = fields["field_description"][0]["#text"]
                docket = self.docket_regex.search(docket_str).group(0)

            name = re.sub(self.docket_regex, " ", name)
            # delete traces of multiple docket numbers
            name = re.sub(r"^(and|[&,])", "", name.strip()).strip()

            self.cases.append(
                {
                    "date": case_date,
                    "url": urljoin(
                        "https://www.courts.nh.gov/sites/g/files/ehbemt471/files/",
                        url,
                    ),
                    "name": name,
                    "docket": docket,
                    "citation": citation,
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
        year_filter = (
            "" if not self.back_scrape_iterable else self.year_to_filter[year]
        )
        params = {
            "iterate_nodes": "true",
            # Will raise a KeyError if there is no proper year key, we will
            # need to manually correct this next year
            "q": self.base_filter.format(year_filter),
            "sort": "field_date_posted|desc|ALLOW_NULLS",
            "filter_mode": self.filter_mode,
            "type": "document",
            "page": "1",
            "size": "25",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.request["headers"] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "Referer": f"https://www.courts.nh.gov/our-courts/supreme-court/orders-and-opinions/{self.document_type}/{year}",
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
