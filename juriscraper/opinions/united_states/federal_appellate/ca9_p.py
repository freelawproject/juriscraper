"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
    - 2023-01-13: Update to use RSS Feed
    - 2025-08-27: Added extract_from_text and avoid duplicates.
    - 2026-05-29: Updated URL after site moved feeds under /decisions/.
    - 2026-08-28: Read the court's DynamoDB table instead of the RSS feed.
"""

import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import generate_aws_sigv4_headers
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


def get_attribute(record: dict, name: str, default: str = "") -> str:
    """Read a DynamoDB attribute value, dropping its type marker

    :param record: a DynamoDB row
    :param name: the column name
    :param default: value to use for a column the row does not carry
    :return: the column value, as a string
    """
    value = record.get(name)
    if not value:
        return default

    return str(next(iter(value.values()), default)).strip()


class Site(OpinionSiteLinear):
    identity_url = "https://cognito-identity.us-west-2.amazonaws.com/"
    query_url = "https://dynamodb.us-west-2.amazonaws.com/"

    identity_id = "us-west-2:8d780f3b-d79c-c6c8-1125-e7a905da6b9b"
    table = "opinions"
    base_url = "https://cdn.ca9.uscourts.gov/datastore/opinions/"
    precedential_status = "Published"
    # Lookback for the regular scrape, in `last_updated` terms.
    upload_window_days = 7
    # A Scan returns at most 1MB per request, a full table requires pagination
    max_pages = 100
    # A floor for the backscrape filter, the scan reads the whole table
    first_opinion_date = datetime(1995, 1, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = self.precedential_status
        self.should_have_results = True

        # AWS Cognito creds step
        self.headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
        }
        self.params = {"IdentityId": self.identity_id}
        self.url = self.identity_url

        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(
            days=self.upload_window_days
        )
        self.build_payload()
        self.make_backscrape_iterable(kwargs)

    def build_payload(self, backscrape: bool = False) -> None:
        """Build the DynamoDB scan for the current start_date/end_date

        The regular scrape filters on `last_updated`, the timestamp the court
        wrote the row. Backscrapes filter on `publish`, the filing date,
        because that is the only column that reaches back over the whole table.

        :param backscrape: filter by filing date instead of upload time
        :return: None
        """
        if backscrape:
            # `publish` is a number holding a "%Y%m%d%H%M%S" timestamp, e.g.
            # 20260527000000. Its time part is always zero.
            column = "publish"
            expression = "#COLUMN >= :from_date AND #COLUMN <= :to_date"
            values = {
                ":from_date": {"N": self.start_date.strftime("%Y%m%d000000")},
                ":to_date": {"N": self.end_date.strftime("%Y%m%d235959")},
            }
        else:
            # `last_updated` is a court-local "%Y-%m-%d %H:%M:%S" string.
            # Truncating to the day absorbs the offset against our own clock.
            column = "last_updated"
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

    async def _download(self, request_dict=None):
        """Build and download the table to parse

        DynamoDB Scan returns at most 1MB per request. If the response
        contains a ``LastEvaluatedKey``, we must paginate by feeding it
        back as ``ExclusiveStartKey`` in subsequent requests.

        :param request_dict: unused; kept for the base class signature
        :return: list of DynamoDB item dicts
        """
        self.downloader_executed = True

        if self.test_mode_enabled():
            with open(self.mock_url) as mock_file:
                return json.load(mock_file)

        sess = self.request["session"]

        # fetch for credentials
        res = await sess.post(self.url, headers=self.headers, json=self.params)
        creds = res.json().get("Credentials")

        all_items = []
        payload = json.loads(self.payload)

        for _page in range(self.max_pages):
            encoded_payload = json.dumps(payload)
            sig = generate_aws_sigv4_headers(
                encoded_payload, self.table, creds
            )

            logger.info(
                "Now downloading case page at: %s (params: %s)"
                % (self.query_url, encoded_payload)
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
            logger.error(
                "%s: reached the %d page scan limit (%d items). Some opinions were not scraped",
                self.court_id,
                self.max_pages,
                len(all_items),
            )

        return all_items

    def _process_html(self) -> None:
        """Parse the table rows into cases, newest upload first

        Rows with no `last_updated` fall back to filing date order.

        :return: None
        """
        records = sorted(
            self.html,
            key=lambda record: (
                get_attribute(record, "last_updated"),
                get_attribute(record, "publish"),
            ),
            reverse=True,
        )

        seen_urls = set()
        for record in records:
            docket = get_attribute(record, "case_num")

            if get_attribute(record, "deleted").lower() in {"1", "true"}:
                continue

            # An empty name would abort the whole scrape in `_check_sanity`,
            # so drop the row instead.
            case_name = get_attribute(record, "case_name")
            if not case_name:
                logger.warning(
                    "%s: skipping row with no `case_name` for docket %s",
                    self.court_id,
                    docket,
                )
                continue

            date_filed = self.get_date_filed(record)
            if not date_filed:
                logger.warning(
                    "%s: skipping row with bad `publish` %s for docket %s",
                    self.court_id,
                    get_attribute(record, "publish"),
                    docket,
                )
                continue

            file_name = get_attribute(record, "file_name")
            if not file_name:
                logger.warning(
                    "%s: skipping row with no `file_name` for docket %s",
                    self.court_id,
                    docket,
                )
                continue

            url = urljoin(self.base_url, file_name)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            self.cases.append(
                {
                    "name": titlecase(case_name),
                    "url": url,
                    "date": date_filed,
                    "status": self.status,
                    "docket": docket,
                    "nature_of_suit": get_attribute(record, "case_type"),
                    **self.get_judge_fields(record),
                }
            )

    def get_date_filed(self, record: dict) -> str:
        """Read the filing date out of the row's `publish` column

        :param record: a DynamoDB row
        :return: the filing date as "%Y-%m-%d", or "" if it cannot be parsed
        """
        publish = get_attribute(record, "publish")

        try:
            return datetime.strptime(publish[:8], "%Y%m%d").strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            return ""

    def get_judge_fields(self, record: dict) -> dict:
        """Map the table's judge column onto case keys

        The column names the judge, except on "Per Curiam" opinions.

        :param record: a DynamoDB row
        :return: the judge related part of the case dict
        """
        author = get_attribute(record, "judge")
        per_curiam = "curiam" in author.lower()
        if per_curiam:
            author = ""

        return {"author": author, "per_curiam": per_curiam}

    def _date_sort(self) -> None:
        """Preserve the upload time ordering applied by `_process_html`

        `AbstractSite._date_sort` would reorder the cases by filing date,
        which can lead to missing opinions.

        :return: None
        """
        return

    async def _download_backwards(
        self, dates: tuple[datetime, datetime]
    ) -> None:
        """Scan the table over a filing date range

        :param dates: (start, end) of the range to scrape
        :return: None
        """
        self.start_date, self.end_date = dates
        self.build_payload(backscrape=True)
        self.html = await self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Prepare a single (start, end) tuple for the backscrape

        A single tuple on purpose: each DynamoDB scan reads the whole table
        regardless of the FilterExpression, so splitting a backscrape into
        `days_interval` chunks would multiply the cost by the number of chunks
        and return nothing extra.

        :param kwargs: may hold `backscrape_start` and `backscrape_end`, as
            "%Y/%m/%d" strings
        :return: None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = (
            datetime.strptime(start, "%Y/%m/%d")
            if start
            else self.first_opinion_date
        )
        end = datetime.strptime(end, "%Y/%m/%d") if end else datetime.now()

        self.back_scrape_iterable = [(start, end)]

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (?:
               Appeals?\s+from\s+the\s+
              | On\s+Remand\s+from\s+the\s+
              | On\s+Petition\s+for\s+Review\s+of\s+an\s+Order\s+of\s+the\s+
            )
            (?P<lower_court>.+(?:\n.+)?)
            """,
            re.X,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }

        return {}
