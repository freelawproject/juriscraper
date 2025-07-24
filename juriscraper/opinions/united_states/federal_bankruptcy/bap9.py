"""
Scraper for the United States Bankruptcy Appellate Panel for the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP
"""

import json
from datetime import datetime
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.payload = json.dumps(
            {"TableName": self.table, "ReturnConsumedCapacity": "TOTAL"}
        )
        self.url = "https://cognito-identity.us-west-2.amazonaws.com/"

    def _download(self):
        """Download data from DynamoDB for oral arguments.

        :return: The JSON response from DynamoDB containing oral argument records.
        """
        if self.test_mode_enabled():
            return json.load(open(self.url))

        sess = self.request["session"]

        # fetch for credentials
        res = sess.post(self.url, headers=self.headers, json=self.params)
        creds = res.json().get("Credentials")

        # fetch signed headers
        sig = generate_aws_sigv4_headers(self.table, creds)

        # fetch bap table
        data = sess.post(self.query_url, headers=sig, data=self.payload)
        return data.json().get("Items", [])

    def _process_html(self):
        """Process the HTML response and extract case details.

        Iterates over the items in the HTML response, extracts relevant
        case information, and appends it to the cases list.

        :return: None; updates self.cases with extracted case details.
        """
        sorted_items = self.sort_items_by_date_filed_desc(self.html)
        for item in sorted_items:
            date_str = item.get("date_filed").get("S")
            try:
                datetime.strptime(date_str, "%m/%d/%Y")
            except ValueError:
                logger.debug("Skipping row with bad date data")
                continue
            slug = item.get("file_name").get("S")
            self.cases.append(
                {
                    "name": f"In re: {item.get('debtor').get('S', '')}",
                    "date": item.get("date_filed").get("S"),
                    "url": urljoin("https://cdn.ca9.uscourts.gov", slug),
                    "docket": item.get("bap_num", {}).get("S"),
                    "status": item.get("document_type").get("S"),
                }
            )

    def sort_items_by_date_filed_desc(self, items: list) -> list:
        """Sort by date filed

        :param items: all items in the data
        :return: sorted list
        """

        def parse_date(item):
            date_str = item.get("date_filed", {}).get("S", "")
            try:
                return datetime.strptime(date_str, "%m/%d/%Y")
            except ValueError:
                return datetime.min  # put malformed dates at the end

        return sorted(items, key=parse_date, reverse=True)
