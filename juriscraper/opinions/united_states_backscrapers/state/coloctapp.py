import re
from datetime import date, datetime
from typing import Any, Dict, Tuple
from urllib.parse import urlencode

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://research.coloradojudicial.gov/search.json"
    detail_url = "https://research.coloradojudicial.gov/vid/{}.json?include=abstract%2Cparent%2Cmeta%2Cformats%2Cchildren%2Cproperties_with_ids%2Clibrary%2Csource&fat=1&locale=en&hide_ct6=true&t={}"
    api_court_code = "14024_02"
    days_interval = 30
    first_opinion_date = datetime(2010, 1, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Request won't work without some of these X- headers
        self.request["headers"].update(
            {
                "X-Requested-With": "XMLHttpRequest",
                "X-Root-Account-Email": "colorado@vlex.com",
                "X-User-Email": "colorado@vlex.com",
                "X-Webapp-Seed": "9887408",
            }
        )
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
            self._request_url_get(url)
            json = self.request["response"].json()

            # Note that json['published_at'] is not the date_filed
            for p in json["properties"]:
                label = p["property"]["label"]
                if label == "Docket Number":
                    docket_number = p["values"][0]
                if label == "Parties":
                    case_name_full = p["values"][0]
                if label == "Decision Date":
                    date_filed = p["values"][0]

            self.cases.append(
                {
                    "date_filed": date_filed,
                    "docket": docket_number,
                    "case_name_full": case_name_full,
                    "case_name": result["title"],
                    "url": f"{json['public_url']}/content",
                    "status": "Unknown",
                }
            )

    def extract_from_text(self, scraped_html: str) -> Dict[str, Any]:
        """Extract status from text

        For Unpublished opinions:
        - May be in free text
        https://research.coloradojudicial.gov/vid/899568481/content
        - or in nested HTML tags
        https://colorado.vlex.io/vid/people-v-gamez-ruiz-890926106/content

        Published opinions may be identified by the presence of a nested citation:
        https://research.coloradojudicial.gov/vid/907372624

        :param scraped_html: download html
        :return: dictionary with "OpinionCluster" key
        """
        status = "Unknown"
        text = html.fromstring(scraped_html.text).xpath("string(.)")
        text = re.sub("\s+", " ", text)

        if "NOT PUBLISHED" in scraped_html.upper():
            status = "Unpublished"
        elif re.search(r"\d{4} COA \d+", scraped_html[:200]):
            status = "Published"

        return {"OpinionCluster": {"precedential_status": status}}

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        start = dates[0].strftime("%Y-%m-%d")
        end = dates[1].strftime("%Y-%m-%d")
        timestamp = str(datetime.now().timestamp())[:10]
        params = {
            "product_id": "WW",
            "jurisdiction": "US",
            "content_type": "2",
            "court": self.api_court_code,
            "date": f"{start}..{end}",
            "bypass_rabl": "true",
            "include": "parent,abstract,snippet,properties_with_ids",
            "per_page": "200",  # Server breaks down when per_page=500, returns 503
            "page": "1",
            "sort": "date",
            "include_local_exclusive": "true",
            "cbm": "6.0|361.0|5.0|9.0|4.0|2.0=0.01|400.0|1.0|0.001|1.5|0.2",
            # These are duplicated by the frontend too
            "locale": ["en", "en"],
            "hide_ct6": ["true", "true"],
            "t": [timestamp, timestamp],
            "type": "document",
        }
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
