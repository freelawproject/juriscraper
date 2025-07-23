"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

from datetime import date, datetime, timedelta
from urllib.parse import urljoin

from juriscraper.lib.dynamo_db_utils import (
    query_dynamodb,
)
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    region = "us-west-2"
    identity_id = "8d780f3b-d7d2-ca54-c86e-6eacc92a1265"
    table_name = "media"
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date;x-amz-security-token;x-amz-target"
    first_opinion_date = datetime(2000, 10, 16)
    days_interval = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.ca9.uscourts.gov/media/"
        self.expected_content_types = [
            "application/octet-stream; charset=UTF-8"
        ]

        self.search_date = date.today() - timedelta(days=1)

    def _download(self):
        """Download data from DynamoDB for oral arguments.

        Retrieves temporary AWS credentials, constructs a DynamoDB scan payload
        to filter oral argument records by publish date, and queries the
        DynamoDB `media` table for matching items.

        :return: The JSON response from DynamoDB containing oral argument records.
        """

        if self.test_mode_enabled():
            self._request_url_mock(self.url)
            self._post_process_response()
            return self._return_response_text_object()

        self.parameters = {
            "FilterExpression": "#PUBLISH >= :from_date",
            "ReturnConsumedCapacity": "TOTAL",
            "ExpressionAttributeNames": {"#PUBLISH": "publish"},
            "ExpressionAttributeValues": {
                ":from_date": {"N": self.search_date.strftime("%Y%m%d")}
            },
            "TableName": "media",
        }

        return query_dynamodb(
            self.identity_id,
            self.region,
            self.parameters,
            self.signed_headers,
            target="Scan",
        )

    def _process_html(self):
        """Process the HTML response and extract case details.

        Iterates over the items in the HTML response, extracts relevant
        case information, and appends it to the cases list.

        :return: None; updates self.cases with extracted case details.
        """
        for item in self.html.get("Items", []):
            self.cases.append(
                {
                    "name": item.get("case_name").get("S", ""),
                    "date": item.get("hearing_date").get("S"),
                    "url": urljoin(
                        self.base_url, item.get("audio_file_name").get("S")
                    ),
                    "docket": item.get("case_num").get("S"),
                    "judge": item.get("case_panel_lc", {}).get("S", ""),
                }
            )

    def _download_backwards(self, search_date: date) -> None:
        """Download and process HTML for a given target date.

        :param search_date (date): The date for which to download and process opinions.
        :return None; sets the target date, downloads the corresponding HTML
        and processes the HTML to extract case details.
        """
        self.search_date = search_date[0]
        self.html = self._download()
        self._process_html()
