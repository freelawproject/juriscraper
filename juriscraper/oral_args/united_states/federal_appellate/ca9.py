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

from pydantic import TypeAdapter
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.auth_utils import (
    COGNITO_RESPONSE,
    generate_aws_sigv4_headers,
)
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import (
    BackscrapeOptions,
    DynamoDBItem,
    DynamoDBScan,
    RawOralArgument,
)
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear

_items_adapter = TypeAdapter(list[DynamoDBItem])
_scan_adapter = TypeAdapter(DynamoDBScan)


class Site(OralArgumentSiteLinear[tuple[str, str]]):
    payload: str

    query_url = "https://dynamodb.us-west-2.amazonaws.com/"
    # Lookback for the regular scrape, in `created_date` terms. The cron runs
    # hourly, so this only needs to cover a scraper outage. Widening it is
    # free: DynamoDB applies a FilterExpression after the scan, so the same
    # pages are read either way. #2111
    upload_window_days = 7
    first_opinion_date = datetime(2000, 10, 16)

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[str, str]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)

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
            "audio/mp3",
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

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> list[DynamoDBItem]:
        """Build and download the table to parse

        DynamoDB Scan returns at most 1MB per request. If the response
        contains a ``LastEvaluatedKey``, we must paginate by feeding it
        back as ``ExclusiveStartKey`` in subsequent requests.

        :return: list of DynamoDB item dicts
        """
        self.downloader_executed = True

        if self.test_mode_enabled():
            with open(self.mock_url) as fixture:
                return _items_adapter.validate_json(
                    fixture.read(), strict=True
                )

        sess = self.request["session"]

        # fetch for credentials
        if self.url is None:
            raise ValueError("The Cognito URL is not configured")
        res = await sess.post(self.url, headers=self.headers, json=self.params)
        res.raise_for_status()
        creds = COGNITO_RESPONSE.validate_python(res.json(), strict=True)[
            "Credentials"
        ]

        all_items: list[DynamoDBItem] = []
        payload: dict[str, object] = json.loads(self.payload)
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
                self.query_url, headers=sig, content=encoded_payload
            )

            if self.save_response is not None:
                self.save_response(self)

            self._post_process_response()
            data = _scan_adapter.validate_python(
                self._return_response_text_object(), strict=True
            )
            all_items.extend(data.get("Items", []))

            last_key = data.get("LastEvaluatedKey")
            if not bool(last_key):
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

    @override
    def _process_html(self) -> None:
        """Process the json response"""

        records = _items_adapter.validate_python(self.html, strict=True)
        ordered_cases: list[tuple[tuple[str, str, str], RawOralArgument]] = []
        for record in records:
            date_str = record.get("hearing_date", {}).get("S")
            docket = record.get("case_num", {}).get("S")
            try:
                # validate ISO date
                if date_str is None:
                    raise ValueError("Missing hearing date")
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                logger.warning(
                    "ca9: skipping row with bad hearing_date %s for docket %s",
                    date_str,
                    docket,
                )
                continue

            audio = record.get("audio_file_name", {}).get("S")
            if audio is None:
                logger.warning(
                    "ca9: skipping row with no audio_file_name for docket %s",
                    docket,
                )
                continue

            panel = record["case_panel"].get("S")
            name = record["case_name"].get("S")
            if panel is None or name is None:
                raise KeyError("S")
            case: RawOralArgument = {
                "date": date_str,
                "docket": docket,
                "judge": panel,
                "name": name,
                "url": urljoin(self.base_url, audio),
            }
            created_date = record.get("created_date", {}).get("S", "")
            ordered_cases.append(
                (
                    (
                        created_date,
                        date_str,
                        (docket if docket is not None else ""),
                    ),
                    case,
                )
            )

        # CourtListener walks these cases top down and stops at the first
        # duplicate, so the newest uploads have to come first: that guarantees
        # every new row is seen before the first row we already have. Ordering
        # by hearing date instead left arguments the court uploaded later in the
        # day sitting behind rows already in CL, where nothing ever reached
        # them again. Rows older than mid 2021 have no `created_date` and fall
        # back to hearing date order. #2111
        ordered_cases.sort(key=lambda item: item[0], reverse=True)
        self.cases.extend(case for _, case in ordered_cases)

    @override
    def _date_sort(self) -> None:
        """Preserve the upload time ordering applied by `_process_html`

        `AbstractSite._date_sort` would reorder the cases by hearing date, which
        is the ordering that made us miss arguments. #2111

        :return: None
        """

    @override
    async def _download_backwards(self, dates: tuple[str, str]) -> None:
        """Download backwards

        :param dates: (start_str, end_str) in "%Y/%m/%d" or empty.
        :return: None
        """
        start_str, end_str = dates

        # Parse start date or fall back to first_opinion_date
        if bool(start_str):
            self.start_date = datetime.strptime(start_str, "%Y/%m/%d")
        else:
            self.start_date = self.first_opinion_date

        # Parse end date or fall back to now
        if bool(end_str):
            self.end_date = datetime.strptime(end_str, "%Y/%m/%d")
        else:
            self.end_date = datetime.now()

        # Rebuild payload for this slice
        self.build_payload(backscrape=True)
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """
        Prepare a single (start, end) tuple, defaulting to __init__’s range
        or overridden via backscrape_start / backscrape_end in kwargs.

        A single tuple on purpose: each DynamoDB scan reads the whole table
        regardless of the FilterExpression, so splitting a backscrape into
        `days_interval` chunks would multiply the cost by the number of chunks
        and return nothing extra.
        """
        start = (
            backscrape_start_value
            if bool(backscrape_start_value := kwargs.get("backscrape_start"))
            else self.start_date.strftime("%Y/%m/%d")
        )
        end = (
            backscrape_end_value
            if bool(backscrape_end_value := kwargs.get("backscrape_end"))
            else self.end_date.strftime("%Y/%m/%d")
        )
        self.back_scrape_iterable = [(start, end)]
