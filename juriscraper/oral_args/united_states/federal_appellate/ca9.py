"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

import json
from datetime import date, datetime
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"
    days_interval = 365
    first_opinion_date = datetime(2000, 10, 16)

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

        self.search_date = datetime.now()

        self.payload = json.dumps(
            {
                "TableName": self.table,
                "ReturnConsumedCapacity": "TOTAL",
                "FilterExpression": "#PUBLISH = :publish",
                "ExpressionAttributeNames": {"#PUBLISH": "publish"},
                "ExpressionAttributeValues": {
                    ":publish": {"N": self.search_date.strftime("%Y%m%d")},
                },
            }
        )
        self.url = "https://cognito-identity.us-west-2.amazonaws.com/"
        self.make_backscrape_iterable(kwargs)

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
        sig = generate_aws_sigv4_headers(self.payload, self.table, creds)

        logger.info(
            "Now downloading case page at: %s (params: %s)"
            % (self.url, self.payload)
        )

        # Fetch media table
        self.request["response"] = sess.post(
            self.query_url, headers=sig, data=self.payload
        )

        if self.save_response:
            self.save_response(self)

        self._post_process_response()
        return self._return_response_text_object()["Items"]

    def _process_html(self):
        """Process the json response"""

        for record in self.html:
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

    def _download_backwards(self, dates: tuple[date]) -> None:
        """Download cases for a specific date range.

        :param dates: A tuple containing start and end dates.
        :return: None; updates self.cases with cases from the specified date range.
        """

        start = dates[0]
        end = dates[1]

        self.payload = json.dumps(
            {
                "FilterExpression": "#PUBLISH >= :from_date AND #PUBLISH <= :to_date",
                "ReturnConsumedCapacity": "TOTAL",
                "ExpressionAttributeNames": {"#PUBLISH": "publish"},
                "ExpressionAttributeValues": {
                    ":from_date": {"N": start.strftime("%Y%m%d")},
                    ":to_date": {"N": end.strftime("%Y%m%d")},
                },
                "TableName": "media",
            }
        )

        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Set up the backscrape iterable for the scraper.

        This method is called to prepare the scraper for backscraping
        by setting the date range and other parameters.

        :param kwargs: Keyword arguments passed to the scraper.
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = [
            (
                self.back_scrape_iterable[0][0],
                self.back_scrape_iterable[-1][-1],
            )
        ]
