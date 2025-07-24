"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

import json
from datetime import datetime
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.table = "media"
        self.base_url = "https://www.ca9.uscourts.gov/"
        self.expected_content_types = [
            "application/octet-stream; charset=UTF-8"
        ]
        self.status = "Published"
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
        """Build and download the table to parse

        :return: json data
        """
        if self.test_mode_enabled():
            return json.load(open(self.url))

        sess = self.request["session"]

        # fetch for credentials
        res = sess.post(self.url, headers=self.headers, json=self.params)
        creds = res.json().get("Credentials")

        # fetch signed headers
        sig = generate_aws_sigv4_headers(self.table, creds)

        # Fetch media table
        data = sess.post(self.query_url, headers=sig, data=self.payload)

        return data.json().get("Items", [])

    def sort_by_hearing_date_desc(self, items):
        """Filter the data by date"""

        def parse_hearing_date(item):
            date_str = item.get("hearing_date", {}).get("S", "")
            return datetime.strptime(date_str, "%Y-%m-%d")

        return sorted(items, key=parse_hearing_date, reverse=True)

    def _process_html(self):
        """Process the json response"""
        sorted_items = self.sort_by_hearing_date_desc(self.html)

        print(sorted_items)
        for record in sorted_items:
            date_str = record.get("hearing_date").get("S")
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                logger.debug("Skipping row with bad data")
                continue

            date = record["hearing_date"]["S"]
            docket = record["case_num"]["S"]
            judge = record["case_panel"]["S"]
            name = record["case_name"]["S"]
            try:
                url = urljoin(self.base_url, record["audio_file_name"]["S"])
            except KeyError:
                logger.debug("Skipping row with no audio file")
                continue

            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "judge": judge,
                    "name": name,
                    "url": url,
                }
            )
