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
from juriscraper.lib.date_utils import unique_year_month
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
        self.search_date = datetime.now()
        self.payload = json.dumps(
            {
                "TableName": self.table,
                "FilterExpression": "#date_filed = :date",
                "ExpressionAttributeNames": {"#date_filed": "date_filed"},
                "ExpressionAttributeValues": {
                    ":date": {"S": self.search_date.strftime("%m/%d/%Y")},
                },
                "ReturnConsumedCapacity": "TOTAL",
            }
        )

        self.url = "https://cognito-identity.us-west-2.amazonaws.com/"
        self.make_backscrape_iterable(kwargs)

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

    def _download_backwards(self, date: date) -> None:
        """Download cases for a specific date range.

        :param dates: A tuple containing start and end dates.
        :return: None; updates self.cases with cases from the specified date range.
        """
        end = (date.replace(day=1) + timedelta(days=32)).replace(day=1)

        expression_values = {
            ":start_date": {"S": date.strftime("%m")},
            ":year": {"S": date.strftime("%Y")},
        }
        filter_expression = (
            "#date_filed > :start_date and contains(#date_filed, :year)"
        )
        if date.month != 12:
            expression_values[":end_date"] = {"S": end.strftime("%m")}
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

        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
