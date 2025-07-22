"""
Scraper for the United States Bankruptcy Appellate Panel for the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP
"""

from datetime import date, datetime
from urllib.parse import urljoin

from juriscraper.lib.dynamo_db_utils import (
    get_temp_credentials,
    query_dynamodb,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    region = "us-west-2"
    identity_id = "us-west-2:8d780f3b-d79c-c6c8-1125-e7a905da6b9b"
    table_name = "bap"
    signed_headers = "host;x-amz-date;x-amz-security-token;x-amz-target"
    first_opinion_date = datetime(2000, 1, 1)
    days_interval = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.ca9.uscourts.gov/bap/"
        self.status = "Published"
        self.search_date = datetime.today()
        self.make_backscrape_iterable(kwargs)

    def _download(self):
        """Download data from DynamoDB for oral arguments.

        Retrieves temporary AWS credentials, constructs a DynamoDB scan payload
        to filter oral argument records by publish date, and queries the
        DynamoDB `bap` table for matching items.

        :return: The JSON response from DynamoDB containing oral argument records.
        """
        if self.test_mode_enabled():
            self._request_url_mock(self.url)
            self._post_process_response()
            return self._return_response_text_object()

        creds = get_temp_credentials(self.identity_id, self.region)
        payload_dict = {
            "TableName": self.table_name,
            "IndexName": "date_filed-index",
            "KeyConditionExpression": "#date_filed = :date_filed",
            "ExpressionAttributeNames": {"#date_filed": "date_filed"},
            "ExpressionAttributeValues": {
                ":date_filed": {"S": self.search_date.strftime("%m/%d/%Y")},
            },
            "ReturnConsumedCapacity": "TOTAL",
        }
        return query_dynamodb(
            creds,
            self.region,
            payload_dict,
            self.signed_headers,
            target="DynamoDB_20120810.Query",
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

    def _process_html(self):
        """Process the HTML response and extract case details.

        Iterates over the items in the HTML response, extracts relevant
        case information, and appends it to the cases list.

        :return: None; updates self.cases with extracted case details.
        """
        print(self.html)
        for item in self.html.get("Items", []):
            self.cases.append(
                {
                    "name": f"In re: {item.get('debtor').get('S', '')}",
                    "date": item.get("date_filed").get("S"),
                    "url": urljoin(
                        self.base_url, item.get("file_name").get("S")
                    ),
                    "docket": item.get("bap_num", {}).get("S"),
                }
            )
