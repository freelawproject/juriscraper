"""
Scraper for the United States Bankruptcy Appellate Panel for the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP
"""

import json
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"
    days_interval = 31
    first_opinion_date = datetime(2005, 1, 6)

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
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=self.days_interval)
        self.build_payload()
        self.url = "https://cognito-identity.us-west-2.amazonaws.com/"
        self.make_backscrape_iterable(kwargs)

    def build_payload(self):
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
        if date.month != 12:
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
        sig = generate_aws_sigv4_headers(self.payload, self.table, creds)

        logger.info(
            "Now downloading case page at: %s (params: %s)"
            % (self.url, self.payload)
        )

        # fetch bap table
        self.request["response"] = sess.post(
            self.query_url, headers=sig, data=self.payload
        )

        if self.save_response:
            self.save_response(self)

        self._post_process_response()
        return self._return_response_text_object()["Items"]

    def _process_html(self):
        """Process the HTML response and extract case details.

        Iterates over the items in the HTML response, extracts relevant
        case information, and appends it to the cases list.

        :return: None; updates self.cases with extracted case details.
        """
        for item in self.html:
            date_str = item.get("date_filed").get("S")
            try:
                d = datetime.strptime(date_str, "%m/%d/%Y")
                if d < self.start_date:
                    continue
                if d > self.end_date:
                    continue
            except ValueError:
                logger.debug("Skipping row with bad date data")
                continue

            slug = item.get("file_name").get("S")
            status = item.get("document_type").get("S")
            if status == "Unpublished Opinion":
                status = "Unpublished"
            else:
                status = "Published"
            self.cases.append(
                {
                    "name": f"In re: {item.get('debtor').get('S', '')}",
                    "date": item.get("date_filed").get("S"),
                    "url": urljoin("https://cdn.ca9.uscourts.gov", slug),
                    "docket": item.get("bap_num", {}).get("S"),
                    "status": status,
                }
            )

    def _download_backwards(self, date: date) -> None:
        """Download cases for a specific date range.

        :param dates: A tuple containing start and end dates.
        :return: None; updates self.cases with cases from the specified date range.
        """
        start_str, end_str, _ = date

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

        self.payload = json.dumps(
            {"TableName": self.table, "ReturnConsumedCapacity": "TOTAL"}
        )
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        self.start_date = kwargs.get(
            "backscrape_start", self.first_opinion_date
        )
        self.end_date = kwargs.get("backscrape_end", datetime.now())
        self.back_scrape_iterable = [(self.start_date, self.end_date, None)]
