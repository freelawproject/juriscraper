"""
Scraper for the United States Bankruptcy Appellate Panel for the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP
"""

import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin

from pydantic import TypeAdapter
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.auth_utils import (
    COGNITO_RESPONSE,
    generate_aws_sigv4_headers,
)
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import (
    BackscrapeOptions,
    DynamoDBItem,
    DynamoDBScan,
    ExtractedMetadata,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

_items_adapter = TypeAdapter(list[DynamoDBItem])
_scan_adapter = TypeAdapter(DynamoDBScan)


class Site(OpinionSiteLinear[tuple[datetime, datetime, None]]):
    payload: str

    query_url = "https://dynamodb.us-west-2.amazonaws.com/"
    days_interval = 31
    first_opinion_date = datetime(2005, 1, 6)
    lower_court_regex = re.compile(
        r"Appeals? from the (?P<lower_court>.+\n.+)"
    )

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[datetime, datetime, None]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.ca9.uscourts.gov/bap/"

        self.table = "bap"
        self.headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
        }
        self.params = {
            "IdentityId": "us-west-2:8d780f3b-d79c-c6c8-1125-e7a905da6b9b"
        }
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=self.days_interval)
        self.build_payload()
        self.url = "https://cognito-identity.us-west-2.amazonaws.com/"
        self.make_backscrape_iterable(kwargs)

    def build_payload(self) -> None:
        """Build query

        :return: query dict
        """
        expression_values = {
            ":start_date": {"S": self.start_date.strftime("%m")},
            ":year": {"S": self.start_date.strftime("%Y")},
        }
        filter_expression = (
            "#date_filed > :start_date and contains(#date_filed, :year)"
        )
        if self.start_date.month != 12:
            expression_values[":end_date"] = {
                "S": self.end_date.strftime("%m")
            }
            filter_expression = "#date_filed > :start_date and #date_filed < :end_date and contains(#date_filed, :year)"

        self.payload = json.dumps(
            {
                "TableName": self.table,
                "FilterExpression": filter_expression,
                "ExpressionAttributeNames": {"#date_filed": "date_filed"},
                "ExpressionAttributeValues": expression_values,
                "ReturnConsumedCapacity": "TOTAL",
            }
        )

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> list[DynamoDBItem]:
        """Download data from DynamoDB for oral arguments.

        :return: The JSON response from DynamoDB containing oral argument records.
        """
        if self.test_mode_enabled():
            with open(self.mock_url) as fixture:
                return _items_adapter.validate_json(
                    fixture.read(), strict=True
                )

        sess = self.request["session"]

        # fetch for credentials
        if self.url is None:
            raise ValueError("The Cognito URL is not configured")
        res = await sess.post(self.url, headers=self.headers, json=self.params)
        res.raise_for_status()
        creds = COGNITO_RESPONSE.validate_python(res.json(), strict=True)[
            "Credentials"
        ]

        # fetch signed headers
        sig = generate_aws_sigv4_headers(self.payload, self.table, creds)

        logger.info(
            "Now downloading case page at: %s (params: %s)"
            % (self.url, self.payload)
        )

        # fetch bap table
        self.request["response"] = await sess.post(
            self.query_url, headers=sig, content=self.payload
        )

        if self.save_response is not None:
            self.save_response(self)

        self._post_process_response()
        return _scan_adapter.validate_python(
            self._return_response_text_object(), strict=True
        ).get("Items", [])

    @override
    def _process_html(self) -> None:
        """Process the HTML response and extract case details.

        Iterates over the items in the HTML response, extracts relevant
        case information, and appends it to the cases list.

        :return: None; updates self.cases with extracted case details.
        """
        for item in _items_adapter.validate_python(self.html, strict=True):
            date_str = item["date_filed"].get("S")
            if date_str is None:
                raise KeyError("S")
            try:
                d = datetime.strptime(date_str, "%m/%d/%Y")
                if d < self.start_date:
                    continue
                if d > self.end_date:
                    continue
            except ValueError:
                logger.debug("Skipping row with bad date data %s", item)
                continue

            slug = item["file_name"].get("S")
            status = item["document_type"].get("S")
            if slug is None or status is None:
                raise KeyError("S")
            if status == "Unpublished Opinion":
                status = "Unpublished"
            else:
                status = "Published"
            self.cases.append(
                {
                    "name": f"In re: {item.get('debtor', {}).get('S', '')}",
                    "date": date_str,
                    "url": urljoin("https://cdn.ca9.uscourts.gov", slug),
                    "docket": item.get("bap_num", {}).get("S"),
                    "status": status,
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        if (match := self.lower_court_regex.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }

        return {}

    @override
    async def _download_backwards(
        self, dates: tuple[datetime, datetime, None]
    ) -> None:
        """Download cases for a specific date range.

        :param dates: A tuple containing start and end dates.
        :return: None; updates self.cases with cases from the specified date range.
        """
        self.start_date, self.end_date, _ = dates

        self.payload = json.dumps(
            {"TableName": self.table, "ReturnConsumedCapacity": "TOTAL"}
        )
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        self.start_date = (
            datetime.strptime(start, "%Y/%m/%d")
            if bool(start)
            else self.first_opinion_date
        )
        self.end_date = (
            datetime.strptime(end, "%Y/%m/%d") if bool(end) else datetime.now()
        )
        self.back_scrape_iterable = [(self.start_date, self.end_date, None)]
