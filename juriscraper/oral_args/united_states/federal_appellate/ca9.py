"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
History:
    - 2026-06-04: Audio files moved from www.ca9.uscourts.gov to
      cdn.ca9.uscourts.gov after the site redesign; same migration that
      moved the opinion feeds (#1987).
"""

import json
from datetime import datetime, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"
    # Lookback for the regular scrape, in `created_date` terms. The cron runs
    # hourly, so this only needs to cover a scraper outage. Widening it is
    # free: DynamoDB applies a FilterExpression after the scan, so the same
    # pages are read either way. #2111
    upload_window_days = 7
    first_opinion_date = datetime(2000, 10, 16)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.court_id = self.__module__
        self.table = "media"
        self.base_url = "https://cdn.ca9.uscourts.gov/datastore/media/"
        # Recent files are served as "application/octet-stream; charset=UTF-8";
        # older files (relevant for backscrapes) as "binary/octet-stream",
        # "audio/mpeg" or "audio/x-ms-wma" depending on the year
        self.expected_content_types = [
            "application/octet-stream; charset=UTF-8",
            "binary/octet-stream",
            "audio/mpeg",
            "audio/x-ms-wma",
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
        self.start_date = self.end_date - timedelta(
            days=self.upload_window_days
        )
        self.build_payload()

        self.url = "https://cognito-identity.us-west-2.amazonaws.com/"
        self.make_backscrape_iterable(kwargs)

    def build_payload(self, backscrape: bool = False) -> None:
        """Build the DynamoDB scan for the current start_date/end_date

        The regular scrape filters on `created_date`, the timestamp the court
        wrote the row, because ordering the crawl by upload time is what keeps
        us from missing arguments; see `_process_html`. Backscrapes filter on
        `publish`, the hearing date, because the court only started recording
        `created_date` in mid 2021 and historical rows would otherwise be
        invisible. #2111

        :param backscrape: filter by hearing date instead of upload time
        :return: None
        """
        if backscrape:
            # `publish` is a number, e.g. 20260605
            column = "publish"
            expression = "#COLUMN >= :from_date AND #COLUMN <= :to_date"
            values = {
                ":from_date": {"N": self.start_date.strftime("%Y%m%d")},
                ":to_date": {"N": self.end_date.strftime("%Y%m%d")},
            }
        else:
            # `created_date` is a court-local "%Y-%m-%d %H:%M:%S" string.
            # Truncating to the day absorbs the offset against our own clock,
            # and there is deliberately no upper bound, so that clock skew can
            # never hide the court's newest uploads
            column = "created_date"
            expression = "#COLUMN >= :from_date"
            values = {
                ":from_date": {
                    "S": self.start_date.strftime("%Y-%m-%d 00:00:00")
                }
            }

        self.payload = json.dumps(
            {
                "TableName": self.table,
                "ReturnConsumedCapacity": "TOTAL",
                "FilterExpression": expression,
                "ExpressionAttributeNames": {"#COLUMN": column},
                "ExpressionAttributeValues": values,
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

        for _page in range(max_pages):
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
            docket = record.get("case_num", {}).get("S")
            try:
                # validate ISO date
                datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                logger.warning(
                    "ca9: skipping row with bad hearing_date %s for docket %s",
                    date_str,
                    docket,
                )
                continue

            try:
                audio = record["audio_file_name"]["S"]
            except KeyError:
                logger.warning(
                    "ca9: skipping row with no audio_file_name for docket %s",
                    docket,
                )
                continue

            self.cases.append(
                {
                    "date": date_str,
                    "docket": record["case_num"]["S"],
                    "judge": record["case_panel"]["S"],
                    "name": record["case_name"]["S"],
                    "url": urljoin(self.base_url, audio),
                    # Only used for ordering below; it has no getter, so it
                    # never reaches the scraped output
                    "created_date": record.get("created_date", {}).get(
                        "S", ""
                    ),
                }
            )

        # CourtListener walks these cases top down and stops at the first
        # duplicate, so the newest uploads have to come first: that guarantees
        # every new row is seen before the first row we already have. Ordering
        # by hearing date instead left arguments the court uploaded later in the
        # day sitting behind rows already in CL, where nothing ever reached
        # them again. Rows older than mid 2021 have no `created_date` and fall
        # back to hearing date order. #2111
        self.cases.sort(
            key=lambda case: (
                case["created_date"],
                case["date"],
                case["docket"],
            ),
            reverse=True,
        )

    def _date_sort(self) -> None:
        """Preserve the upload time ordering applied by `_process_html`

        `AbstractSite._date_sort` would reorder the cases by hearing date, which
        is the ordering that made us miss arguments. #2111

        :return: None
        """

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
        self.build_payload(backscrape=True)
        self.html = await self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """
        Prepare a single (start, end) tuple, defaulting to __init__’s range
        or overridden via backscrape_start / backscrape_end in kwargs.

        A single tuple on purpose: each DynamoDB scan reads the whole table
        regardless of the FilterExpression, so splitting a backscrape into
        `days_interval` chunks would multiply the cost by the number of chunks
        and return nothing extra.
        """
        start = kwargs.get("backscrape_start", self.start_date)
        end = kwargs.get("backscrape_end", self.end_date)
        self.back_scrape_iterable = [(start, end)]
