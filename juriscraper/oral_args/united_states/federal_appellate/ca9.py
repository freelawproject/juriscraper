"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

import json
from datetime import datetime, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"
    days_interval = 30
    first_opinion_date = datetime(2000, 10, 16)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.court_id = self.__module__
        self.table = "media"
        self.base_url = "https://www.ca9.uscourts.gov/datastore/media/"
        self.expected_content_types = [
            "application/octet-stream; charset=UTF-8"
        ]
        # AWS Cognito creds step:
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

    def build_payload(self):
        """Build the DynamoDB query for the current start_date/end_date

        :return: None
        """
        self.payload = json.dumps(
            {
                "TableName": self.table,
                "ReturnConsumedCapacity": "TOTAL",
                "FilterExpression": "#PUBLISH >= :from_date AND #PUBLISH <= :to_date",
                "ExpressionAttributeNames": {"#PUBLISH": "publish"},
                "ExpressionAttributeValues": {
                    ":from_date": {"N": self.start_date.strftime("%Y%m%d")},
                    ":to_date": {"N": self.end_date.strftime("%Y%m%d")},
                },
            }
        )

    async def _download(self):
        """Build and download the table to parse

        DynamoDB Scan returns at most 1MB per request. If the response
        contains a ``LastEvaluatedKey``, we must paginate by feeding it
        back as ``ExclusiveStartKey`` in subsequent requests.

        :return: list of DynamoDB item dicts
        """
        self.downloader_executed = True

        if self.test_mode_enabled():
            return json.load(open(self.mock_url))

        sess = self.request["session"]

        # fetch for credentials
        res = await sess.post(self.url, headers=self.headers, json=self.params)
        creds = res.json().get("Credentials")

        all_items = []
        payload = json.loads(self.payload)
        max_pages = 100

        for page in range(max_pages):
            encoded_payload = json.dumps(payload)
            sig = generate_aws_sigv4_headers(
                encoded_payload, self.table, creds
            )

            logger.info(
                "Now downloading case page at: %s (params: %s)"
                % (self.url, encoded_payload)
            )
            self.request["response"] = await sess.post(
                self.query_url, headers=sig, data=encoded_payload
            )

            if self.save_response:
                self.save_response(self)

            self._post_process_response()
            data = self._return_response_text_object()
            all_items.extend(data.get("Items", []))

            last_key = data.get("LastEvaluatedKey")
            if not last_key:
                break

            payload["ExclusiveStartKey"] = last_key
            logger.info(
                "Paginating DynamoDB scan (%d items so far)", len(all_items)
            )
        else:
            logger.warning(
                "Reached max pagination limit of %d pages (%d items)",
                max_pages,
                len(all_items),
            )

        return all_items

    def _process_html(self):
        """Process the json response"""

        for record in self.html:
            date_str = record.get("hearing_date", {}).get("S")
            try:
                # validate ISO date
                datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                logger.debug(f"Skipping row with bad hearing_date: {date_str}")
                continue

            try:
                audio = record["audio_file_name"]["S"]
            except KeyError:
                logger.debug("Skipping row with no audio_file_name")
                continue

            self.cases.append(
                {
                    "date": date_str,
                    "docket": record["case_num"]["S"],
                    "judge": record["case_panel"]["S"],
                    "name": record["case_name"]["S"],
                    "url": urljoin(self.base_url, audio),
                }
            )

    async def _download_backwards(self, dates: tuple[str, str]) -> None:
        """Download backwards

        :param dates: (start_str, end_str) in "%Y/%m/%d" or empty.
        :return: None
        """
        start_str, end_str = dates

        # Parse start date or fall back to first_opinion_date
        if start_str:
            self.start_date = datetime.strptime(start_str, "%Y/%m/%d")
        else:
            self.start_date = self.first_opinion_date

        # Parse end date or fall back to now
        if end_str:
            self.end_date = datetime.strptime(end_str, "%Y/%m/%d")
        else:
            self.end_date = datetime.now()

        # Rebuild payload for this slice
        self.build_payload()
        self.html = await self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """
        Prepare a single (start, end) tuple, defaulting to __init__’s range
        or overridden via backscrape_start / backscrape_end in kwargs.
        """
        start = kwargs.get("backscrape_start", self.start_date)
        end = kwargs.get("backscrape_end", self.end_date)
        self.back_scrape_iterable = [(start, end)]
