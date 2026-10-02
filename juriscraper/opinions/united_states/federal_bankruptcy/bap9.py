"""
Scraper for the United States Bankruptcy Appellate Panel for the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP
"""

import json
import re
from datetime import date, datetime, time, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.Backscraper import DateBackscraper
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear, DateBackscraper):
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"
    days_interval = 31
    first_opinion_date = datetime(2005, 1, 6)
    lower_court_regex = re.compile(
        r"Appeals? from the (?P<lower_court>.+\n.+)"
    )

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
        now = datetime.now()
        self.build_payload(now - timedelta(days=self.days_interval), now)
        # The payload already filters by month; don't filter out anything
        # else in `_process_html`. This used to be a side effect of the old
        # `make_backscrape_iterable` override (see #2139)
        self.start_date = self.first_opinion_date
        self.end_date = now
        self.url = "https://cognito-identity.us-west-2.amazonaws.com/"
        self.make_backscrape_iterable(kwargs)

    def build_payload(self, start: datetime, end: datetime) -> None:
        """Build the query for the regular scrape; sets `self.payload`

        :param start: start of the requested window
        :param end: end of the requested window
        :return: None
        """
        expression_values = {
            ":start_date": {"S": start.strftime("%m")},
            ":year": {"S": start.strftime("%Y")},
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

    async def _download(self):
        """Download data from DynamoDB for oral arguments.

        :return: The JSON response from DynamoDB containing oral argument records.
        """
        if self.test_mode_enabled():
            return json.load(open(self.mock_url))

        sess = self.request["session"]

        # fetch for credentials
        res = await sess.post(self.url, headers=self.headers, json=self.params)
        creds = res.json().get("Credentials")

        # fetch signed headers
        sig = generate_aws_sigv4_headers(self.payload, self.table, creds)

        logger.info(
            "Now downloading case page at: %s (params: %s)"
            % (self.url, self.payload)
        )

        # fetch bap table
        self.request["response"] = await sess.post(
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
                logger.debug("Skipping row with bad date data %s", item)
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

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        if match := self.lower_court_regex.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }

        return {}

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Download cases for a specific date range.

        :param dates: the (start, end) range, both ends inclusive
        :return: None; updates self.cases with cases from the specified date range.
        """
        # `_process_html` compares these with datetimes
        start, end = dates
        self.start_date = datetime.combine(start, time.min)
        self.end_date = datetime.combine(end, time.max)

        self.payload = json.dumps(
            {"TableName": self.table, "ReturnConsumedCapacity": "TOTAL"}
        )
        self.html = await self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """A single range: a backscrape request returns the whole table,
        which is then filtered by date in `_process_html`

        :param kwargs: the kwargs passed to `Site.__init__`
        :return: None; sets self.back_scrape_iterable in place
        """
        self.back_scrape_iterable = [self.get_backscrape_date_range(kwargs)]
